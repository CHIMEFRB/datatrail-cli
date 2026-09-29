"""Datatrail Scout Command."""

import logging
import re
from pathlib import PurePosixPath
from typing import Any, Dict, List, Optional

import click
import requests
from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table

from dtcli.config import procure
from dtcli.ls import list as ls
from dtcli.utilities import cadcclient
from dtcli.utilities.utilities import (
    REQUEST_TIMEOUT,
    check_canfar_status,
    set_log_level,
    validate_scope,
)

logger = logging.getLogger("scout")

console = Console()
error_console = Console(stderr=True, style="bold red")

# Remote roots used by the Datatrail server's scout proxy. These are independent
# of the client's local root_mounts configuration.
SCOUT_ROOT_MOUNTS = {
    "chime": "/",
    "baseband_buffer": "/data/baseband_buffer/",
    "kko": "/",
    "gbo": "/",
    "hco": "/",
}


@click.command(name="scout", help="Scout a dataset.")
@click.argument("scopes", required=False, type=click.STRING, nargs=-1)
@click.argument("dataset", required=True, type=click.STRING, nargs=1)
@click.option("-v", "--verbose", count=True, help="Verbosity: v=INFO, vv=DEBUG.")
@click.option("-q", "--quiet", is_flag=True, help="Set log level to ERROR.")
@click.pass_context
def scout(  # noqa: C901
    ctx: click.Context,
    scopes: List[str],
    dataset: str,
    verbose: int,
    quiet: bool,
):
    """Scout a dataset.

    Args:
        ctx (click.Context): Click context.
        scopes (List[str]): Scopes of dataset.
        dataset (str): Name of dataset.
        verbose (int): Verbosity: v=INFO, vv=DUBUG.
        quiet (bool): Set log level to ERROR.

    Returns:
        None
    """
    # Set logging level.
    set_log_level(logger, verbose, quiet)
    logger.debug("`scout` called with:")
    logger.debug(f"scopes: {scopes} [{type(scopes)}]")
    logger.debug(f"dataset: {dataset} [{type(dataset)}]")
    logger.debug(f"verbose: {verbose} [{type(verbose)}]")
    logger.debug(f"quiet: {quiet} [{type(quiet)}]")

    # Check if scopes are valid.
    if scopes:
        logger.debug(f"Scopes limited to: {list(scopes)}")
        try:
            valid_scopes = all(validate_scope(scope) for scope in scopes)
        except Exception:
            error_console.print("Unable to validate scopes.")
            ctx.exit(1)
        if not valid_scopes:
            error_console.print("A scope is invalid.")
            console.print("Valid scopes are:")
            ctx.invoke(ls)
            ctx.exit(1)

    # Load configuration.
    try:
        config = procure()
        server = config["server"]
        logger.debug("Configuration loaded successfully.")
    except Exception:
        logger.error(
            "No configuration file found. Create one with `datatrail config init`."
        )
        ctx.exit(1)

    # Check Canfar status.
    check_canfar_status(error_console)

    # Scout dataset.
    url = server.rstrip("/") + "/query/dataset/scout"
    params: Dict[str, Any] = {"name": dataset}
    if scopes:
        params["scopes"] = scopes
    logger.debug(f"URL: {url}")
    try:
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.Timeout:
        error_console.print("Error: Datatrail server timed out.")
        ctx.exit(1)
    except requests.RequestException:
        error_console.print("Error: Datatrail scout request failed.")
        ctx.exit(1)
    if not 200 <= response.status_code < 300:
        error_console.print(
            f"Error: Datatrail server returned HTTP {response.status_code}."
        )
        ctx.exit(1)
    try:
        data = response.json()
        logger.debug(f"Data: {data}")
    except ValueError:
        error_console.print("Error: Datatrail server returned invalid JSON.")
        ctx.exit(1)
    if not _valid_scout_data(data):
        error_console.print("Error: Datatrail returned no valid scout results.")
        ctx.exit(1)

    file_discrepancies: List[List] = []
    failed = False

    for scope in data:
        basepath = data[scope]["basepath"].replace("'", "''")
        query = f"select count(*) from inventory.Artifact where uri like 'cadc:CHIMEFRB/{basepath}%'"  # noqa: E501
        try:
            count = int(cadcclient.query(query)[0][0])
            if count < 0:
                raise ValueError("Invalid file count.")
        except Exception:
            error_console.print(f"{scope} - Minoc count query failed.")
            count = -1
            failed = True
        data[scope]["observed"]["minoc"] = count
        storage_elements = dict.fromkeys(
            [*data[scope]["observed"], *data[scope]["expected"]]
        )
        for se in storage_elements:
            data[scope]["observed"].setdefault(se, 0)
            data[scope]["expected"].setdefault(se, 0)
            if data[scope]["observed"][se] > data[scope]["expected"][se]:
                file_discrepancies.append([scope, se])

    show_scout_results(dataset, data)

    if file_discrepancies:
        error_console.print("File discrepancies:")
    for scope, se in file_discrepancies:
        error_console.print(f" - {se}: {scope}")
        if Confirm.ask("\nWould you like to attempt to heal this discrepancy?"):
            if not _heal(server, dataset, scope, se, data[scope]):
                failed = True
    if failed:
        ctx.exit(1)


