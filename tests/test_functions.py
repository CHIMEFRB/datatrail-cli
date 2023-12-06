"""Tests for Datatrail CLI."""

from datetime import datetime as dt
from typing import Any, Dict, List, Optional

import pytest

from dtcli.src.functions import get_unregistered_dataset, view_results


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
