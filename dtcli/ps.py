"""Datatrail Detailed Status Command."""

import logging
import os
from pathlib import Path

import click
from requests.exceptions import SSLError
from rich.console import Console
from rich.table import Table

from dtcli.ls import list
from dtcli.src import functions
from dtcli.utilities import cadcclient
from dtcli.utilities.utilities import set_log_level, validate_scope

logger = logging.getLogger("ps")

console = Console()
error_console = Console(stderr=True, style="bold red")


@click.command(name="ps", help="Details of a dataset.")
@click.argument("scope", required=True, type=click.STRING, nargs=1)
@click.argument("dataset", required=True, type=click.STRING, nargs=1)
@click.option("-s", "--show-files", is_flag=True, help="Show file names.")
@click.option("-v", "--verbose", count=True, help="Verbosity: v=INFO, vv=DEBUG.")
@click.option("-q", "--quiet", is_flag=True, help="Set log level to ERROR.")
@click.pass_context
def ps(
    ctx: click.Context,
    scope: str,
    dataset: str,
    show_files: bool,
    verbose: int,
    quiet: bool,
):
    """Detailed status of a dataset.

    Args:
        ctx (click.Context): Click context.
        scope (str): Scope of dataset.
        dataset (str): Name of dataset.
        show_files (bool): Show list of files.
        verbose (int): Verbosity: v=INFO, vv=DUBUG.
        quiet (bool): Set log level to ERROR.

    Returns:
        None
    """
    # Set logging level.
    set_log_level(logger, verbose, quiet)
    logger.debug("`ps` called with:")
    logger.debug(f"scope: {scope} [{type(scope)}]")
    logger.debug(f"dataset: {dataset} [{type(dataset)}]")
    logger.debug(f"show_files: {show_files} [{type(show_files)}]")
    logger.debug(f"verbose: {verbose} [{type(verbose)}]")
    logger.debug(f"quiet: {quiet} [{type(quiet)}]")

    try:
        if not validate_scope(scope):
            error_console.print("Scope does not exist!")
            console.print("Valid scopes are:")
            ctx.invoke(list)
            return None
    except Exception as e:
        error_console.print(e)
        return None

    # Check Canfar status.
    canfar_up = cadcclient.status()
    if not canfar_up:
        error_console.print(
            "Either Minoc is down or certificate is invalid.", style="bold yellow"
        )

    try:
        files, policies = functions.ps(scope, dataset, verbose, quiet)
        if isinstance(files, str) or isinstance(policies, str):
            error_console.print("Error: files = ", files)
            error_console.print("Error: policies = ", policies)
            return None
    except Exception as e:
        error_console.print(e)
        return None

    if show_files and files:
        # Files table
        file_table = create_files_table(dataset, scope, files)

        with console.pager():
            logger.debug("Showing file table.")
            console.print(file_table)
        return None

    if files and ("error" in files.keys()):
        error_console.print(files["error"])
        return None

    # Info table
    elif files:
        if len(files["file_replica_locations"]) < 1:
            unregistered_info = functions.get_unregistered_dataset(dataset, scope)
            if unregistered_info:
                console.print(
                    f":warning: {dataset} is an unregistered dataset :warning:",
                    style="bold yellow",
                    justify="center",
                )
                console.print(
                    f"Parent dataset: [bold red]{unregistered_info['results']['attach_to_dataset']}[/]"  # noqa: E501
                )
                console.print(
                    f"Reason it cannot be registered: [bold red]{unregistered_info['results']['reason']}[/]\n"  # noqa: E501
                )

        else:
            info_table = create_info_table(dataset, scope, files)
            logger.debug("Showing info table.")
            console.print(info_table)

    # Policy table
    if policies:
        policy_table = create_policy_table(dataset, scope, policies)
        logger.debug("Showing policy table.")
        console.print(policy_table)


def create_info_table(dataset: str, scope: str, files: dict):
    """Create info table."""
    logger.debug("Creating info table.")
    info_table = Table(
        title=f"Datatrail: {dataset} {scope} at SEs",
        header_style="magenta",
        title_style="bold magenta",
    )
    info_table.add_column("Storage Element (SE)", style="bold")
    info_table.add_column("Number of Files", style="green")
    info_table.add_column("Size of Files [GB]", style="green")
    for se in files["file_replica_locations"]:
        logger.debug(f"Creating row for: {se}")
        se_files = files["file_replica_locations"][se]
        if se == "minoc":
            se_files = [f.replace("cadc:CHIMEFRB", "") for f in se_files]
            # Make sure starts with a /
            common_path = os.path.commonpath(
                ["/" + f if not f.startswith("/") else f for f in se_files]
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
            info_table.add_row(se, f"{len(se_files)}", f"{size:.2f}")
        else:
            info_table.add_row(se, f"{len(se_files)}", "Not available")
    return info_table


def create_policy_table(dataset: str, scope: str, policies: dict):
    """Create policy table."""
    logger.debug("Creating policy table.")
    policy_table = Table(
        title=f"Datatrail: Policies for {dataset} {scope}",
        header_style="magenta",
        title_style="bold magenta",
        show_footer=True,
        footer_style="bold red",
    )
    if len(policies["belongs_to"]) > 1:
        belongs_to = ", ".join([lgr_ds["name"] for lgr_ds in policies["belongs_to"]])
    elif len(policies["belongs_to"]) == 1:
        belongs_to = policies["belongs_to"][0]["name"]
    else:
        belongs_to = ""
    policy_table.add_column("Policy", style="bold", footer="Belongs to")
    policy_table.add_column("Storage Element", footer=belongs_to)
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
    return policy_table


def create_files_table(dataset: str, scope: str, files: dict):
    """Create files table."""
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
    return file_table
