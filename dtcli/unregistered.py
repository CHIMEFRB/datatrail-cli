"""Datatrail Unregistered datasets commands."""

import logging
from collections import defaultdict
from typing import DefaultDict, List, Tuple

import click
from rich.console import Console
from rich.table import Table
from rich.text import Text

from dtcli.src import functions
from dtcli.utilities.utilities import set_log_level

logger = logging.getLogger(__name__)

console = Console()
error_console = Console(stderr=True, style="bold red")

CATEGORY_STYLES = {
    "ATTACH_MISSING": "yellow",
    "CREATE_DUPLICATE": "magenta",
    "POSTGRES": "red",
    "OTHER": "red",
    "STATUS": "cyan",
}


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

    if not results:
        console.print("No unregistered datasets found.")
        return

    total = sum(results.values())

    table = Table(
        title=f"Summary of reasons — {total:,} unregistered datasets",
        header_style="magenta",
        title_style="bold magenta",
        row_styles=["none", "dim"],
    )
    table.add_column("Category")
    table.add_column("Detail")
    table.add_column("Count", justify="right")
    table.add_column("%", justify="right")

    # Group signatures by their category prefix, e.g. "ATTACH_MISSING:...".
    groups: DefaultDict[str, List[Tuple[str, int]]] = defaultdict(list)
    for sig, count in results.items():
        category, _, detail = sig.partition(":")
        groups[category].append((detail, count))

    ordered = sorted(
        groups.items(),
        key=lambda group: sum(count for _, count in group[1]),
        reverse=True,
    )
    for index, (category, reasons) in enumerate(ordered):
        if index:
            table.add_section()
        style = CATEGORY_STYLES.get(category, "white")
        reasons.sort(key=lambda reason: reason[1], reverse=True)
        for row, (detail, count) in enumerate(reasons):
            if category in ("ATTACH_MISSING", "CREATE_DUPLICATE"):
                detail = detail.replace(":", " → ", 1)
            table.add_row(
                Text(category, style=style) if row == 0 else "",
                Text(detail) if detail else "(no reason recorded)",
                f"{count:,}",
                f"{count / total:.1%}",
            )

    console.print(table)
