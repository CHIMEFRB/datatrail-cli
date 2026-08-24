"""Tests for Datatrail CLI."""

from datetime import datetime as dt
from typing import Any, Dict, List, Optional

import pytest

from dtcli.src import functions
from dtcli.src.functions import (
    find_unregistered_datasets,
    get_unregistered_dataset,
    view_results,
)


def test_view_results() -> None:
    """Test view_results."""
    pipeline: str = "datatrail-registration-last-completed-date"
    query: Dict[str, Any] = {"site": "chime"}
    projection: Dict[str, Any] = {"results": 1}
    results: List[Dict[str, Any]] = view_results(pipeline, query, projection)
    assert dt.strptime(
        results[0]["results"]["last_completed_date"], "%Y-%M-%d"
    ) > dt.strptime("2023-12-01", "%Y-%M-%d")


def test_view_results_bad_pipeline() -> None:
    """Test view_results with bad pipeline."""
    pipeline: str = "bad-pipeline-name"
    query: Dict[str, Any] = {"site": "chime"}
    projection: Dict[str, Any] = {"results": 1}
    results: List[Dict[str, Any]] = view_results(pipeline, query, projection)
    if results:
        assert results == []
    else:
        pytest.skip("No results found.")


def test_get_unregistered_dataset() -> None:
    """Test get_unregistered_dataset."""
    pipeline: str = "datatrail-unregistered-datasets"
    query: Dict[str, Any] = {}
    projection: Dict[str, Any] = {"results.dataset_name": 1, "results.dataset_scope": 1}
    limit: int = 1
    try:
        results: Dict[str, Any] = view_results(pipeline, query, projection, limit)[0]
    except IndexError:
        pytest.skip("No unregistered datasets found.")
    dataset_name: str = results["results"]["dataset_name"]
    dataset_scope: str = results["results"]["dataset_scope"]

    unregistered_dataset: Optional[Dict[str, Any]] = get_unregistered_dataset(
        dataset_name, dataset_scope
    )
    if unregistered_dataset:
        assert "attach_to_dataset" in unregistered_dataset["results"].keys()
        assert "reason" in unregistered_dataset["results"].keys()
    else:
        pytest.skip("No unregistered datasets found.")


def test_find_unregistered_datasets() -> None:
    """Test find_unregistered_datasets."""
    pipeline: str = "datatrail-unregistered-datasets"
    projection: Dict[str, Any] = {"results.dataset_name": 1, "results.dataset_scope": 1}
    try:
        known: Dict[str, Any] = view_results(pipeline, {}, projection, 1)[0]
    except IndexError:
        pytest.skip("No unregistered datasets found.")
    dataset_name: str = known["results"]["dataset_name"]
    dataset_scope: str = known["results"]["dataset_scope"]

    results: List[Dict[str, Any]] = find_unregistered_datasets(dataset_name)
    assert len(results) > 0
    assert all(r["results"]["dataset_name"] == dataset_name for r in results)
    assert "reason" in results[0]["results"].keys()

    # Scope of the dataset filters nothing out, an unrelated scope filters all.
    assert find_unregistered_datasets(dataset_name, scope=dataset_scope)
    assert find_unregistered_datasets(dataset_name, scope="not.a.scope") == []

    # A partial search finds at least the datasets an exact search does.
    partial: List[Dict[str, Any]] = find_unregistered_datasets(
        dataset_name[:-1], partial=True
    )
    assert len(partial) >= len(results)


def test_find_unregistered_datasets_no_match() -> None:
    """Test find_unregistered_datasets with an event that is not unregistered."""
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
        assert results == {"error": "Datatrail did not answer the scopes query."}


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
