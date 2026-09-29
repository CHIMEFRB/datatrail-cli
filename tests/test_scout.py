"""Offline regressions for scout reports and confirmed healing requests."""

import json
from types import SimpleNamespace
from typing import Any, List
from unittest.mock import Mock

import pytest
import requests
from click.testing import CliRunner

from dtcli import scout

INVALID_REPORTS: List[Any] = [None, [], {}, {"error": "private-error"}, {"scope": {}}]


def response(payload=None, status=200, text=None):
    """Create a real Requests response, including its normal JSON/status checks."""
    result = requests.Response()
    result.status_code = status
    result._content = (json.dumps(payload) if text is None else text).encode()
    return result


def record(observed=None, expected=None):
    """Match the server response, whose observed sites do not include Minoc."""
    return {
        "basepath": "data/event/1",
        "filetype": ".h5",
        "observed": {"chime": 1} if observed is None else observed,
        "expected": {"chime": 1, "minoc": 0} if expected is None else expected,
    }


@pytest.fixture
def services(monkeypatch):
    """Replace every service and prompt without reading the user's configuration."""
    mocked = SimpleNamespace(
        get=Mock(return_value=response({"scope": record()})),
        post=Mock(return_value=response("ran successfully")),
        query=Mock(return_value=[["0"], [""]]),
        checksums=Mock(return_value={"data/event/1/file.h5": "a" * 32}),
        confirm=Mock(return_value=False),
        config={
            "server": "https://example.invalid/datatrail",
            "root_mounts": {"chime": "/", "hco": "/"},
        },
    )
    monkeypatch.setattr(scout, "procure", lambda: mocked.config)
    monkeypatch.setattr(scout, "validate_scope", lambda scope: True)
    monkeypatch.setattr(scout, "check_canfar_status", lambda console: (True, True))
    monkeypatch.setattr(scout.requests, "get", mocked.get)
    monkeypatch.setattr(scout.requests, "post", mocked.post)
    monkeypatch.setattr(scout.cadcclient, "query", mocked.query)
    monkeypatch.setattr(scout.cadcclient, "dataset_md5s", mocked.checksums)
    monkeypatch.setattr(scout.Confirm, "ask", mocked.confirm)
    return mocked


@pytest.mark.parametrize("arguments", [["dataset"], ["scope", "dataset"]])
def test_scout_accepts_optional_scopes(services, arguments):
    """Use returned scopes for both documented invocation forms."""
    result = CliRunner().invoke(scout.scout, arguments)

    assert result.exit_code == 0, result.output
    assert "scope" in result.output
    assert "minoc" in result.output
    services.post.assert_not_called()


@pytest.mark.parametrize("checksum", ["a" * 32, "md5:" + "A" * 32])
def test_scout_heals_minoc_missing_from_server_observed(services, checksum):
    """Include the separately queried Minoc count when selecting discrepancies."""
    services.query.return_value = [["1"], [""]]
    services.checksums.return_value = {"data/event/1/file.h5": checksum}
    services.confirm.return_value = True

    result = CliRunner().invoke(scout.scout, ["scope", "dataset"])

    assert result.exit_code == 0, result.output
    services.confirm.assert_called_once()
    services.checksums.assert_called_once_with("data/event/1")
    services.post.assert_called_once_with(
        "https://example.invalid/datatrail/commit/dataset/scout/sync",
        params={"name": "dataset", "scope": "scope", "replicate_to": "minoc"},
        json={"data/event/1/file.h5": "a" * 32},
        timeout=scout.REQUEST_TIMEOUT,
    )


def test_scout_renders_and_checks_different_site_sets(services):
    """Each scope has its own discrepancies and all sites appear in the table."""
    services.get.return_value = response(
        {
            "first": record({"chime": 2}, {"chime": 1}),
            "second": record({"baseband_buffer": 2}, {"baseband_buffer": 1, "hco": 1}),
        }
    )

    result = CliRunner().invoke(scout.scout, ["first", "second", "dataset"])

    assert result.exit_code == 0, result.output
    assert "chime: first" in result.output
    assert "baseband_buffer: second" in result.output
    assert "hco" in result.output
    assert services.confirm.call_count == 2
    services.post.assert_not_called()


