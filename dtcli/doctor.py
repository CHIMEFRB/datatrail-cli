"""Datatrail readiness checks."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import click
import requests
from OpenSSL import crypto  # type: ignore

from dtcli.config import procure, validate

REQUEST_TIMEOUT = 10
SERVICE_URLS = {
    "minoc": "https://ws-uv.canfar.net/minoc/capabilities",
    "luskan": "https://ws-uv.canfar.net/luskan/capabilities",
}


def _result(ok: bool, message: str) -> Dict[str, Any]:
    """Create one check result."""
    return {"ok": ok, "message": message}


def _check_config() -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
    """Format shared configuration checks for the readiness report."""
    config = procure(quiet=True)
    if config is None:
        return _result(False, "Configuration could not be loaded."), None

    if not validate(config):
        return _result(False, "Configuration is missing required values."), None
    return _result(True, "Configuration is ready."), config


def _check_server(server: str) -> Dict[str, Any]:
    """Check the central server's health report."""
    try:
        response = requests.get(
            server.rstrip("/") + "/health/check",
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException:
        return _result(False, "Datatrail server request failed.")
    if not 200 <= response.status_code < 300:
        return _result(False, f"Datatrail server returned HTTP {response.status_code}.")
    try:
        health = response.json()
    except (requests.JSONDecodeError, ValueError):
        return _result(False, "Datatrail server returned invalid JSON.")
    if not isinstance(health, dict) or not isinstance(health.get("status"), str):
        return _result(False, "Datatrail server returned an invalid health report.")
    checks = health.get("checks")
    if not isinstance(checks, dict) or not {"database", "api"}.issubset(checks):
        return _result(False, "Datatrail server returned an invalid health report.")
    if not all(
        isinstance(check, dict) and isinstance(check.get("status"), str)
        for check in checks.values()
    ):
        return _result(False, "Datatrail server returned an invalid health report.")
    if health["status"] != "ok" or any(
        check["status"] != "ok" for check in checks.values()
    ):
        return _result(False, "Datatrail server reported an unhealthy status.")
    return _result(True, "Datatrail server is ready.")


def _certificate_time(value: Optional[bytes]) -> Optional[datetime]:
    """Parse an X509 certificate timestamp."""
    if value is None:
        return None
    try:
        return datetime.strptime(value.decode("ascii"), "%Y%m%d%H%M%SZ").replace(
            tzinfo=timezone.utc
        )
    except (UnicodeDecodeError, ValueError):
        return None


def _check_certificate(certfile: str) -> Dict[str, Any]:
    """Check that the configured certificate is current."""
    try:
        pem = Path(certfile).read_bytes()
    except (OSError, ValueError):
        return _result(False, "CANFAR certificate could not be read.")
    try:
        certificate = crypto.load_certificate(crypto.FILETYPE_PEM, pem)
    except crypto.Error:
        return _result(False, "CANFAR certificate is not valid PEM.")

    not_before = _certificate_time(certificate.get_notBefore())
    not_after = _certificate_time(certificate.get_notAfter())
    now = datetime.now(timezone.utc)
    if not_before is None or not_after is None:
        return _result(False, "CANFAR certificate dates are invalid.")
    if now < not_before:
        return _result(False, "CANFAR certificate is not valid yet.")
    if now >= not_after:
        return _result(False, "CANFAR certificate is expired.")
    return _result(True, "CANFAR certificate is valid.")


def _check_service(name: str, url: str, certfile: str) -> Dict[str, Any]:
    """Check one authenticated CANFAR service."""
    try:
        response = requests.get(
            url,
            cert=certfile,
            allow_redirects=True,
            timeout=REQUEST_TIMEOUT,
        )
    except (OSError, requests.RequestException):
        return _result(False, f"{name} request failed.")
    if not 200 <= response.status_code < 300:
        return _result(False, f"{name} returned HTTP {response.status_code}.")
    identity = response.headers.get("x-vo-authenticated")
    if not isinstance(identity, str) or not identity.strip():
        return _result(False, f"{name} did not authenticate the certificate.")
    return _result(True, f"{name} is ready.")


def run_checks() -> Dict[str, Any]:
    """Run all readiness checks."""
    config_check, config = _check_config()
    checks = {"config": config_check}
    if config is None:
        message = "Not checked because configuration failed."
        checks.update(
            {
                "server": _result(False, message),
                "certificate": _result(False, message),
                "minoc": _result(False, message),
                "luskan": _result(False, message),
            }
        )
        return {"ok": False, "checks": checks}

    checks["server"] = _check_server(config["server"])
    checks["certificate"] = _check_certificate(config["vospace_certfile"])
    if checks["certificate"]["ok"]:
        for name, url in SERVICE_URLS.items():
            checks[name] = _check_service(name, url, config["vospace_certfile"])
    else:
        message = "Not checked because the certificate failed."
        checks["minoc"] = _result(False, message)
        checks["luskan"] = _result(False, message)
    return {"ok": all(check["ok"] for check in checks.values()), "checks": checks}


def _show_report(report: Dict[str, Any]) -> None:
    """Print readiness results."""
    for name, check in report["checks"].items():
        status = "OK" if check["ok"] else "FAILED"
        click.echo(f"{name}: {status} - {check['message']}")


@click.command(name="doctor", help="Check Datatrail readiness.")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def doctor(ctx: click.Context, output_json: bool) -> None:
    """Check configuration and service readiness."""
    report = run_checks()
    if output_json:
        click.echo(json.dumps(report, indent=2))
    else:
        _show_report(report)
    if not report["ok"]:
        ctx.exit(1)