def _valid_scout_data(data: Any) -> bool:
    """Require the report fields used to display and select repairs."""
    if not isinstance(data, dict) or not data or "error" in data:
        return False
    for scope, info in data.items():
        if not isinstance(scope, str) or not scope or not isinstance(info, dict):
            return False
        if not isinstance(info.get("basepath"), str) or not info["basepath"]:
            return False
        if not isinstance(info.get("filetype"), str):
            return False
        for field in ("observed", "expected"):
            counts = info.get(field)
            if not isinstance(counts, dict) or not all(
                isinstance(site, str)
                and site
                and isinstance(count, int)
                and not isinstance(count, bool)
                and count >= (0 if field == "expected" else -1)
                for site, count in counts.items()
            ):
                return False
    return True


def _validated_checksums(data: Any) -> Optional[Dict[str, str]]:
    """Accept filename-to-MD5 mappings and normalize the optional MD5 prefix."""
    if not isinstance(data, dict) or not data or "error" in data:
        return None
    checksums = {}
    for filename, value in data.items():
        if not isinstance(filename, str) or not filename.strip():
            return None
        if not isinstance(value, str):
            return None
        checksum = value.strip().lower()
        if checksum.startswith("md5:"):
            checksum = checksum[4:]
        if re.fullmatch(r"[0-9a-f]{32}", checksum) is None:
            return None
        checksums[filename] = checksum
    return checksums


def _site_checksums(
    checksums: Dict[str, str], site: str, basepath: str
) -> Optional[Dict[str, str]]:
    """Convert scout filenames to the dataset-relative names used by sync."""
    if site not in SCOUT_ROOT_MOUNTS:
        return None
    root = PurePosixPath(SCOUT_ROOT_MOUNTS[site])
    base = PurePosixPath(basepath)
    if base.is_absolute() or ".." in base.parts:
        return None
    normalized = {}
    for filename, checksum in checksums.items():
        path = PurePosixPath(filename)
        if ".." in path.parts:
            return None
        try:
            relative = path.relative_to(root) if path.is_absolute() else path
            suffix = relative.relative_to(base)
        except ValueError:
            return None
        name = relative.as_posix()
        if not suffix.parts or name in normalized:
            return None
        normalized[name] = checksum
    return normalized


def _heal(server: str, dataset: str, scope: str, site: str, info: Dict) -> bool:
    """Fetch validated checksums and submit one explicitly confirmed repair."""
    try:
        if site == "minoc":
            data = cadcclient.dataset_md5s(info["basepath"])
        else:
            response = requests.get(
                server.rstrip("/") + "/query/dataset/scout/md5sums",
                params={
                    "basepath": info["basepath"],
                    "site": site,
                    "filetype": info["filetype"],
                },
                timeout=REQUEST_TIMEOUT,
            )
            if not 200 <= response.status_code < 300:
                raise ValueError("Checksum request failed.")
            data = response.json()
    except Exception:
        error_console.print(f"{scope} ({site}) - Checksum query failed; skipping.")
        return False
    checksums = _validated_checksums(data)
    if checksums is not None and site != "minoc":
        checksums = _site_checksums(checksums, site, info["basepath"])
    if checksums is None:
        error_console.print(f"{scope} ({site}) - Invalid checksum response; skipping.")
        return False
    try:
        response = requests.post(
            server.rstrip("/") + "/commit/dataset/scout/sync",
            params={"name": dataset, "scope": scope, "replicate_to": site},
            json=checksums,
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException:
        error_console.print(f"{scope} ({site}) - Healing failed.")
        return False
    if not 200 <= response.status_code < 300:
        error_console.print(f"{scope} ({site}) - Healing failed.")
        return False
    console.print(f"{scope} ({site}) - Healing successful.")
    return True


def show_scout_results(dataset: str, data: dict):
    """Create and display a table with scout results.

    Args:
        dataset: Name of dataset.
        data: Data to display.
    """
    # Display results.
    scopes = list(data.keys())
    storage_elements = dict.fromkeys(
        site for info in data.values() for site in [*info["observed"], *info["expected"]]
    )
    table = Table(
        title=f"Scout Results for {dataset}",
        header_style="magenta",
        title_style="bold magenta",
    )
    table.add_column("Scope", style="bold")
    for se in storage_elements:
        table.add_column(se, style="bold")

    for scope in scopes:
        # Observed
        row = [scope]
        for se in storage_elements:
            row.append(str(data[scope]["observed"].get(se, 0)))
        table.add_row(*row, style="blue")

        # Expected
        row = [scope]
        for se in storage_elements:
            row.append(str(data[scope]["expected"].get(se, 0)))
        table.add_row(*row, style="yellow", end_section=True)

    console.print(table)
    console.print("Legend: [blue]Observed[/blue], [yellow]Expected[/yellow]")
    console.print(
        "NOTE: In the case where more files are expected at a site other than \
minoc, that this may be due to the file type filtering when querying each site. This \
is a known limitation of the current implementation.",
    )
    console.print()