def test_scout_declined_healing_never_fetches_or_posts_checksums(services):
    """Leave the archive unchanged unless the specific repair is confirmed."""
    services.query.return_value = [["1"]]

    result = CliRunner().invoke(scout.scout, ["scope", "dataset"])

    assert result.exit_code == 0, result.output
    services.confirm.assert_called_once()
    services.checksums.assert_not_called()
    services.post.assert_not_called()


@pytest.mark.parametrize(
    "site, root", [("baseband_buffer", "/data/baseband_buffer/"), ("chime", "/")]
)
def test_scout_non_minoc_healing_uses_correct_endpoint_and_payload(services, site, root):
    """Fetch site checksums from the real route and submit the validated mapping."""
    checksums = {"data/event/1/file.h5": "0123456789abcdef" * 2}
    services.get.side_effect = [
        response({"scope": record({site: 1}, {site: 0})}),
        response({root + filename: value for filename, value in checksums.items()}),
    ]
    services.confirm.return_value = True

    result = CliRunner().invoke(scout.scout, ["scope", "dataset"])

    assert result.exit_code == 0, result.output
    assert services.get.call_args_list[1].args == (
        "https://example.invalid/datatrail/query/dataset/scout/md5sums",
    )
    assert services.get.call_args_list[1].kwargs == {
        "params": {
            "basepath": "data/event/1",
            "site": site,
            "filetype": ".h5",
        },
        "timeout": scout.REQUEST_TIMEOUT,
    }
    assert services.post.call_args.kwargs["json"] == checksums
    assert services.post.call_args.kwargs["params"]["replicate_to"] == site


def test_scout_remote_root_is_independent_of_client_mount(services):
    """Client filesystem mounts cannot change the remote scout path contract."""
    services.config["root_mounts"]["baseband_buffer"] = "/archive/baseband/"
    services.get.side_effect = [
        response({"scope": record({"baseband_buffer": 1}, {"baseband_buffer": 0})}),
        response({"/data/baseband_buffer/data/event/1/file.h5": "a" * 32}),
    ]
    services.confirm.return_value = True

    result = CliRunner().invoke(scout.scout, ["scope", "dataset"])

    assert result.exit_code == 0, result.output
    assert services.post.call_args.kwargs["json"] == {"data/event/1/file.h5": "a" * 32}


def test_scout_heals_baseband_buffer_and_chime_independently(services):
    """Repair discrepancies at both scout sites even when Minoc has no files."""
    services.get.side_effect = [
        response({"scope": record({"baseband_buffer": 2, "chime": 1}, {})}),
        response(
            {
                "/data/baseband_buffer/data/event/1/first.h5": "a" * 32,
                "/data/baseband_buffer/data/event/1/second.h5": "b" * 32,
            }
        ),
        response({"/data/event/1/first.h5": "a" * 32}),
    ]
    services.confirm.return_value = True

    result = CliRunner().invoke(scout.scout, ["scope", "dataset"])

    assert result.exit_code == 0, result.output
    assert services.confirm.call_count == 2
    assert services.post.call_count == 2
    calls = services.post.call_args_list
    assert calls[0].kwargs["params"]["replicate_to"] == "baseband_buffer"
    assert calls[0].kwargs["json"] == {
        "data/event/1/first.h5": "a" * 32,
        "data/event/1/second.h5": "b" * 32,
    }
    assert calls[1].kwargs["params"]["replicate_to"] == "chime"
    assert calls[1].kwargs["json"] == {"data/event/1/first.h5": "a" * 32}
    services.checksums.assert_not_called()


