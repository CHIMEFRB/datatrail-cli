"""Datatrail Detailed Status Command."""

import logging
import os
from pathlib import Path

import click
from requests.exceptions import SSLError
from rich.console import Console
from rich.table import Table

from dtcli.src import functions
from dtcli.utilities import cadcclient
from dtcli.utilities.utilities import validate_scope

logger = logging.getLogger("ps")

console = Console()
error_console = Console(stderr=True, style="bold red")


@click.command(name="ps", help="Details of a dataset.")
@click.argument("scope", required=True, type=click.STRING, nargs=1)
@click.argument("dataset", required=True, type=click.STRING, nargs=1)
@click.option("-s", "--show-files", is_flag=True, help="Show file names.")
@click.option("-v", "--verbose", count=True, help="Verbosity: v=INFO, vv=DEBUG.")
@click.option("-q", "--quiet", is_flag=True, help="Set log level to ERROR.")
def ps(  # noqa: C901
    scope: str,
    dataset: str,
    show_files: bool,
    verbose: int,
    quiet: bool,
):
    """Detailed status of a dataset.

    Args:
        scope (str): Scope of dataset.
        dataset (str): Name of dataset.
        show_files (bool): Show list of files.
        verbose (int): Verbosity: v=INFO, vv=DUBUG.
        quiet (bool): Set log level to ERROR.

    Returns:
        None
    """
    # Set logging level.
    logger.setLevel("WARNING")
    if verbose == 1:
        logger.setLevel("INFO")
    elif verbose > 1:
        logger.setLevel("DEBUG")
    elif quiet:
        logger.setLevel("ERROR")
    logger.debug("`ps` called with:")
    logger.debug(f"scope: {scope} [{type(scope)}]")
    logger.debug(f"dataset: {dataset} [{type(dataset)}]")
    logger.debug(f"show_files: {show_files} [{type(show_files)}]")
    logger.debug(f"verbose: {verbose} [{type(verbose)}]")
    logger.debug(f"quiet: {quiet} [{type(quiet)}]")

    if not validate_scope(scope):
        raise ValueError("Scope does not exist.")
    try:
        files, policies = functions.ps(scope, dataset, verbose, quiet)
    except Exception as e:
        logger.error(e)
        return None

    # Info table
    logger.debug("Creating info table.")
    info_table = Table(
        title=f"Datatrail: {dataset} {scope} at Minoc",
        header_style="magenta",
        title_style="bold magenta",
    )
    info_table.add_column("Storage Element", style="bold")
    info_table.add_column("Number of Files", style="green")
    info_table.add_column("Size of Files [GB]", style="green")
    if files["file_replica_locations"].get("minoc"):
        minoc_files = files["file_replica_locations"]["minoc"]
        minoc_files = [f.replace("cadc:CHIMEFRB", "") for f in minoc_files]
        # Make sure starts with a /
        common_path = os.path.commonpath(
            ["/" + f if not f.startswith("/") else f for f in minoc_files]
        )
        try:
            size = cadcclient.size(common_path)
        except SSLError as error:
            logger.error(error)
            error_console.print(
                """
No valid CADC certificate found.
Create one using 'cadc-get-cert -u <USERNAME>'.
"""
            )
            return None
        info_table.add_row("minoc", f"{len(minoc_files)}", f"{size:.2f}")
    else:
        info_table.add_row("minoc", str(0), str(0))

    # Files table
    logger.debug("Creating files table.")
    file_table = Table(
        # header_style="magenta",
        title_style="magenta",
    )
    file_table.add_column(
        f"Datatrail: Files for {dataset} {scope}", style="bold magenta"
    )

    for se in files["file_replica_locations"]:
        common_path = os.path.commonpath(files["file_replica_locations"][se])
        names = [
            Path(_).relative_to(common_path) for _ in files["file_replica_locations"][se]
        ]
        for idx, fn in enumerate(names):
            if idx == 0:
                file_table.add_row(f"Storage Element: [magenta]{se}")
                file_table.add_row(f"Common Path: {common_path}/", style="bold green")
                file_table.add_row(f"[green]- {fn}")
                # file_table.add_row(se, common_path, fn)
            else:
                file_table.add_row(f"- {fn}", style="green")
                # file_table.add_row("", "", fn)
        file_table.add_section()

    # Policy table
    logger.debug("Creating policy table.")
    policy_table = Table(
        title=f"Datatrail: Policies for {dataset} {scope}",
        header_style="magenta",
        title_style="bold magenta",
        show_footer=True,
        footer_style="bold red",
    )
    policy_table.add_column("Policy", style="bold", footer="Belongs to")
    policy_table.add_column("Storage Element", footer=policies["belongs_to"][0]["name"])
    policy_table.add_column("Priority")
    policy_table.add_column("Default")
    policy_table.add_column(r"Delete After \[days]")

    rp = policies["replication_policy"]
    for idx, se in enumerate(rp["preferred_storage_elements"]):
        if idx == 0:
            policy_table.add_row(
                "Replication", se, rp["priority"], str(rp["default"]), "-"
            )
        else:
            policy_table.add_row("", se, rp["priority"], str(rp["default"]), "-")
    policy_table.add_section()

    dps = policies["deletion_policy"]
    for idx, dp in enumerate(dps):
        if idx == 0:
            policy_table.add_row(
                "Deletion",
                dp["storage_element"],
                dp["priority"],
                str(dp["default"]),
                str(dp["delete_after_days"]),
            )
        else:
            policy_table.add_row(
                "",
                dp["storage_element"],
                dp["priority"],
                str(dp["default"]),
                str(dp["delete_after_days"]),
            )
    policy_table.add_section()

    if show_files:
        with console.pager():
            logger.debug("Showing file table.")
            console.print(file_table)
    else:
        logger.debug("Showing info table.")
        console.print(info_table)
        logger.debug("Showing policy table.")
        console.print(policy_table)
