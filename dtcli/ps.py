"""Datatrail Detailed Status Command."""

import click
from chime_frb_api import get_logger
from rich.console import Console
from rich.table import Table

from dtcli.src import functions

logger = get_logger()


@click.command(name="ps", help="Details of a dataset.")
@click.argument("scope", required=True, type=click.STRING, nargs=1)
@click.argument("dataset", required=True, type=click.STRING, nargs=1)
def ps(scope: str, dataset: str):
    """Detailed status of a dataset."""
    try:
        files, policies = functions.ps(scope, dataset)
    except Exception as e:
        logger.error(e)
        return None

    # Files table
    file_table = Table(
        title=f"Datatrail: Files for {dataset} {scope}",
        header_style="magenta",
        title_style="bold magenta",
    )
    file_table.add_column("Storage Element", style="bold")
    file_table.add_column("File Path", style="green", overflow="fold")

    for se in files["file_replica_locations"]:
        for idx, fp in enumerate(files["file_replica_locations"][se]):
            if idx == 0:
                file_table.add_row(se, fp)
            else:
                file_table.add_row("", fp)
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
    console.print(file_table)
    console.print(policy_table)
