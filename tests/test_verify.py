"""Tests for dataset verification."""

import json
import logging
from typing import Any, Dict

import pytest
import requests
from click.testing import CliRunner
from rich.console import Console
from rich.logging import RichHandler

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


def test_verify_json_with_real_request_failure(monkeypatch) -> None:
    """Keep diagnostic logs out of JSON when the real API helper fails."""
    monkeypatch.setattr("dtcli.cli.check_version", lambda: None)
    monkeypatch.setattr(
        verify.functions, "procure", lambda: {"server": "https://example.invalid"}
    )

    def fail_request(*args, **kwargs):
        """Simulate a transport failure containing private request details."""
        raise requests.ConnectionError("private-request-value")

    monkeypatch.setattr(verify.functions.requests, "post", fail_request)
    handler = RichHandler(console=Console())
    logger = verify.functions.logger
    logger.addHandler(handler)
    previous_disable = logging.root.manager.disable
    try:
        result = CliRunner().invoke(cli, ["verify", "test.scope", "event", "--json"])
    finally:
        logger.removeHandler(handler)

    assert result.exit_code == 2
    assert json.loads(result.output)["summary"]["unavailable"] == 1
    assert "private-request-value" not in result.output
    assert logging.root.manager.disable == previous_disable


@pytest.mark.parametrize("response", [None, {}, [None], ["invalid"]])
def test_minoc_invalid_metadata_is_unavailable(monkeypatch, response):
    """Treat malformed metadata responses as service failures without crashing."""
    monkeypatch.setattr(verify.cadcclient, "info", lambda paths: response)
    uri = "cadc:CHIMEFRB/data/file.h5"

    metadata, unavailable = verify._minoc_metadata([uri])

    assert metadata == {}
    assert unavailable == {uri}


@pytest.mark.parametrize("rows", [None, {}, [None], [["bad-row"]]])
def test_inventory_invalid_metadata_is_unavailable(monkeypatch, rows):
    """Do not misreport malformed inventory responses as missing files."""
    monkeypatch.setattr(verify.cadcclient, "query", lambda query: rows)
    uri = "cadc:CHIMEFRB/data/file.h5"

    metadata, unavailable = verify._inventory_metadata([uri])

    assert metadata == {}
    assert unavailable == {uri}


@pytest.mark.parametrize("value", [True, False, -1, "-1", 1.5, float("inf"), {}])
def test_size_rejects_invalid_byte_counts(value):
    """Do not verify files using coerced or negative byte counts."""
    assert verify._size(value) is None


@pytest.mark.parametrize("value", [True, 123, [], {}, None, " "])
def test_checksum_rejects_invalid_types(value):
    """Require a nonempty checksum string rather than coercing response values."""
    assert verify._checksum(value) is None


def test_inventory_batches_and_escapes_registered_uris(monkeypatch):
    """Keep queries bounded and correctly quote names containing apostrophes."""
    uris = [f"cadc:CHIMEFRB/data/file-{index}" for index in range(101)]
    uris[0] = "cadc:CHIMEFRB/data/file'quoted"
    calls = []

    def query(statement):
        """Record each requested batch and return matching metadata."""
        batch = uris[:100] if not calls else uris[100:]
        calls.append(statement)
        return [[uri, "12", "md5:ABC"] for uri in batch]

    monkeypatch.setattr(verify.cadcclient, "query", query)

    metadata, unavailable = verify._inventory_metadata(uris)

    assert unavailable == set()
    assert set(metadata) == set(uris)
    assert len(calls) == 2
    assert "'cadc:CHIMEFRB/data/file''quoted'" in calls[0]


def test_incomplete_metadata_is_not_present():
    """Report unavailable fields instead of passing incomplete metadata."""
    results = verify._empty_report("scope", "dataset")["results"]

    verify._compare_metadata(
        "cadc:CHIMEFRB/data/file", {"size": 12}, {"checksum": "abc"}, results
    )

    assert results["present"] == []
    assert results["unavailable"][0]["services"] == ["luskan", "minoc"]
    assert set(results["unavailable"][0]["fields"]) == {"size", "checksum"}
