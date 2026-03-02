"""Utility functions."""

import json
import logging
from typing import Any, Dict, List, Tuple, Union

import requests
from requests.models import Response
from rich.console import Console

from dtcli.utilities import cadcclient

try:
    from packaging.version import parse
except ImportError:
    from pip._vendor.packaging.version import parse


def set_log_level(logger: logging.Logger, verbose: int = 0, quiet: bool = False) -> None:
    """Set log level."""
    if verbose == 1:
        logger.setLevel("INFO")
    elif verbose > 1:
        logger.setLevel("DEBUG")
    elif quiet:
        logger.setLevel("ERROR")
    else:
        logger.setLevel("WARNING")


def decode_response(response: Response) -> Union[Dict, str]:
    """Decode response.

    Args:
        response (Response): Request response.

    Returns:
        Union[Dict, str]: JSON response or text.
    """
    if response.status_code in [200, 201]:
        return response.json()
    elif response.status_code in [503]:
        raise requests.exceptions.ConnectionError("Service not responding.")
    else:
        return response.text


def validate_request_response(
    request_response: Any,
    dataset: str,
    scope: str,
) -> None:
    """Validate the response of a request.

    Args:
        request_response (Any): response to validate

    Returns:
        None
    """
    if "object has no attribute" in request_response:
        raise Exception(f"Could not find {dataset} {scope} in Datatrail.")


def split(data: List[Any], count: int) -> List[List[Any]]:
    """Split a list into batches.

    Args:
        data (List[Any]): List to split.
        count (int): Number of batches to split into.

    Returns:
        List[List[Any]]: List of batches.
    """
    batch_size = len(data) // count
    remainder = len(data) % count
    batches: List[Any] = []
    idx = 0
    for i in range(count):
        if i < remainder:
            batch = data[idx : idx + batch_size + 1]  # noqa: E203
            idx += batch_size + 1
        else:
            batch = data[idx : idx + batch_size]  # noqa: E203
            idx += batch_size
        if len(batch) > 0:
            batches.append(batch)
    return batches


def validate_scope(scope: str) -> bool:
    """Check if scope is valid.

    Args:
        scope (str): Scope to check.

    Returns:
        bool: True if scope is valid.
    """
    resp = requests.get("https://frb.chimenet.ca/datatrail/query/dataset/scopes")
    scopes = decode_response(resp)
    return scope in scopes


def get_latest_released_version(
    package: str = "datatrail-cli",
    url_pattern: str = "https://pypi.python.org/pypi/{package}/json",
):
    """Get latest released version of a package from pypi.python.org.

    Args:
        package (str): Package name. Defaults to "datatrail-cli".
        url_pattern (str): URL pattern. Defaults to "https://pypi.python.org/pypi/{package}/json".  # noqa: E501

    Returns:
        str: Latest released version.
    """
    req = requests.get(url_pattern.format(package=package))
    version = parse("0")
    if req.status_code == requests.codes.ok:
        j = json.loads(req.text.encode(req.encoding))  # type: ignore
        releases = j.get("releases", [])
        for release in releases:
            ver = parse(release)
            if not ver.is_prerelease:
                version = max(version, ver)
    return version


def cli_is_latest_release() -> bool:
    """Check if CLI is latest release."""
    from importlib.metadata import PackageNotFoundError, version

    try:
        current_version = parse(version("datatrail-cli"))
        return current_version == get_latest_released_version()
    except (ConnectionError, PackageNotFoundError):
        return True


def check_canfar_status(console: Console) -> Tuple[bool, bool]:
    """Checks the status of Luskan and Minoc.

    Args:
        console: Console to print status messages to.

    Returns:
        Tuple[bool, bool]: Status of Minoc and Luskan, respectively.
    """
    # Check Canfar status.
    minoc_up, luskan_up = cadcclient.status()
    if not minoc_up:
        console.print(":warning: Minoc is down!", style="bold yellow")
    if not luskan_up:
        console.print(":warning: Luskan is down!", style="bold yellow")
    if not minoc_up or not luskan_up:
        console.print(
            "See https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/status/ for service availability.",  # noqa: E501
            style="bold yellow",
        )
    return minoc_up, luskan_up
