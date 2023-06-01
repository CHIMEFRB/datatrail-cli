"""Datatrail Clear Command."""

import logging
import os

import click
from rich.console import Console
from rich.prompt import Confirm

from dtcli.config import procure
from dtcli.src.functions import clear_dataset_path, find_dataset_common_path
from dtcli.utilities.utilities import validate_scope

logger = logging.getLogger("clear")

console = Console()


@click.command(name="clear", help="Clear a dataset.")
@click.argument("scope", type=click.STRING, required=True, nargs=1)
@click.argument("dataset", type=click.STRING, required=True, nargs=1)
@click.option("-v", "--verbose", count=True, help="Verbosity: v=INFO, vv=DEBUG.")
@click.option("-q", "--quiet", is_flag=True, help="Set log level to ERROR.")
@click.option("--force", "-f", is_flag=True, help="Do not prompt for confirmation.")
def clear(
    scope: str,
    dataset: str,
    verbose: int = 0,
    quiet: bool = False,
    force: bool = False,
) -> None:
    """Clear a dataset.

    Args:
        scope (str): Scope of dataset.
        dataset (str): Name of dataset.
        verbose (int): Verbosity: v=INFO, vv=DUBUG.
        quiet (bool): Minimal logging.
        force (bool): Automatically download files.
    """
    logger.setLevel("WARNING")
    if verbose == 1:
        logger.setLevel("INFO")
    elif verbose > 1:
        logger.setLevel("DEBUG")
    elif quiet:
        logger.setLevel("ERROR")
    logger.debug("`clear` called with:")
    logger.debug(f"scope: {scope} [{type(scope)}]")
    logger.debug(f"dataset: {dataset} [{type(dataset)}]")
    logger.debug(f"verbose: {verbose} [{type(verbose)}]")
    logger.debug(f"quiet: {quiet} [{type(quiet)}]")

    # Load configuration.
    try:
        logger.debug("Loading configuration.")
        config = procure()
        site = config["site"]
        logger.debug(f"Site set to: {site}")
    except Exception:
        logger.exception("Configuration missing!! Run `dtcli config init`.")
        raise click.Abort()

    if not validate_scope(scope):
        raise ValueError("Scope does not exist.")

    # Find number of files in common directory and size.
    console.print(f"\nSearching for files for {dataset} {scope}...\n")
    common_path = find_dataset_common_path(scope, dataset, site, verbose, quiet)
    if not common_path:
        raise click.Abort()
    files = os.listdir(common_path)
    size = sum(os.path.getsize(os.path.join(common_path, f)) for f in files)

    console.print(f"Directory: {common_path}", style="bold")
    console.print(f"Found {len(files)} files.")
    console.print(f"Total size: {size / 1024**3:.2f} GB.\n")

    # Confirm deletion.
    if force:
        is_delete = True
    else:
        is_delete = Confirm.ask("Delete files?")

    # Delete files.
    if is_delete:
        clear_dataset_path(common_path, verbose, quiet)
