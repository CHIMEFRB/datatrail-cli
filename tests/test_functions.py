"""Tests for Datatrail CLI."""

from datetime import datetime as dt
from typing import Any, Dict

import pytest

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


def _fake_list(scope=None, dataset=None, verbose=0, quiet=False):
    """Stand-in for functions.list with one scope not answering."""
    if scope is None:
        return {"scopes": ["b.scope", "a.scope", "c.scope"]}
    if dataset is None:
        if scope == "a.scope":
            return {"larger_datasets": ["data.other", "data.good", "skip.me"]}
        if scope == "c.scope":
            return {"larger_datasets": []}
        return {"error": "Datatrail Server at CHIME is not responding."}
    if dataset == "data.good":
        return {"datasets": ["child1", "child2"]}
    return {"error": "Datatrail Server at CHIME is not responding."}


def test_discover_datasets(monkeypatch) -> None:
    """Test discover_datasets filtering, sorting, and expansion."""
    monkeypatch.setattr(functions, "list", _fake_list)
    results: Dict[str, Any] = functions.discover_datasets(match="data", expand=True)
    assert results["results"] == [
        {"scope": "a.scope", "dataset": "child2", "parent": "data.good"},
        {"scope": "a.scope", "dataset": "child1", "parent": "data.good"},
        {"scope": "a.scope", "dataset": "data.other", "parent": None},
    ]
    # An unanswered query is reported, never shown as empty.
    assert results["failed"] == [
        "children of a.scope data.other",
        "datasets in b.scope",
    ]


def test_discover_datasets_no_expand(monkeypatch) -> None:
    """Test discover_datasets without expansion, terms ANDed against scope."""
    monkeypatch.setattr(functions, "list", _fake_list)
    results: Dict[str, Any] = functions.discover_datasets(match="a.scope,data")
    assert results["results"] == [
        {"scope": "a.scope", "dataset": "data.good", "parent": None},
        {"scope": "a.scope", "dataset": "data.other", "parent": None},
    ]
    assert results["failed"] == ["datasets in b.scope"]


def test_discover_datasets_single_scope(monkeypatch) -> None:
    """Test discover_datasets walking one named scope only."""
    monkeypatch.setattr(functions, "list", _fake_list)
    results: Dict[str, Any] = functions.discover_datasets(scope="a.scope")
    assert [r["dataset"] for r in results["results"]] == [
        "data.good",
        "data.other",
        "skip.me",
    ]
    assert results["failed"] == []


def test_discover_datasets_empty_scope_is_not_failure(monkeypatch) -> None:
    """Test a scope that answers with no datasets is empty, not failed."""
    monkeypatch.setattr(functions, "list", _fake_list)
    results: Dict[str, Any] = functions.discover_datasets(scope="c.scope")
    assert results["results"] == []
    assert results["failed"] == []


def test_discover_datasets_unanswered_scopes_query(monkeypatch) -> None:
    """Test a non-list scopes answer is an error, never walked as text."""

    def bad_list(scope=None, dataset=None, verbose=0, quiet=False):
        return {"scopes": "Bad Gateway"}

    monkeypatch.setattr(functions, "list", bad_list)
    results: Dict[str, Any] = functions.discover_datasets(match="gain")
    assert "error" in results
    assert "results" not in results


def test_discover_datasets_recursive_paths(monkeypatch) -> None:
    """Test recursive discovery paths, ordering, filtering, and duplicates."""
    calls = []
    children = {
        "wanted.root": ["branch.b", "branch.a", "branch.a"],
        "branch.a": ["leaf.shared", "leaf.a"],
        "branch.b": ["leaf.b", "leaf.shared"],
    }

    def fake_list(scope=None, dataset=None, verbose=0, quiet=False):
        if dataset is None:
            return {
                "larger_datasets": [
                    "wanted.root",
                    "skip.root",
                    "wanted.empty",
                    "wanted.root",
                ]
            }
        calls.append(dataset)
        return {"datasets": children.get(dataset, [])}

    monkeypatch.setattr(functions, "list", fake_list)
    results = functions.discover_datasets(
        scope="test.scope", match="wanted", recursive=True
    )
    assert results == {
        "results": [
            {
                "scope": "test.scope",
                "dataset": "wanted.empty",
                "parent": None,
                "path": ["wanted.empty"],
            },
            {
                "scope": "test.scope",
                "dataset": "leaf.a",
                "parent": "branch.a",
                "path": ["wanted.root", "branch.a", "leaf.a"],
            },
            {
                "scope": "test.scope",
                "dataset": "leaf.shared",
                "parent": "branch.a",
                "path": ["wanted.root", "branch.a", "leaf.shared"],
            },
            {
                "scope": "test.scope",
                "dataset": "leaf.b",
                "parent": "branch.b",
                "path": ["wanted.root", "branch.b", "leaf.b"],
            },
        ],
        "failed": [],
    }
    assert "skip.root" not in calls
    assert calls.count("wanted.root") == 1
    assert calls.count("leaf.shared") == 1


