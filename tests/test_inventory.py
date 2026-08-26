"""Tests for durable inventory manifests."""

import json
from pathlib import Path
from typing import Any, Dict, List

import pytest
from click.testing import CliRunner

from dtcli import inventory as inventory_command
from dtcli.cli import cli as datatrail


def _row(dataset: str, path: List[str]) -> Dict[str, Any]:
    """Build a recursive discovery row."""
    return {
        "scope": "test.scope",
        "dataset": dataset,
        "parent": path[-2] if len(path) > 1 else None,
        "path": path,
    }


def test_inventory_builds_atomic_manifest(tmp_path: Path, monkeypatch) -> None:
    """Test deterministic replicas and per-dataset checkpoints."""
    output = tmp_path / "inventory.json"
    calls = []
    writes = []

    def discover(**kwargs):
        assert kwargs["match"] == "baseband,classified"
        return {
            "results": [
                _row("ready", ["root", "ready"]),
                _row("empty", ["root", "empty"]),
            ],
            "failed": [],
        }

    def file_info(scope, dataset, verbose=0, quiet=False):
        calls.append(dataset)
        if dataset == "empty":
            return {"file_replica_locations": {}}
        return {
            "file_replica_locations": {
                "minoc": ["cadc:file-b", "cadc:file-a", "cadc:file-a"],
                "archive": ["archive:file"],
            }
        }

    original_write = inventory_command._write_manifest

    def record_write(path, manifest):
        original_write(path, manifest)
        writes.append(json.loads(json.dumps(manifest)))

    monkeypatch.setattr(inventory_command.functions, "discover_datasets", discover)
    monkeypatch.setattr(inventory_command.functions, "get_dataset_file_info", file_info)
    monkeypatch.setattr(inventory_command, "_write_manifest", record_write)

    manifest = inventory_command.build_inventory(
        scope=None,
        match="classified, BASEBAND",
        parent=None,
        output=output,
    )

    assert manifest["schema"] == "datatrail.inventory/v1"
    assert manifest["selection"] == {
        "scope": None,
        "match": ["baseband", "classified"],
        "parent": None,
    }
    assert manifest["complete"] is True
    assert [entry["dataset"] for entry in manifest["datasets"]] == [
        "empty",
        "ready",
    ]
    assert manifest["datasets"][0]["status"] == "empty"
    assert manifest["datasets"][1]["replicas"] == [
        {"storage_element": "archive", "uri": "archive:file"},
        {"storage_element": "minoc", "uri": "cadc:file-a"},
        {"storage_element": "minoc", "uri": "cadc:file-b"},
    ]
    assert calls == ["empty", "ready"]
    assert len(writes) == 4
    assert [entry["status"] for entry in writes[0]["datasets"]] == [
        "pending",
        "pending",
    ]
    assert [entry["status"] for entry in writes[1]["datasets"]] == [
        "empty",
        "pending",
    ]
    assert json.loads(output.read_text()) == manifest
    assert list(tmp_path.glob(".inventory.json.*.tmp")) == []


def test_inventory_resume_retries_only_failures(tmp_path: Path, monkeypatch) -> None:
    """Test a rerun reuses finished entries and retries failures."""
    output = tmp_path / "inventory.json"
    attempts = {"ready": 0, "empty": 0, "flaky": 0}

    def discover(**kwargs):
        return {
            "results": [
                _row("ready", ["root", "ready"]),
                _row("empty", ["root", "empty"]),
                _row("flaky", ["root", "flaky"]),
            ],
            "failed": [],
        }

    def file_info(scope, dataset, verbose=0, quiet=False):
        attempts[dataset] += 1
        if dataset == "empty":
            return {"file_replica_locations": {}}
        if dataset == "flaky" and attempts[dataset] == 1:
            return {"error": "service unavailable"}
        return {"file_replica_locations": {"minoc": [f"cadc:{dataset}"]}}

    monkeypatch.setattr(inventory_command.functions, "discover_datasets", discover)
    monkeypatch.setattr(inventory_command.functions, "get_dataset_file_info", file_info)

    first = inventory_command.build_inventory(
        scope="test.scope", match=None, parent=None, output=output
    )
    assert first["complete"] is False
    assert (
        next(entry for entry in first["datasets"] if entry["dataset"] == "flaky")[
            "status"
        ]
        == "failed"
    )

    second = inventory_command.build_inventory(
        scope="test.scope", match=None, parent=None, output=output
    )
    assert second["complete"] is True
    assert attempts == {"ready": 1, "empty": 1, "flaky": 2}
    flaky = next(entry for entry in second["datasets"] if entry["dataset"] == "flaky")
    assert flaky["status"] == "ready"
    assert "error" not in flaky