@pytest.mark.parametrize(
    "filenames",
    [
        ["/archive/baseband/data/event/1/file.h5"],
        ["/data/baseband_buffer_other/data/event/1/file.h5"],
        ["/data/baseband_buffer/data/event/10/file.h5"],
        ["/data/baseband_buffer/data/event/1/../1/file.h5"],
        ["/data/baseband_buffer/data/event/1"],
        ["/data/baseband_buffer/data/event/1/file.h5", "data/event/1/file.h5"],
        ["data/event/10/file.h5"],
    ],
)
def test_scout_rejects_checksums_outside_root_or_dataset(services, filenames):
    """Never guess a path prefix or submit ambiguous names for a confirmed repair."""
    services.get.side_effect = [
        response({"scope": record({"baseband_buffer": 1}, {"baseband_buffer": 0})}),
        response(dict.fromkeys(filenames, "a" * 32)),
    ]
    services.confirm.return_value = True

    result = CliRunner().invoke(scout.scout, ["scope", "dataset"])

    assert result.exit_code == 1
    assert "Invalid checksum response" in result.output
    services.post.assert_not_called()


def test_scout_unknown_remote_site_prevents_healing(services):
    """Unknown remote mounts must fail rather than infer a prefix from filenames."""
    services.get.side_effect = [
        response({"scope": record({"new_site": 1}, {"new_site": 0})}),
        response({"/new_mount/data/event/1/file.h5": "a" * 32}),
    ]
    services.confirm.return_value = True

    result = CliRunner().invoke(scout.scout, ["scope", "dataset"])

    assert result.exit_code == 1
    services.post.assert_not_called()


def test_scout_negative_expected_count_prevents_healing(services):
    """An invalid expected count must not make a missing replica look repairable."""
    services.get.return_value = response({"scope": record({"chime": 0}, {"chime": -1})})
    services.confirm.return_value = True

    result = CliRunner().invoke(scout.scout, ["scope", "dataset"])

    assert result.exit_code == 1
    services.confirm.assert_not_called()
    services.post.assert_not_called()


def test_scout_unknown_observed_count_does_not_prompt_healing(services):
    """The server's -1 sentinel represents an unavailable scout, not a replica."""
    services.get.return_value = response({"scope": record({"chime": -1}, {"chime": 0})})
    services.confirm.return_value = True

    result = CliRunner().invoke(scout.scout, ["scope", "dataset"])

    assert result.exit_code == 0, result.output
    services.confirm.assert_not_called()
    services.post.assert_not_called()


@pytest.mark.parametrize("error", [requests.ConnectionError, requests.Timeout])
def test_scout_request_errors_are_concise_failures(services, error):
    """Report expected transport failures without an uncaught exception."""
    services.get.side_effect = error("private-request-details")

    result = CliRunner().invoke(scout.scout, ["scope", "dataset"])

    assert result.exit_code == 1
    assert isinstance(result.exception, SystemExit)
    assert "failed" in result.output.lower() or "timed out" in result.output.lower()
    assert "private-request-details" not in result.output
    services.post.assert_not_called()


@pytest.mark.parametrize("payload", INVALID_REPORTS)
def test_scout_rejects_empty_or_malformed_results(services, payload):
    """Avoid table/index errors and never heal from an invalid report."""
    services.get.return_value = response(payload)

    result = CliRunner().invoke(scout.scout, ["dataset"])

    assert result.exit_code == 1
    assert isinstance(result.exception, SystemExit)
    services.query.assert_not_called()
    services.confirm.assert_not_called()
    services.post.assert_not_called()


def test_scout_rejects_failed_http_status_before_using_payload(services):
    """A valid-looking JSON document cannot override HTTP failure."""
    services.get.return_value = response({"scope": record()}, status=503)

    result = CliRunner().invoke(scout.scout, ["scope", "dataset"])

    assert result.exit_code == 1
    services.query.assert_not_called()
    services.post.assert_not_called()


