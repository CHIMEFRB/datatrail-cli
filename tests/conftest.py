"""HTTP fixtures for tests that do not need the live services."""

import json

import pytest
import requests


@pytest.fixture
def http_responses(monkeypatch):
    """Serve explicit responses through Requests without bypassing JSON decoding."""
    responses = {}
    unexpected = []

    def add(method, url, data, payload=None):
        key = (method, url, json.dumps(payload, sort_keys=True))
        responses[key] = data

    def send(session, prepared, **kwargs):
        try:
            payload = json.loads(prepared.body) if prepared.body else None
        except (TypeError, ValueError) as error:
            unexpected.append((prepared.method, prepared.url, "non-JSON body"))
            raise AssertionError("Unexpected non-JSON request body") from error
        key = (prepared.method, prepared.url, json.dumps(payload, sort_keys=True))
        if key not in responses:
            unexpected.append(key)
            raise AssertionError(f"Unexpected HTTP request: {key}")
        response = requests.Response()
        response.status_code = 200
        response.url = prepared.url
        response.request = prepared
        response.headers["Content-Type"] = "application/json"
        response.encoding = "utf-8"
        response._content = json.dumps(responses[key]).encode("utf-8")
        return response

    monkeypatch.setattr(requests.Session, "send", send)
    yield add
    # CLI commands can catch exceptions, so also check for unexpected requests here.
    assert not unexpected, f"Unexpected HTTP requests: {unexpected}"


@pytest.fixture
def datatrail_api(http_responses):
    """Supply a small dataset hierarchy for CLI output and filtering tests."""
    server = "https://frb.chimenet.ca/datatrail"
    scope = "chime.event.baseband.raw"
    http_responses(
        "GET",
        f"{server}/query/dataset/scopes",
        [scope, "chime.event.intensity.raw"],
    )
    http_responses(
        "GET",
        f"{server}/query/dataset/larger?scope={scope}",
        {"larger_datasets": ["classified.FRB", "unclassified"]},
    )
    http_responses(
        "GET",
        f"{server}/query/dataset/children/{scope}/classified.FRB",
        {"contains": ["289007650", "289007651"]},
    )
    http_responses(
        "POST",
        f"{server}/query/dataset/find",
        {
            "file_replica_locations": {
                "minoc": ["data/test-missing/222266914/file.msgpack"]
            }
        },
        {"scope": "chime.event.intensity.raw", "name": "222266914"},
    )
    http_responses(
        "POST",
        "https://frb.chimenet.ca/results/view",
        [],
        {
            "query": {
                "pipeline": "datatrail-unregistered-datasets",
                "results.dataset_name": "not-an-event",
            },
            "projection": {"results.files": 0},
            "limit": 100,
        },
    )


@pytest.fixture
def results_response(http_responses):
    """Register the expected query and response for a workflow-results request."""

    def add(pipeline, query, projection, data, limit=100):
        http_responses(
            "POST",
            "https://frb.chimenet.ca/results/view",
            data,
            {
                "query": {"pipeline": pipeline, **query},
                "projection": projection,
                "limit": limit,
            },
        )

    return add
