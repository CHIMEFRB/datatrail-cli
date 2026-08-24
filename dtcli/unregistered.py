"""Datatrail Unregistered datasets commands."""

import json
import logging
import re
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, DefaultDict, Dict, List, Optional, Tuple

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


@unregistered.command(help="Check whether an event is an unregistered dataset.")
@click.argument("event", required=True, type=click.STRING, nargs=1)
@click.option("-s", "--scope", type=click.STRING, help="Only search within this scope.")
@click.option("-p", "--partial", is_flag=True, help="Match events containing EVENT.")
@click.option("-v", "--verbose", count=True, help="Verbosity: v=INFO, vv=DEBUG.")
@click.option("-q", "--quiet", is_flag=True, help="Only errors shown in logs.")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def search(
    ctx: click.Context,
    event: str,
    scope: Optional[str] = None,
    partial: bool = False,
    verbose: int = 0,
    quiet: bool = False,
    output_json: bool = False,
):
    """Search the unregistered datasets for an event.

    Args:
        ctx (click.Context): Click context.
        event (str): Name of the event to search for.
        scope (str): Only search within this scope.
        partial (bool): Match events containing EVENT.
        verbose (int): Verbosity: v=INFO, vv=DEBUG.
        quiet (bool): Only errors shown in logs.
        output_json (bool): Output as JSON.
    """
    # Set logging level.
    set_log_level(logger, verbose, quiet)
    logger.debug("`search` called with:")
    logger.debug(f"event: {event} [{type(event)}]")
    logger.debug(f"scope: {scope} [{type(scope)}]")
    logger.debug(f"partial: {partial} [{type(partial)}]")
    logger.debug(f"verbose: {verbose} [{type(verbose)}]")
    logger.debug(f"quiet: {quiet} [{type(quiet)}]")

    try:
        results = functions.find_unregistered_datasets(event, scope, partial)
    except Exception as error:
        logger.debug(error)
        if output_json:
            print(json.dumps({"error": str(error)}, indent=2))
            ctx.exit(1)
        error_console.print(error)
        return None

    if output_json:
        print(
            json.dumps(
                {
                    "event": event,
                    "scope": scope,
                    "partial": partial,
                    "unregistered": [result["results"] for result in results],
                },
                indent=2,
            )
        )
        return None

    if not results:
        within = f" in {scope}" if scope else ""
        console.print(f"{event} is not an unregistered dataset{within}.", style="green")
        if not partial:
            console.print("Use --partial to search for events containing this name.")
        return None

    console.print(
        f":warning: {event} is an unregistered dataset :warning:",
        style="bold yellow",
        justify="center",
    )
    console.print(
        f"{len(results):,} record{'s' if len(results) > 1 else ''} found.",
        style="bold magenta",
        justify="center",
    )
    results = sorted(
        results, key=lambda result: result.get("creation") or 0, reverse=True
    )
    for index, result in enumerate(results):
        if index:
            console.print()
        console.print(create_record_table(result))


def create_record_table(result: Dict[str, Any]) -> Table:
    """Create a table detailing a single unregistered record.

    Args:
        result (Dict[str, Any]): Unregistered dataset record.

    Returns:
        Table: Table of the record details.
    """
    record = result["results"]
    creation = result.get("creation")
    recorded = (
        datetime.fromtimestamp(creation, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        if creation
        else "unknown"
    )

    table = Table(box=None, show_header=False, padding=(0, 2, 0, 0))
    table.add_column(style="bold")
    table.add_column(overflow="fold")
    table.add_row("Event", str(record.get("dataset_name")))
    table.add_row("Scope", str(record.get("dataset_scope")))
    table.add_row("Site", str(result.get("site")))
    table.add_row("Parent dataset", str(record.get("attach_to_dataset") or "-"))
    table.add_row("Recorded", recorded)
    table.add_row(
        "Reason",
        Text(
            re.sub(r"\n+", "\n", str(record.get("reason") or "")).strip()
            or "(no reason recorded)",
            style="red",
        ),
    )
    return table