def test_discover_datasets_recursive_empty_and_failed(monkeypatch) -> None:
    """Test recursive discovery keeps empty and failed branches distinct."""

    def fake_list(scope=None, dataset=None, verbose=0, quiet=False):
        if dataset is None:
            return {"larger_datasets": ["root"]}
        if dataset == "root":
            return {"datasets": ["offline", "malformed", "empty"]}
        if dataset == "offline":
            return {"error": "service unavailable"}
        if dataset == "malformed":
            return {"datasets": [None]}
        return {"datasets": []}

    monkeypatch.setattr(functions, "list", fake_list)
    results = functions.discover_datasets(scope="test.scope", recursive=True)
    assert results["results"] == [
        {
            "scope": "test.scope",
            "dataset": "empty",
            "parent": "root",
            "path": ["root", "empty"],
        },
        {
            "scope": "test.scope",
            "dataset": "malformed",
            "parent": "root",
            "path": ["root", "malformed"],
        },
        {
            "scope": "test.scope",
            "dataset": "offline",
            "parent": "root",
            "path": ["root", "offline"],
        },
    ]
    assert results["failed"] == [
        "children of test.scope root / malformed",
        "children of test.scope root / offline",
    ]


def test_discover_datasets_recursive_cycle(monkeypatch) -> None:
    """Test recursive discovery stops and reports a hierarchy cycle."""
    calls = []

    def fake_list(scope=None, dataset=None, verbose=0, quiet=False):
        if dataset is None:
            return {"larger_datasets": ["root"]}
        calls.append(dataset)
        return {"datasets": ["branch"] if dataset == "root" else ["root"]}

    monkeypatch.setattr(functions, "list", fake_list)
    results = functions.discover_datasets(scope="test.scope", recursive=True)
    assert results["results"] == [
        {
            "scope": "test.scope",
            "dataset": "branch",
            "parent": "root",
            "path": ["root", "branch"],
        }
    ]
    assert results["failed"] == [
        "cycle in test.scope: root / branch / root",
    ]
    assert calls == ["root", "branch"]


@pytest.mark.parametrize(
    "names", ["Bad Gateway", {"name": "root"}, [None], ["root", None], [" "], 7]
)
def test_discovery_rejects_invalid_scope_names(monkeypatch, http_responses, names):
    """Malformed scope names cannot start an incomplete archive walk."""
    monkeypatch.setattr(functions, "procure", lambda: {"server": "http://testserver"})
    http_responses("GET", "http://testserver/query/dataset/scopes", names)

    result = functions.discover_datasets(match="root")

    assert "error" in result
    assert "results" not in result


@pytest.mark.parametrize(
    "names", ["Bad Gateway", {"name": "root"}, [None], ["root", None], [" "], 7]
)
def test_discovery_rejects_invalid_larger_dataset_names(
    monkeypatch, http_responses, names
):
    """An invalid collection is a failed scope, never a list of bogus rows."""
    monkeypatch.setattr(functions, "procure", lambda: {"server": "http://testserver"})
    http_responses(
        "GET",
        "http://testserver/query/dataset/larger?scope=test.scope",
        {"larger_datasets": names},
    )

    assert functions.discover_datasets(scope="test.scope") == {
        "results": [],
        "failed": ["datasets in test.scope"],
    }


@pytest.mark.parametrize(
    "names", ["Bad Gateway", {"name": "leaf"}, [None], ["leaf", None], [" "], 7]
)
def test_discovery_rejects_invalid_child_names(monkeypatch, http_responses, names):
    """Malformed children retain the parent and report an incomplete map."""
    monkeypatch.setattr(functions, "procure", lambda: {"server": "http://testserver"})
    http_responses(
        "GET",
        "http://testserver/query/dataset/larger?scope=test.scope",
        {"larger_datasets": ["root"]},
    )
    http_responses(
        "GET",
        "http://testserver/query/dataset/children/test.scope/root",
        {"contains": names},
    )

    assert functions.discover_datasets(scope="test.scope", expand=True) == {
        "results": [{"scope": "test.scope", "dataset": "root", "parent": None}],
        "failed": ["children of test.scope root"],
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
