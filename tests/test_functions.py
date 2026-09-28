"""Tests for Datatrail CLI."""

from datetime import datetime as dt
from typing import Any, Dict

from dtcli.src import functions
from dtcli.src.functions import (
    find_unregistered_datasets,
    get_unregistered_dataset,
    view_results,
)
from dtcli.utilities.results import failure


def test_view_results(results_response) -> None:
    """Test view_results with a fixed pipeline record."""
    pipeline = "datatrail-registration-last-completed-date"
    query = {"site": "chime"}
    projection = {"results": 1}
    expected = [{"results": {"last_completed_date": "2024-01-02"}}]
    results_response(pipeline, query, projection, expected)
    results = view_results(pipeline, query, projection)
    assert results == expected
    assert dt.strptime(
        results[0]["results"]["last_completed_date"], "%Y-%m-%d"
    ) > dt.strptime("2023-12-01", "%Y-%m-%d")


def test_view_results_bad_pipeline(results_response) -> None:
    """Test an unknown pipeline returns an empty result."""
    pipeline = "bad-pipeline-name"
    query = {"site": "chime"}
    projection = {"results": 1}
    results_response(pipeline, query, projection, [])
    assert view_results(pipeline, query, projection) == []


def test_get_unregistered_dataset(results_response) -> None:
    """Test the event lookup returns its registration details."""
    record = {
        "results": {
            "dataset_name": "289007650",
            "dataset_scope": "chime.event.baseband.raw",
            "attach_to_dataset": "classified.FRB",
            "reason": "Parent dataset is missing.",
        }
    }
    results_response(
        "datatrail-unregistered-datasets",
        {"site": "chime", "results.dataset_name": "289007650"},
        {"results.files": 0},
        [record],
        limit=1,
    )
    result = get_unregistered_dataset("289007650", "chime.event.baseband.raw")
    assert result == record
    assert "attach_to_dataset" in result["results"]
    assert "reason" in result["results"]


def test_find_unregistered_datasets(results_response) -> None:
    """Test exact, scoped, and partial event queries against fixed responses."""
    pipeline = "datatrail-unregistered-datasets"
    projection = {"results.files": 0}
    name, scope = "289007650", "chime.event.baseband.raw"
    record = {
        "results": {
            "dataset_name": name,
            "dataset_scope": scope,
            "reason": "Parent dataset is missing.",
        }
    }
    results_response(pipeline, {"results.dataset_name": name}, projection, [record])
    results_response(
        pipeline,
        {"results.dataset_name": name, "results.dataset_scope": scope},
        projection,
        [record],
    )
    results_response(
        pipeline,
        {"results.dataset_name": name, "results.dataset_scope": "not.a.scope"},
        projection,
        [],
    )
    results_response(
        pipeline,
        {"results.dataset_name": {"$regex": name[:-1]}},
        projection,
        [record],
    )
    results = find_unregistered_datasets(name)
    assert results == [record]
    assert all(r["results"]["dataset_name"] == name for r in results)
    assert "reason" in results[0]["results"]
    assert find_unregistered_datasets(name, scope=scope) == [record]
    assert find_unregistered_datasets(name, scope="not.a.scope") == []
    assert find_unregistered_datasets(name[:-1], partial=True) == [record]


def test_find_unregistered_datasets_no_match(results_response) -> None:
    """Test an event with no unregistered records."""
    results_response(
        "datatrail-unregistered-datasets",
        {"results.dataset_name": "not-an-event"},
        {"results.files": 0},
        [],
    )
    assert find_unregistered_datasets("not-an-event") == []


def test_list_scopes_unanswered(monkeypatch) -> None:
    """Test a non-list scopes response becomes an error, not a payload."""

    class _TextResponse:
        status_code = 502
        text = "Bad Gateway"

    class _DictResponse:
        status_code = 200

        @staticmethod
        def json() -> Dict[str, Any]:
            return {"detail": "unexpected shape"}

    monkeypatch.setattr(functions, "procure", lambda: {"server": "http://testserver"})
    for response in (_TextResponse(), _DictResponse()):
        monkeypatch.setattr(
            functions.requests, "get", lambda url, timeout, _r=response: _r
        )
        results: Dict[str, Any] = functions.list()
        assert results == {
            "error": "Datatrail did not answer the scopes query.",
            "error_code": "invalid_response",
            "retryable": False,
        }


def test_list_scopes_connection_error_is_retryable(monkeypatch) -> None:
    """Test a connection failure has a stable retryable result."""
    monkeypatch.setattr(functions, "procure", lambda: {"server": "http://testserver"})

    def _raise(url: str, timeout: int) -> None:
        raise functions.requests.exceptions.ConnectionError("offline")

    monkeypatch.setattr(functions.requests, "get", _raise)
    assert functions.list() == {
        "error": "Datatrail Server at CHIME is not responding.",
        "error_code": "service_unavailable",
        "retryable": True,
    }


def test_list_missing_config_is_not_retryable(monkeypatch) -> None:
    """Test a local configuration failure is deterministic."""

    def _raise() -> None:
        raise FileNotFoundError

    monkeypatch.setattr(functions, "procure", _raise)
    assert functions.list() == {
        "error": "No config. Create one with `datatrail config init`.",
        "error_code": "configuration_error",
        "retryable": False,
    }


def test_ps_preserves_file_query_failure(monkeypatch) -> None:
    """Test ps returns the file failure without querying policies."""
    expected = failure("offline", "service_unavailable", True)
    monkeypatch.setattr(functions, "procure", lambda: {"server": "http://testserver"})
    monkeypatch.setattr(
        functions,
        "get_dataset_file_info",
        lambda *args, **kwargs: expected,
    )

    def _unexpected_request(url: str) -> None:
        raise AssertionError(f"unexpected policy request: {url}")

    monkeypatch.setattr(functions.requests, "get", _unexpected_request)
    assert functions.ps("scope", "dataset") == (expected, None)
