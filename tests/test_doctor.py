"""Tests for readiness checks."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from click.testing import CliRunner

from dtcli import doctor
from dtcli.cli import cli


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


def test_run_checks_ready(monkeypatch, tmp_path: Path) -> None:
    """Report success when every dependency is ready."""
    certfile = tmp_path / "cert.pem"
    certfile.write_text("certificate")
    now = datetime.now(timezone.utc)
    certificate = FakeCertificate(now - timedelta(days=1), now + timedelta(days=1))
    monkeypatch.setattr(doctor, "_load_config", lambda: _config(certfile))
    monkeypatch.setattr(
        doctor.crypto, "load_certificate", lambda file_type, pem: certificate
    )

    def fake_get(url, **kwargs):
        """Return valid server and service responses."""
        if url.endswith("/query/dataset/scopes"):
            return FakeResponse(payload=["test.scope"])
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


def test_server_requires_scope_list(monkeypatch) -> None:
    """Reject an unexpected central server response."""
    monkeypatch.setattr(
        doctor.requests,
        "get",
        lambda url, **kwargs: FakeResponse(payload={"scopes": ["test.scope"]}),
    )

    result = doctor._check_server("https://example.invalid/datatrail")

    assert result["ok"] is False
    assert result["message"] == "Datatrail server returned an invalid scope list."


def test_service_requires_authentication_header(monkeypatch) -> None:
    """Reject a service response without authenticated identity."""
    monkeypatch.setattr(doctor.requests, "get", lambda url, **kwargs: FakeResponse())

    result = doctor._check_service("minoc", "https://example.invalid", "cert.pem")

    assert result["ok"] is False
    assert result["message"] == "minoc did not authenticate the certificate."


def test_doctor_json_hides_request_details(monkeypatch, tmp_path: Path) -> None:
    """Keep configured credentials and request errors out of JSON output."""
    certfile = tmp_path / "cert.pem"
    certfile.write_text("certificate")
    now = datetime.now(timezone.utc)
    certificate = FakeCertificate(now - timedelta(days=1), now + timedelta(days=1))
    config = _config(certfile)
    config["server"] = "https://user:secret@example.invalid/datatrail"
    monkeypatch.setattr("dtcli.cli.check_version", lambda: None)
    monkeypatch.setattr(doctor, "_load_config", lambda: config)
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
