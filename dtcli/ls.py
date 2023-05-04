"""Datatrail List Command."""

import click
from chime_frb_api import get_logger
from rich.console import Console
from rich.table import Table

# from dtcli.src import functions

logger = get_logger()


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
        console = Console()
        console.print(table)

    # Display datasets in scope.
    if "datasets" in results.keys():
        pass

    # No contact with server.
    if "error" in results.keys():
        logger.error(results["error"])
