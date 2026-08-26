"""Tests for manifest-driven downloads."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from dtcli import pull_manifest as pull_manifest_module
from dtcli.cli import cli as datatrail


def write_inventory(path: Path, files, complete: bool = True) -> None:
    """Write a small inventory manifest."""
    replicas = [
        {"storage_element": "minoc", "uri": f"cadc:CHIMEFRB/{name}"} for name in files
    ]
    path.write_text(
        json.dumps(
            {
                "schema": "datatrail.inventory/v1",
                "complete": complete,
                "datasets": [
                    {
                        "scope": "test.scope",
                        "dataset": "test-dataset",
                        "status": "ready",
                        "replicas": replicas,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def test_transfer_resumes_only_failed_files(tmp_path: Path, monkeypatch) -> None:
    """A rerun keeps completed files and retries failures."""
    manifest = tmp_path / "inventory.json"
    state = tmp_path / "pull.json"
    destination = tmp_path / "data"
    write_inventory(manifest, ["first.dat", "second.dat"])
    calls = []

    def first_attempt(source, destination, processors, verbose):
        calls.append((source, processors))
        Path(destination[0]).write_bytes(b"first")
        return [
            {
                "source": "second.dat",
                "destination": destination[1],
                "error": "service unavailable",
            }
        ]

    monkeypatch.setattr(pull_manifest_module.cadcclient, "pget", first_attempt)
    transfer = pull_manifest_module.prepare_transfer(manifest, destination, state)
    pull_manifest_module.run_transfer(transfer, state, cores=2)

    assert transfer["complete"] is False
    assert [entry["status"] for entry in transfer["files"]] == [
        "complete",
        "failed",
    ]
    assert json.loads(state.read_text()) == transfer

    def second_attempt(source, destination, processors, verbose):
        calls.append((source, processors))
        assert source == ["second.dat"]
        Path(destination[0]).write_bytes(b"second")
        return []

    monkeypatch.setattr(pull_manifest_module.cadcclient, "pget", second_attempt)
    resumed = pull_manifest_module.prepare_transfer(manifest, destination, state)
    pull_manifest_module.run_transfer(resumed, state, cores=2)

    assert resumed["complete"] is True
    assert [entry["status"] for entry in resumed["files"]] == [
        "complete",
        "complete",
    ]
    assert calls == [(["first.dat", "second.dat"], 2), (["second.dat"], 2)]


def test_missing_completed_file_is_downloaded_again(tmp_path: Path, monkeypatch) -> None:
    """A missing destination invalidates its completed state."""
    manifest = tmp_path / "inventory.json"
    state = tmp_path / "pull.json"
    destination = tmp_path / "data"
    write_inventory(manifest, ["file.dat"])

    def download(source, destination, processors, verbose):
        Path(destination[0]).write_bytes(b"contents")
        return []

    monkeypatch.setattr(pull_manifest_module.cadcclient, "pget", download)
    transfer = pull_manifest_module.prepare_transfer(manifest, destination, state)
    pull_manifest_module.run_transfer(transfer, state, cores=1)
    (destination / "file.dat").unlink()

    resumed = pull_manifest_module.prepare_transfer(manifest, destination, state)

    assert resumed["files"][0]["status"] == "pending"
    assert resumed["complete"] is False


def test_interruption_keeps_previous_checkpoint(tmp_path: Path, monkeypatch) -> None:
    """An interruption keeps earlier batches completed."""
    manifest = tmp_path / "inventory.json"
    state = tmp_path / "pull.json"
    destination = tmp_path / "data"
    write_inventory(manifest, ["first.dat", "second.dat"])
    attempts = 0

    def download(source, destination, processors, verbose):
        nonlocal attempts
        attempts += 1
        if attempts == 2:
            raise KeyboardInterrupt
        Path(destination[0]).write_bytes(b"first")
        return []

    monkeypatch.setattr(pull_manifest_module.cadcclient, "pget", download)
    transfer = pull_manifest_module.prepare_transfer(manifest, destination, state)
    with pytest.raises(KeyboardInterrupt):
        pull_manifest_module.run_transfer(transfer, state, cores=1)

    saved = json.loads(state.read_text())
    assert [entry["status"] for entry in saved["files"]] == [
        "complete",
        "pending",
    ]
    assert saved["complete"] is False


@pytest.mark.parametrize(
    "uri",
    [
        "cadc:OTHER/file.dat",
        "cadc:CHIMEFRB/../file.dat",
        "cadc:CHIMEFRB//file.dat",
        "cadc:CHIMEFRB/folder\\file.dat",
    ],
)
def test_unsafe_or_unsupported_uri_is_rejected(tmp_path: Path, uri: str) -> None:
    """Only safe paths in the expected Minoc namespace are accepted."""
    manifest = tmp_path / "inventory.json"
    manifest.write_text(
        json.dumps(
            {
                "schema": "datatrail.inventory/v1",
                "complete": True,
                "datasets": [
                    {
                        "scope": "test.scope",
                        "dataset": "test-dataset",
                        "status": "ready",
                        "replicas": [{"storage_element": "minoc", "uri": uri}],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        pull_manifest_module.prepare_transfer(
            manifest, tmp_path / "data", tmp_path / "pull.json"
        )


def test_destination_symlink_escape_is_rejected(tmp_path: Path) -> None:
    """A symlink cannot redirect a transfer outside its root."""
    manifest = tmp_path / "inventory.json"
    destination = tmp_path / "data"
    outside = tmp_path / "outside"
    destination.mkdir()
    outside.mkdir()
    (destination / "linked").symlink_to(outside, target_is_directory=True)
    write_inventory(manifest, ["linked/file.dat"])

    with pytest.raises(ValueError, match="escapes the destination"):
        pull_manifest_module.prepare_transfer(
            manifest, destination, tmp_path / "pull.json"
        )


def test_command_fails_when_inventory_is_incomplete(tmp_path: Path, monkeypatch) -> None:
    """Available files can finish without hiding an inventory gap."""
    manifest = tmp_path / "inventory.json"
    destination = tmp_path / "data"
    write_inventory(manifest, ["file.dat"], complete=False)

    def download(source, destination, processors, verbose):
        Path(destination[0]).parent.mkdir(parents=True, exist_ok=True)
        Path(destination[0]).write_bytes(b"contents")
        return []

    monkeypatch.setattr(pull_manifest_module.cadcclient, "pget", download)
    runner = CliRunner()
    result = runner.invoke(
        pull_manifest_module.pull_manifest,
        [str(manifest), "--directory", str(destination), "--force"],
    )

    assert result.exit_code == 1
    assert "The inventory is incomplete" in result.output
    assert (destination / "file.dat").read_bytes() == b"contents"


def test_dataset_without_minoc_replica_stays_incomplete(tmp_path: Path) -> None:
    """A ready dataset without Minoc files is reported in transfer state."""
    manifest = tmp_path / "inventory.json"
    manifest.write_text(
        json.dumps(
            {
                "schema": "datatrail.inventory/v1",
                "complete": True,
                "datasets": [
                    {
                        "scope": "test.scope",
                        "dataset": "archive-only",
                        "status": "ready",
                        "replicas": [
                            {"storage_element": "archive", "uri": "archive:file.dat"}
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    transfer = pull_manifest_module.prepare_transfer(
        manifest, tmp_path / "data", tmp_path / "pull.json"
    )

    assert transfer["files"] == []
    assert transfer["unavailable_datasets"] == [
        {"scope": "test.scope", "dataset": "archive-only"}
    ]
    assert transfer["complete"] is False


def test_command_is_registered() -> None:
    """The root command exposes manifest downloads."""
    result = CliRunner().invoke(datatrail, ["pull-manifest", "--help"])

    assert result.exit_code == 0
    assert "MANIFEST" in result.output
    assert "--cores" in result.output
