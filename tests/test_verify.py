"""Tests for dataset verification."""

import json
from typing import Any, Dict

from click.testing import CliRunner

from dtcli import verify
from dtcli.cli import cli


def _metadata(size: int, checksum: str) -> Dict[str, Any]:
    """Create file metadata for a test."""
    return {"size": size, "checksum": checksum}


def test_verify_dataset_categories(monkeypatch) -> None:
    """Classify exact file and metadata outcomes."""
    names = ["a.h5", "b.h5", "c.h5", "d.h5", "e.h5"]
    uris = [f"cadc:CHIMEFRB/data/{name}" for name in names]
    monkeypatch.setattr(
        verify.functions,
        "get_dataset_file_info",
        lambda scope, dataset: {
            "file_replica_locations": {"minoc": [f"data/{name}" for name in names]}
        },
    )
    monkeypatch.setattr(
        verify,
        "_minoc_metadata",
        lambda files: (
            {
                uris[0]: _metadata(10, "aaa"),
                uris[2]: _metadata(30, "ccc"),
                uris[3]: _metadata(40, "ddd"),
                uris[4]: _metadata(50, "eee"),
            },
            set(),
        ),
    )
    monkeypatch.setattr(
        verify,
        "_inventory_metadata",
        lambda files: (
            {
                uris[0]: _metadata(10, "aaa"),
                uris[1]: _metadata(20, "bbb"),
                uris[2]: _metadata(31, "ccc"),
                uris[3]: _metadata(40, "different"),
            },
            {uris[4]},
        ),
    )

    report = verify.verify_dataset("test.scope", "event")

    assert report["ok"] is False
    assert report["summary"] == {
        "present": 1,
        "missing": 1,
        "size_mismatch": 1,
        "checksum_mismatch": 1,
        "unavailable": 1,
    }
    assert report["results"]["present"][0]["uri"] == uris[0]
    assert report["results"]["missing"][0]["services"] == ["minoc"]
    assert report["results"]["size_mismatch"][0]["uri"] == uris[2]
    assert report["results"]["checksum_mismatch"][0]["uri"] == uris[3]
    assert report["results"]["unavailable"][0]["services"] == ["luskan"]


def test_inventory_metadata_uses_exact_uris(monkeypatch) -> None:
    """Query only the registered CADC URIs."""
    calls = []

    def fake_query(query: str):
        """Return one inventory row."""
        calls.append(query)
        return [["cadc:CHIMEFRB/data/a.h5", "12", "md5:ABC"], [""]]

    monkeypatch.setattr(verify.cadcclient, "query", fake_query)

    metadata, unavailable = verify._inventory_metadata(["cadc:CHIMEFRB/data/a.h5"])

    assert unavailable == set()
    assert metadata == {"cadc:CHIMEFRB/data/a.h5": {"size": 12, "checksum": "abc"}}
    assert "where uri in ('cadc:CHIMEFRB/data/a.h5')" in calls[0]


def test_verify_json_reports_unavailable_service(monkeypatch) -> None:
    """Return machine-readable failure when Datatrail is unavailable."""
    monkeypatch.setattr("dtcli.cli.check_version", lambda: None)
    monkeypatch.setattr(
        verify.functions,
        "get_dataset_file_info",
        lambda scope, dataset: {"error": "connection failed"},
    )

    result = CliRunner().invoke(cli, ["verify", "test.scope", "event", "--json"])

    assert result.exit_code == 2
    report = json.loads(result.output)
    assert report["ok"] is False
    assert report["summary"]["unavailable"] == 1
    assert report["results"]["unavailable"][0]["services"] == ["datatrail"]
    assert "connection failed" not in result.output


def test_verify_empty_registration_is_clean(monkeypatch) -> None:
    """Treat an empty registered file list as a valid result."""
    monkeypatch.setattr(
        verify.functions,
        "get_dataset_file_info",
        lambda scope, dataset: {"file_replica_locations": {"minoc": []}},
    )

    report = verify.verify_dataset("test.scope", "empty")

    assert report["registered"] == 0
    assert report["ok"] is True
