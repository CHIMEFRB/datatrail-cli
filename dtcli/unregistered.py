"""Datatrail Unregistered datasets commands."""

import logging

import click
from rich.console import Console
from rich.table import Table

from dtcli.src import functions
from dtcli.utilities.utilities import set_log_level

logger = logging.getLogger(__name__)

console = Console()
error_console = Console(stderr=True, style="bold red")


@click.group(help="Commands related to unregistered datasets.")
def unregistered():
    """Group of commands related to unregistered datasets."""
    pass


@unregistered.command(help="Summarise the reasons for unregistered datasets.")
@click.option("-v", "--verbose", count=True, help="Verbosity: v=INFO, vv=DEBUG.")
@click.option("-q", "--quiet", is_flag=True, help="Only errors shown in logs.")
@click.pass_context
def summary(
    ctx: click.Context,
    verbose: int = 0,
    quiet: bool = False,
):
    """Show a summary of the unregistered datasets.

    Args:
        ctx (click.Context): Click context.
        verbose (int): Verbosity: v=INFO, vv=DEBUG.
        quiet (bool): Only errors shown in logs.
    """
    # Set logging level.
    set_log_level(logger, verbose, quiet)
    logger.debug("`summary` called with:")
    logger.debug(f"verbose: {verbose} [{type(verbose)}]")
    logger.debug(f"quiet: {quiet} [{type(quiet)}]")

    results = functions.summarise_unregistered_datasets()

    table = Table(
        title="Summary of reasons", header_style="magenta", title_style="bold magenta"
    )
    table.add_column("Reason")
    table.add_column("Number of Datasets")

    for key, value in results.items():
        table.add_row(key, str(value))

    console.print(table)
