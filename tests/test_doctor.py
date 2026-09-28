"""Tests for readiness checks."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import requests
from click.testing import CliRunner

from dtcli import doctor
from dtcli.cli import cli
from dtcli.config import procure


class FakeCertificate:
    """Certificate with controlled validity dates."""

    def __init__(self, not_before: datetime, not_after: datetime):
        """Store certificate dates."""
        self.not_before = not_before
        self.not_after = not_after

    def get_notBefore(self) -> bytes:
        """Return the start date as an X509 timestamp."""
        return self.not_before.strftime("%Y%m%d%H%M%SZ").encode("ascii")

    def get_notAfter(self) -> bytes:
        """Return the end date as an X509 timestamp."""
        return self.not_after.strftime("%Y%m%d%H%M%SZ").encode("ascii")


class FakeResponse:
    """Small requests response substitute."""

    def __init__(self, status_code=200, payload=None, headers=None):
        """Store response fields."""
        self.status_code = status_code
        self.payload = payload
        self.headers = headers or {}

    def json(self):
        """Return the configured JSON payload."""
        return self.payload


def _config(certfile: Path):
    """Create a valid test configuration."""
    return {
        "server": "https://example.invalid/datatrail",
        "vospace_certfile": str(certfile),
        "site": "local",
        "root_mounts": {"local": "./"},
    }


def _health(status="ok", database="ok", api="ok"):
    """Create a health response matching the server endpoint."""
    return {
        "status": status,
        "checks": {
            "database": {"status": database, "response_time_ms": 7.58},
            "api": {"status": api, "response_time_ms": 8.25},
        },
        "timestamp": "2026-08-31T19:57:21.140372+00:00",
        "total_response_time_ms": 8.25,
    }


def test_run_checks_ready(monkeypatch, tmp_path: Path) -> None:
    """Report success when every dependency is ready."""
    certfile = tmp_path / "cert.pem"
    certfile.write_text("certificate")
    now = datetime.now(timezone.utc)
    certificate = FakeCertificate(now - timedelta(days=1), now + timedelta(days=1))
    monkeypatch.setattr(doctor, "procure", lambda **kwargs: _config(certfile))
    monkeypatch.setattr(
        doctor.crypto, "load_certificate", lambda file_type, pem: certificate
    )

    def fake_get(url, **kwargs):
        """Return valid server and service responses."""
        if url == "https://example.invalid/datatrail/health/check":
            assert kwargs == {"timeout": doctor.REQUEST_TIMEOUT}
            return FakeResponse(payload=_health())
        assert url in doctor.SERVICE_URLS.values()
        return FakeResponse(headers={"x-vo-authenticated": "user"})

    monkeypatch.setattr(doctor.requests, "get", fake_get)

    report = doctor.run_checks()

    assert report["ok"] is True
    assert list(report["checks"]) == [
        "config",
        "server",
        "certificate",
        "minoc",
        "luskan",
    ]
    assert all(check["ok"] for check in report["checks"].values())


def test_certificate_expired(monkeypatch, tmp_path: Path) -> None:
    """Reject an expired certificate without showing its contents."""
    certfile = tmp_path / "cert.pem"
    certfile.write_text("private-value")
    now = datetime.now(timezone.utc)
    certificate = FakeCertificate(now - timedelta(days=2), now - timedelta(days=1))
    monkeypatch.setattr(
        doctor.crypto, "load_certificate", lambda file_type, pem: certificate
    )

    result = doctor._check_certificate(str(certfile))

    assert result == {"ok": False, "message": "CANFAR certificate is expired."}
    assert "private-value" not in result["message"]


@pytest.mark.parametrize("suffix", ["", "/"])
def test_server_checks_health_endpoint(monkeypatch, suffix) -> None:
    """Use the bounded health request regardless of a trailing slash."""
    calls = []

    def fake_get(url, **kwargs):
        """Record the request and return a healthy server response."""
        calls.append((url, kwargs))
        return FakeResponse(payload=_health())

    monkeypatch.setattr(doctor.requests, "get", fake_get)

    result = doctor._check_server("https://example.invalid/datatrail" + suffix)

    assert result == {"ok": True, "message": "Datatrail server is ready."}
    assert calls == [
        (
            "https://example.invalid/datatrail/health/check",
            {"timeout": doctor.REQUEST_TIMEOUT},
        )
    ]


@pytest.mark.parametrize(
    "payload",
    [
        None,
        [],
        ["test.scope"],
        "ok",
        {},
        {"status": True, "checks": _health()["checks"]},
        {"status": "ok"},
        {"status": "ok", "checks": []},
        {"status": "ok", "checks": {}},
        {"status": "ok", "checks": {"database": {"status": "ok"}}},
        {"status": "ok", "checks": {"database": "ok", "api": {"status": "ok"}}},
        {"status": "ok", "checks": {"database": {}, "api": {"status": "ok"}}},
    ],
)
def test_server_rejects_malformed_health_report(monkeypatch, payload) -> None:
    """Reject malformed health reports, including the old scopes payload."""
    monkeypatch.setattr(
        doctor.requests,
        "get",
        lambda url, **kwargs: FakeResponse(payload=payload),
    )

    result = doctor._check_server("https://example.invalid/datatrail")

    assert result["ok"] is False
    assert result["message"] == "Datatrail server returned an invalid health report."


@pytest.mark.parametrize(
    "payload",
    [
        _health(status="error"),
        _health(database="unhealthy"),
        _health(api="degraded"),
    ],
)
def test_server_rejects_unhealthy_status(monkeypatch, payload) -> None:
    """Fail when the server or a component is unhealthy despite HTTP 200."""
    monkeypatch.setattr(
        doctor.requests, "get", lambda url, **kwargs: FakeResponse(payload=payload)
    )

    result = doctor._check_server("https://example.invalid/datatrail")

    assert result == {
        "ok": False,
        "message": "Datatrail server reported an unhealthy status.",
    }


def test_server_rejects_http_error(monkeypatch) -> None:
    """A healthy-looking payload cannot override a failed HTTP response."""
    monkeypatch.setattr(
        doctor.requests,
        "get",
        lambda url, **kwargs: FakeResponse(status_code=503, payload=_health()),
    )

    result = doctor._check_server("https://example.invalid/datatrail")

    assert result == {"ok": False, "message": "Datatrail server returned HTTP 503."}


def test_server_rejects_invalid_json(monkeypatch) -> None:
    """Hide response contents when JSON decoding fails."""

    class InvalidResponse(FakeResponse):
        """Response that cannot be decoded as JSON."""

        def json(self):
            """Raise a decoding error containing private response text."""
            raise ValueError("private-response")

    monkeypatch.setattr(doctor.requests, "get", lambda url, **kwargs: InvalidResponse())

    result = doctor._check_server("https://example.invalid/datatrail")

    assert result == {"ok": False, "message": "Datatrail server returned invalid JSON."}


@pytest.mark.parametrize("error", [requests.Timeout, requests.ConnectionError])
def test_server_hides_request_errors(monkeypatch, error) -> None:
    """Report network failures without exposing the request URL."""

    def fail_request(url, **kwargs):
        """Raise a network error containing sensitive request details."""
        raise error(url)

    monkeypatch.setattr(doctor.requests, "get", fail_request)

    result = doctor._check_server("https://user:secret@example.invalid/datatrail")

    assert result == {"ok": False, "message": "Datatrail server request failed."}


@pytest.mark.parametrize("identity", [None, "", " \t"])
def test_service_requires_authentication_header(monkeypatch, identity) -> None:
    """Reject a service response without authenticated identity."""
    monkeypatch.setattr(
        doctor.requests,
        "get",
        lambda url, **kwargs: FakeResponse(headers={"x-vo-authenticated": identity}),
    )

    result = doctor._check_service("minoc", "https://example.invalid", "cert.pem")

    assert result["ok"] is False
    assert result["message"] == "minoc did not authenticate the certificate."


def test_certificate_rejects_invalid_path():
    """Report an invalid configured path without raising an exception."""
    assert doctor._check_certificate("invalid\x00path") == {
        "ok": False,
        "message": "CANFAR certificate could not be read.",
    }


def test_service_handles_certificate_read_failure(monkeypatch):
    """Handle a certificate that disappears before Requests opens it."""

    def fail_request(*args, **kwargs):
        """Raise the certificate path error produced by Requests."""
        raise OSError("private-certificate-path")

    monkeypatch.setattr(doctor.requests, "get", fail_request)

    assert doctor._check_service("minoc", "https://example.invalid", "cert.pem") == {
        "ok": False,
        "message": "minoc request failed.",
    }


def test_doctor_json_hides_request_details(monkeypatch, tmp_path: Path) -> None:
    """Keep configured credentials and request errors out of JSON output."""
    certfile = tmp_path / "cert.pem"
    certfile.write_text("certificate")
    now = datetime.now(timezone.utc)
    certificate = FakeCertificate(now - timedelta(days=1), now + timedelta(days=1))
    config = _config(certfile)
    config["server"] = "https://user:secret@example.invalid/datatrail"
    monkeypatch.setattr("dtcli.cli.check_version", lambda: None)
    monkeypatch.setattr(doctor, "procure", lambda **kwargs: config)
    monkeypatch.setattr(
        doctor.crypto, "load_certificate", lambda file_type, pem: certificate
    )

    def fail_request(url, **kwargs):
        """Raise an error containing sensitive request details."""
        raise requests.ConnectionError(url)

    monkeypatch.setattr(doctor.requests, "get", fail_request)

    result = CliRunner().invoke(cli, ["doctor", "--json"])

    assert result.exit_code == 1
    report = json.loads(result.output)
    assert report["ok"] is False
    assert report["checks"]["server"]["ok"] is False
    assert "secret" not in result.output
    assert "user:" not in result.output


@pytest.mark.parametrize("contents", [None, "server: [private-value", "[]", "{}"])
def test_doctor_json_with_invalid_config(monkeypatch, tmp_path, contents) -> None:
    """Use the shared loader without logs or network probes on config failure."""
    configfile = tmp_path / "config.yaml"
    if contents is not None:
        configfile.write_text(contents)
    monkeypatch.setattr("dtcli.cli.check_version", lambda: None)
    monkeypatch.setattr(
        doctor, "procure", lambda **kwargs: procure(configfile, **kwargs)
    )

    def unexpected_request(*args, **kwargs):
        """Fail the test if a failed configuration triggers a network probe."""
        pytest.fail("Network probes must be skipped when configuration fails.")

    monkeypatch.setattr(doctor.requests, "get", unexpected_request)

    result = CliRunner().invoke(cli, ["doctor", "--json"])

    assert result.exit_code == 1
    report = json.loads(result.output)
    assert report["ok"] is False
    assert all(check["ok"] is False for check in report["checks"].values())
    assert "private-value" not in result.output
    assert str(configfile) not in result.output
    assert report["checks"]["server"]["message"] == (
        "Not checked because configuration failed."
    )
