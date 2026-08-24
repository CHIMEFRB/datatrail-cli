"""Datatrail List Command."""

import json
import logging
from typing import Any, Dict, Optional

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
@click.option("--json", "output_json", is_flag=True, help="Output as JSON.")
@click.option(
    "--match",
    type=click.STRING,
    default=None,
    help="Comma-separated, case-insensitive terms a larger dataset must all contain.",
)
@click.option(
    "--expand",
    is_flag=True,
    help="Open each matched larger dataset one level and list its children.",
)
@click.pass_context
def list(  # noqa: C901
    ctx: click.Context,
    scope: Optional[str] = None,
    datasets: Optional[str] = None,
    verbose: int = 0,
    quiet: bool = False,
    write: bool = False,
    output_json: bool = False,
    match: Optional[str] = None,
    expand: bool = False,
):
    """List Datatrail Scopes & Datasets.

    Args:
        ctx (click.Context): Click context.
        scope (str): Scope of dataset.
        datasets (str): Name of dataset.
        verbose (int): Verbosity: v=INFO, vv=DEBUG.
        quiet (bool): Only errors shown in logs.
        write (bool): Write the events to file.
        output_json (bool): Output as JSON.
        match (str): Comma-separated terms a larger dataset must all contain.
        expand (bool): Open each matched larger dataset one level.
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
            ctx.exit(1)
            return None
    if match is not None or expand:
        if datasets:
            error_console.print(
                "--match and --expand map larger datasets; "
                "omit the DATASETS argument."
            )
            ctx.exit(1)
            return None
        if expand and match is None and not scope:
            error_console.print(
                "--expand alone would open every dataset in the archive; "
                "give a SCOPE or --match to narrow it."
            )
            ctx.exit(1)
            return None
        discovery = functions.discover_datasets(scope, match, expand, verbose, quiet)
        _display_discovery(discovery, ctx, expand, write, output_json, scope)
        return None
    results = functions.list(scope, datasets, verbose, quiet)

    # Output JSON if requested.
    if output_json:
        print(json.dumps(results, indent=2))
        if "error" in results:
            ctx.exit(1)
        return

    # Display scopes.
    if "scopes" in results.keys():
        table = Table(
            title="Datatrail: Scopes",
            header_style="magenta",
            title_style="bold magenta",
        )
        table.add_column("Scopes")
        matched = set()
        for site in ["chime", "kko", "gbo", "hco"]:
            for s in [_ for _ in results["scopes"] if site in _]:
                table.add_row(s)
                matched.add(s)
            table.add_section()
        other_scopes = [_ for _ in results["scopes"] if _ not in matched]
        for s in other_scopes:
            table.add_row(s)
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
        ctx.exit(1)


def _display_discovery(
    results: Dict[str, Any],
    ctx: click.Context,
    expand: bool,
    write: bool,
    output_json: bool,
    scope: Optional[str],
) -> None:
    """Display the dataset map built by functions.discover_datasets.

    An empty map with unanswered queries exits non-zero: nothing was
    determined. A partial map is shown, with the unanswered queries listed.

    Args:
        results (Dict[str, Any]): Dictionary from functions.discover_datasets.
        ctx (click.Context): Click context.
        expand (bool): Whether children were listed, adding a parent column.
        write (bool): Write the map to file.
        output_json (bool): Output as JSON.
        scope (Optional[str]): Scope walked, None when all were.
    """
    if output_json:
        print(json.dumps(results, indent=2))
        if "error" in results:
            ctx.exit(1)
        if not results["results"] and results["failed"]:
            ctx.exit(1)
        return
    if "error" in results:
        error_console.print(results["error"])
        ctx.exit(1)
        return
    rows = results["results"]
    failed = results["failed"]
    if write:
        with open(f"./dataset_map_{scope if scope else 'all_scopes'}.json", "w") as f:
            json.dump(results, f)
    if rows:
        table = Table(
            title="Datatrail: Dataset Map",
            header_style="magenta",
            title_style="bold magenta",
        )
        table.add_column("Scope")
        table.add_column("Dataset")
        if expand:
            table.add_column("Parent")
        previous = None
        for row in rows:
            if previous is not None and row["scope"] != previous:
                table.add_section()
            previous = row["scope"]
            line = [row["scope"], row["dataset"]]
            if expand:
                line.append(row["parent"] if row["parent"] else "")
            table.add_row(*line)
        with console.pager(styles=False):
            console.print(table)
    elif not failed:
        console.print("No datasets matched.")
    if failed:
        error_console.print("Map is incomplete -- Datatrail did not answer for:")
        for item in failed:
            error_console.print(f"  {item}")
        if not rows:
            ctx.exit(1)
