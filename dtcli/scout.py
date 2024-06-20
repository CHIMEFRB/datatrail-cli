"""Datatrail Scout Command."""

import logging
from typing import List

import click
import requests
from cadcutils.exceptions import BadRequestException
from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table

from dtcli.config import procure
from dtcli.ls import list as ls
from dtcli.utilities import cadcclient
from dtcli.utilities.utilities import set_log_level, validate_scope

logger = logging.getLogger("scout")

console = Console()
error_console = Console(stderr=True, style="bold red")


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
            if not all([validate_scope(scope) for scope in scopes]):
                error_console.print("A scope is invalid.")
                console.print("Valid scopes are:")
                ctx.invoke(ls)
                return None
        except Exception as e:
            error_console.print(e)
            return None

    # Load configuration.
    try:
        config = procure()
        server = config["server"]
        logger.debug("Configuration loaded successfully.")
    except Exception:
        logger.error(
            "No configuration file found. Create one with `datatrail config init`."
        )
        return {"error": "No config. Create one with `datatrail config init`."}

    # Check Canfar status.
    canfar_up = cadcclient.status()
    if not canfar_up:
        error_console.print(
            "Either Minoc is down or certificate is invalid.", style="bold yellow"
        )

    # Scout dataset.
    endpoint = (
        f"/query/dataset/scout?name={dataset}"
        if not scopes
        else f"/query/dataset/scout?name={dataset}&{'&'.join([f'scopes={s}' for s in scopes])}"  # noqa: E501
    )
    url = server + endpoint
    logger.debug(f"URL: {url}")
    response = requests.get(url)
    try:
        data = response.json()
        logger.debug(f"Data: {data}")
    except requests.JSONDecodeError:
        if "Response Timeout" in response.text:
            error_console.print("Error: Datatrail server timed out.")
            return None
        else:
            error_console.print(f"Error: {response.text}")
            return None

    if "error" in data.keys():
        error_console.print(data["error"])
        return None

    scopes_with_minoc_discrepancy: List[str] = []
    for scope in data.keys():
        basepath = data.get(scope).get("basepath")
        query = f"select count(*) from inventory.Artifact where uri like 'cadc:CHIMEFRB/{basepath}%'"  # noqa: E501
        try:
            count, _ = cadcclient.query(query)
            count = int(count[0])
        except BadRequestException as error:
            error_console.print("Query failed.")
            error_console.print(error)
            return None
        except Exception as error:
            error_console.print("Query failed.")
            error_console.print(error)
            return None
        data[scope]["observed"]["minoc"] = count

        keys_missing_in_observed = list(
            set(data[scope]["expected"].keys()) - set(data[scope]["observed"].keys())
        )
        keys_missing_in_expected = list(
            set(data[scope]["observed"].keys()) - set(data[scope]["expected"].keys())
        )

        for key in keys_missing_in_observed:
            data[scope]["observed"][key] = 0

        for key in keys_missing_in_expected:
            data[scope]["expected"][key] = 0

        if data[scope]["observed"]["minoc"] > data[scope]["expected"]["minoc"]:
            scopes_with_minoc_discrepancy.append(scope)

    show_scout_results(dataset, data)

    if scopes_with_minoc_discrepancy:
        error_console.print("Scopes with minoc discrepancy:")
    for scope in scopes_with_minoc_discrepancy:
        error_console.print(f" - {scope}")
        ifHeal = Confirm.ask("\nWould you like to attempt to heal this discrepancy?")
        if ifHeal:
            basepath = data.get(scope).get("basepath")
            minoc_md5s = cadcclient.dataset_md5s(basepath)
            # console.print(minoc_md5s)
            url = (
                server
                + "/commit/dataset/scout/sync"
                + f"?name={dataset}&scope={scope}&replicate_to=minoc"
            )
            response = requests.post(url, json=minoc_md5s)
            if response.status_code == 200:
                console.print(f"{scope} - Healing successful.")
            else:
                error_console.print(f"{scope} - Healing failed.")


def show_scout_results(dataset: str, data: dict):
    """Create and display a table with scout results.

    Args:
        dataset: Name of dataset.
        data: Data to display.
    """
    # Display results.
    scopes = list(data.keys())
    storage_elements = list(data[scopes[0]]["observed"].keys())
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
            row.append(str(data[scope]["observed"][se]))
        table.add_row(*row, style="blue")

        # Expected
        row = [scope]
        for se in storage_elements:
            row.append(str(data[scope]["expected"][se]))
        table.add_row(*row, style="yellow", end_section=True)

    console.print(table)
    console.print("Legend: [blue]Observed[/blue], [yellow]Expected[/yellow]")
    console.print(
        "NOTE: In the case where more files are expected at a site other than \
minoc, that this may be due to the file type filtering when querying each site. This \
is a known limitation of the current implementation.",
    )
    console.print()
