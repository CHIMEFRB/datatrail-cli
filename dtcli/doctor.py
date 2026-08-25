"""Datatrail readiness checks."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse

import click
import requests
import yaml
from OpenSSL import crypto  # type: ignore

from dtcli.config import CONFIG

REQUEST_TIMEOUT = 10
SERVICE_URLS = {
    "minoc": "https://ws-uv.canfar.net/minoc/capabilities",
    "luskan": "https://ws-uv.canfar.net/luskan/capabilities",
}


def _result(ok: bool, message: str) -> Dict[str, Any]:
    """Create one check result."""
    return {"ok": ok, "message": message}


def _load_config() -> Optional[Dict[str, Any]]:
    """Load the configuration without printing its contents."""
    try:
        with open(CONFIG) as stream:
            config = yaml.safe_load(stream)
    except (OSError, UnicodeError, yaml.YAMLError):
        return None
    return config if isinstance(config, dict) else None


def _check_config() -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
    """Load and validate the configuration."""
    config = _load_config()
    if config is None:
        return _result(False, "Configuration could not be loaded."), None

    server = config.get("server")
    certificate = config.get("vospace_certfile")
    site = config.get("site")
    root_mounts = config.get("root_mounts")
    parsed = urlparse(server) if isinstance(server, str) else None
    valid_server = bool(parsed and parsed.scheme in ("http", "https") and parsed.netloc)
    valid_mount = (
        isinstance(site, str)
        and isinstance(root_mounts, dict)
        and isinstance(root_mounts.get(site), str)
    )
    if not valid_server or not isinstance(certificate, str) or not valid_mount:
        return _result(False, "Configuration is missing required values."), None
    return _result(True, "Configuration is ready."), config


def _check_server(server: str) -> Dict[str, Any]:
    """Check the central server and response shape."""
    try:
        response = requests.get(
            server.rstrip("/") + "/query/dataset/scopes",
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException:
        return _result(False, "Datatrail server request failed.")
    if not 200 <= response.status_code < 300:
        return _result(False, f"Datatrail server returned HTTP {response.status_code}.")
    try:
        scopes = response.json()
    except (requests.JSONDecodeError, ValueError):
        return _result(False, "Datatrail server returned invalid JSON.")
    if not isinstance(scopes, list) or not all(
        isinstance(scope, str) for scope in scopes
    ):
        return _result(False, "Datatrail server returned an invalid scope list.")
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
    except OSError:
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
    except requests.RequestException:
        return _result(False, f"{name} request failed.")
    if not 200 <= response.status_code < 300:
        return _result(False, f"{name} returned HTTP {response.status_code}.")
    if not isinstance(response.headers.get("x-vo-authenticated"), str):
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
