"""Datatrail Detailed Status Command."""

import logging
import os
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from dtcli.src import functions
from dtcli.utilities import cadcclient

logger = logging.getLogger("ps")


@click.command(name="ps", help="Details of a dataset.")
@click.argument("scope", required=True, type=click.STRING, nargs=1)
@click.argument("dataset", required=True, type=click.STRING, nargs=1)
@click.option("-s", "--show-files", is_flag=True, help="Show file names.")
def ps(scope: str, dataset: str, show_files: bool):
    """Detailed status of a dataset."""
    try:
        files, policies = functions.ps(scope, dataset)
    except Exception as e:
        logger.error(e)
        return None

    # Info table
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
        common_path = os.path.commonpath(minoc_files)
        if not common_path.startswith("data") or not common_path.startswith("/data"):
            common_path = common_path.replace("cadc:CHIMEFRB", "")
        size = cadcclient.size(common_path)
        info_table.add_row("minoc", f"{len(minoc_files)}", f"{size:.2f}")
    else:
        info_table.add_row("minoc", str(0), str(0))

    # Files table
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

    console = Console()
    if show_files:
        with console.pager():
            console.print(file_table)
    else:
        console.print(info_table)
        console.print(policy_table)
