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
@click.argument("scope", required=False)
@click.argument("datasets", nargs=-1, required=False)
def list(scope: str = None, datasets: str = None):
    """List Datatrail Scopes & Datasets."""
    results = functions.list(scope, datasets)

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
        table.add_row("\t".join(results["datasets"]))
        with console.pager(styles=False):
            console.print(table)

    # No contact with server.
    if "error" in results.keys():
        console.print(results["error"], style="red bold")