@pytest.mark.parametrize(
    "payload",
    [None, [], {}, {"error": "failed"}, {"file": ""}, {"file": 1}, {"file": "not-md5"}],
)
def test_scout_invalid_checksum_payload_prevents_healing(services, payload):
    """Never submit empty, error, or malformed checksum responses as replicas."""
    services.get.side_effect = [
        response({"scope": record({"chime": 2}, {"chime": 1})}),
        response(payload),
    ]
    services.confirm.return_value = True

    result = CliRunner().invoke(scout.scout, ["scope", "dataset"])

    assert result.exit_code == 1
    assert isinstance(result.exception, SystemExit)
    services.post.assert_not_called()


@pytest.mark.parametrize(
    "failure",
    [
        requests.ConnectionError("private"),
        requests.Timeout("private"),
        response({}, 503),
        response(text="not-json"),
    ],
)
def test_scout_checksum_get_failure_prevents_post(services, failure):
    """Failed checksum requests cannot trigger a healing POST."""
    services.get.side_effect = [
        response({"scope": record({"chime": 2}, {"chime": 1})}),
        failure,
    ]
    services.confirm.return_value = True

    result = CliRunner().invoke(scout.scout, ["scope", "dataset"])

    assert result.exit_code == 1
    assert isinstance(result.exception, SystemExit)
    assert "private" not in result.output
    services.post.assert_not_called()


def test_scout_continues_independent_healing_after_failure(services):
    """A failed repair leaves the command unsuccessful but permits another repair."""
    services.get.side_effect = [
        response({"scope": record({"chime": 2, "hco": 2}, {"chime": 1, "hco": 1})}),
        response({}, status=503),
        response({"data/event/1/file.h5": "a" * 32}),
    ]
    services.confirm.return_value = True

    result = CliRunner().invoke(scout.scout, ["scope", "dataset"])

    assert result.exit_code == 1
    assert services.confirm.call_count == 2
    services.post.assert_called_once()
    assert services.post.call_args.kwargs["params"]["replicate_to"] == "hco"
    assert "Healing successful" in result.output


@pytest.mark.parametrize(
    "failure", [requests.ConnectionError("private"), response({}, 503)]
)
def test_scout_failed_healing_post_is_nonzero(services, failure):
    """Report failed writes as command failures after explicit confirmation."""
    services.query.return_value = [["1"], [""]]
    services.confirm.return_value = True
    services.post.side_effect = [failure]

    result = CliRunner().invoke(scout.scout, ["scope", "dataset"])

    assert result.exit_code == 1
    assert isinstance(result.exception, SystemExit)
    assert "Healing failed" in result.output
    assert "private" not in result.output


def test_scout_invalid_initial_json_is_concise(services):
    """Do not expose malformed server contents or proceed to healing."""
    services.get.return_value = response(text="private-response")

    result = CliRunner().invoke(scout.scout, ["dataset"])

    assert result.exit_code == 1
    assert isinstance(result.exception, SystemExit)
    assert "invalid JSON" in result.output
    assert "private-response" not in result.output
    services.post.assert_not_called()


def test_scout_count_failure_does_not_heal_unknown_minoc_state(services):
    """Continue checking independent scopes without repairing an unknown count."""
    services.get.return_value = response({"first": record(), "second": record()})
    services.query.side_effect = [RuntimeError("private-query"), [["1"]]]
    services.confirm.return_value = True

    result = CliRunner().invoke(scout.scout, ["dataset"])

    assert result.exit_code == 1
    services.confirm.assert_called_once()
    services.post.assert_called_once()
    assert services.post.call_args.kwargs["params"]["scope"] == "second"
    assert "private-query" not in result.output


def test_scout_minoc_checksum_failure_prevents_healing(services):
    """A failed inventory checksum lookup cannot be submitted as a repair."""
    services.query.return_value = [["1"]]
    services.confirm.return_value = True
    services.checksums.side_effect = RuntimeError("private-query")

    result = CliRunner().invoke(scout.scout, ["scope", "dataset"])

    assert result.exit_code == 1
    assert "Checksum query failed" in result.output
    assert "private-query" not in result.output
    services.post.assert_not_called()