def test_inventory_parent_starts_at_subtree(tmp_path: Path, monkeypatch) -> None:
    """Test a named parent starts recursive traversal directly."""
    output = tmp_path / "inventory.json"

    def descendants(scope, roots, verbose=0, quiet=False):
        assert scope == "test.scope"
        assert roots == ["root"]
        return [_row("leaf", ["root", "leaf"])], []

    monkeypatch.setattr(
        inventory_command.functions, "_discover_descendants", descendants
    )
    monkeypatch.setattr(
        inventory_command.functions,
        "get_dataset_file_info",
        lambda *args, **kwargs: {"file_replica_locations": {}},
    )

    manifest = inventory_command.build_inventory(
        scope="test.scope", match=None, parent="root", output=output
    )
    assert manifest["complete"] is True
    assert manifest["selection"]["parent"] == "root"
    assert manifest["datasets"][0]["path"] == ["root", "leaf"]
    assert manifest["datasets"][0]["status"] == "empty"


def test_inventory_default_exit_fails_on_discovery_gap(
    tmp_path: Path, monkeypatch
) -> None:
    """Test incomplete discovery needs an explicit successful-exit option."""
    output = tmp_path / "inventory.json"

    monkeypatch.setattr(
        inventory_command.functions,
        "discover_datasets",
        lambda **kwargs: {
            "results": [_row("leaf", ["root", "leaf"])],
            "failed": ["children of test.scope root / offline"],
        },
    )
    monkeypatch.setattr(
        inventory_command.functions,
        "get_dataset_file_info",
        lambda *args, **kwargs: {"file_replica_locations": {"minoc": ["cadc:leaf"]}},
    )
    runner = CliRunner()
    result = runner.invoke(
        datatrail, ["inventory", "test.scope", "--output", str(output)]
    )
    assert result.exit_code == 1
    assert "Inventory incomplete" in result.output
    assert json.loads(output.read_text())["complete"] is False

    allowed = runner.invoke(
        datatrail,
        [
            "inventory",
            "test.scope",
            "--output",
            str(output),
            "--allow-incomplete",
        ],
    )
    assert allowed.exit_code == 0
    assert "Inventory incomplete" in allowed.output


def test_inventory_default_exit_fails_on_file_query(tmp_path: Path, monkeypatch) -> None:
    """Test a failed file query makes the command fail by default."""
    output = tmp_path / "inventory.json"
    monkeypatch.setattr(
        inventory_command.functions,
        "discover_datasets",
        lambda **kwargs: {
            "results": [_row("leaf", ["root", "leaf"])],
            "failed": [],
        },
    )
    monkeypatch.setattr(
        inventory_command.functions,
        "get_dataset_file_info",
        lambda *args, **kwargs: {"error": "service unavailable"},
    )
    result = CliRunner().invoke(
        datatrail, ["inventory", "test.scope", "--output", str(output)]
    )
    assert result.exit_code == 1
    manifest = json.loads(output.read_text())
    assert manifest["complete"] is False
    assert manifest["datasets"][0]["status"] == "failed"
    assert manifest["datasets"][0]["error"] == "service unavailable"


@pytest.mark.parametrize(
    "arguments,message",
    [
        ([], "Give SCOPE"),
        (["--parent", "root"], "--parent requires SCOPE"),
        (
            ["test.scope", "--parent", "root", "--match", "gain"],
            "either --parent or --match",
        ),
        (["test.scope", "--match", "  ,  "], "--match must contain"),
    ],
)
def test_inventory_rejects_unbounded_or_ambiguous_selection(
    tmp_path: Path, arguments: List[str], message: str
) -> None:
    """Test inventory selection always has one clear boundary."""
    output = tmp_path / "inventory.json"
    runner = CliRunner()
    result = runner.invoke(datatrail, ["inventory", *arguments, "--output", str(output)])
    assert result.exit_code == 1
    assert message in result.output
    assert not output.exists()


def test_inventory_refuses_different_selection(tmp_path: Path, monkeypatch) -> None:
    """Test a manifest cannot be resumed with a different selection."""
    output = tmp_path / "inventory.json"
    monkeypatch.setattr(
        inventory_command.functions,
        "discover_datasets",
        lambda **kwargs: {"results": [], "failed": []},
    )
    inventory_command.build_inventory(
        scope="first.scope", match=None, parent=None, output=output
    )
    with pytest.raises(ValueError, match="selection does not match"):
        inventory_command.build_inventory(
            scope="second.scope", match=None, parent=None, output=output
        )


def test_inventory_help() -> None:
    """Test the inventory command is registered with its main options."""
    result = CliRunner().invoke(datatrail, ["inventory", "--help"])
    assert result.exit_code == 0
    assert "--match" in result.output
    assert "--parent" in result.output
    assert "--output" in result.output
    assert "--allow-incomplete" in result.output
