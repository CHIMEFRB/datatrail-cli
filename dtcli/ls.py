"""Datatrail List Command."""

from typing import Optional

import click
from chime_frb_api import get_logger
from rich.console import Console
from rich.table import Table

from dtcli.src import functions

logger = get_logger()

console = Console()


@click.command(help="List scopes & datasets")
@click.argument(
    "scope",
    type=click.STRING,
    nargs=1,
    required=False,
)
@click.argument(
    "datasets",
    type=click.STRING,
    nargs=1,
    required=False,
)
@click.option("-v", "--verbose", count=True, help="Verbosity: v=INFO, vv=DEBUG.")
@click.option("-q", "--quiet", is_flag=True, help="Only errors shown in logs.")
def list(
    scope: Optional[str] = None,
    datasets: Optional[str] = None,
    verbose: int = 0,
    quiet: bool = False,
):
    """List Datatrail Scopes & Datasets."""
    logger.setLevel("WARNING")
    if verbose == 1:
        logger.setLevel("INFO")
    elif verbose > 1:
        logger.setLevel("DEBUG")
    elif quiet:
        logger.setLevel("ERROR")
    logger.debug("`list` called with:")
    logger.debug(f"scope: {scope} [{type(scope)}]")
    logger.debug(f"datasets: {datasets} [{type(datasets)}]")
    logger.debug(f"verbose: {verbose} [{type(verbose)}]")
    logger.debug(f"quiet: {quiet} [{type(quiet)}]")
    results = functions.list(scope, datasets, verbose, quiet)

    # Display scopes.
    if "scopes" in results.keys():
        table = Table(
            title="Datatrail: Scopes",
            header_style="magenta",
            title_style="bold magenta",
        )
        table.add_column("Scopes")
        for s in results["scopes"]:
            table.add_row(s)
        console.print(table)

    # Display datasets in scope.
    if "datasets" in results.keys():
        table = Table(
            title=f"Datatrail: Child Datasets {datasets} {scope}",
            header_style="magenta",
            title_style="bold magenta",
        )
        table.add_column("Datasets", justify="center")
        # for d in results["datasets"]:
        # table.add_row(d)
        table.add_row("\t".join(results["datasets"]))
        with console.pager(styles=False):
            console.print(table)
        # console.print(results["datasets"])

    # No contact with server.
    if "error" in results.keys():
        console.print(results["error"], style="red bold")
