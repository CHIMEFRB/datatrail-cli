"""Datatrail List Command."""

import json
import logging
from typing import Optional

import click
from requests.exceptions import ConnectionError
from rich.console import Console
from rich.table import Table

from dtcli.src import functions
from dtcli.utilities.utilities import set_log_level, validate_scope

logger = logging.getLogger("ls")

console = Console()
error_console = Console(stderr=True, style="bold red")


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
@click.option("--write", is_flag=True, help="Write the events to file.")
@click.pass_context
def list(
    ctx: click.Context,
    scope: Optional[str] = None,
    datasets: Optional[str] = None,
    verbose: int = 0,
    quiet: bool = False,
    write: bool = False,
):
    """List Datatrail Scopes & Datasets.

    Args:
        ctx (click.Context): Click context.
        scope (str): Scope of dataset.
        datasets (str): Name of dataset.
        verbose (int): Verbosity: v=INFO, vv=DEBUG.
        quiet (bool): Only errors shown in logs.
        write (bool): Write the events to file.
    """
    # Set logging level.
    set_log_level(logger, verbose, quiet)
    logger.debug("`list` called with:")
    logger.debug(f"scope: {scope} [{type(scope)}]")
    logger.debug(f"datasets: {datasets} [{type(datasets)}]")
    logger.debug(f"verbose: {verbose} [{type(verbose)}]")
    logger.debug(f"quiet: {quiet} [{type(quiet)}]")
    if scope:
        try:
            if not validate_scope(scope):
                error_console.print("Scope does not exist!")
                console.print("Valid scopes are:")
                ctx.invoke(list)
                return None
        except ConnectionError as e:
            error_console.print(e)
            return None
    results = functions.list(scope, datasets, verbose, quiet)

    # Display scopes.
    if "scopes" in results.keys():
        table = Table(
            title="Datatrail: Scopes",
            header_style="magenta",
            title_style="bold magenta",
        )
        table.add_column("Scopes")
        for site in ["chime", "kko", "gbo", "hco"]:
            for s in [_ for _ in results["scopes"] if site in _]:
                table.add_row(s)
            table.add_section()
        console.print(table)

    if "larger_datasets" in results.keys():
        results["larger_datasets"] = sorted(results["larger_datasets"])

        if write:
            with open(f"./larger_datasets_list_{scope}.txt", "w") as file:
                json.dump(results, file)

        table = Table(
            title=f"Datatrail: Larger Datasets {scope}",
            header_style="magenta",
            title_style="bold magenta",
        )
        table.add_column("Larger datasets", justify="center")
        table.add_row("\t".join(results["larger_datasets"]))
        with console.pager(styles=False):
            console.print(table)

    # Display datasets in parent dataset for scope.
    if "datasets" in results.keys():
        results["datasets"] = sorted(results["datasets"], reverse=True)
        if write:
            with open(f"./dataset_list_for_{scope}_{datasets}.txt", "w") as file:
                json.dump(results, file)

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
        error_console.print(results["error"])
