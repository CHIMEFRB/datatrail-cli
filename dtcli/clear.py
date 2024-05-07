"""Datatrail Clear Command."""

import logging
import os

import click
from requests.exceptions import ConnectionError
from rich.console import Console
from rich.prompt import Confirm

from dtcli.config import procure
from dtcli.src.functions import clear_dataset_path, find_dataset_common_path
from dtcli.utilities.utilities import set_log_level, validate_scope

logger = logging.getLogger("clear")

console = Console()
error_console = Console(stderr=True, style="bold red")


@click.command(
    name="clear",
    help="""Clear a dataset.""",
)
@click.argument("scope", type=click.STRING, required=True, nargs=1)
@click.argument("dataset", type=click.STRING, required=True, nargs=1)
@click.option(
    "--directory",
    "-d",
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True, writable=True, resolve_path=True
    ),
    default=None,
    help="Root directory to use. Default: None, will use the value set in the config.",
)
@click.option(
    "--clear-parents",
    is_flag=True,
    help="Clear all empty parent directories of dataset.",
)
@click.option("-v", "--verbose", count=True, help="Verbosity: v=INFO, vv=DEBUG.")
@click.option("-q", "--quiet", is_flag=True, help="Set log level to ERROR.")
@click.option("--force", "-f", is_flag=True, help="Will not prompt for confirmation.")
@click.pass_context
def clear(
    ctx: click.Context,
    scope: str,
    dataset: str,
    directory: str,
    clear_parents: bool,
    verbose: int = 0,
    quiet: bool = False,
    force: bool = False,
) -> None:
    """Clear a dataset.

    Args:
        ctx (click.Context): Click context.
        scope (str): Scope of dataset.
        dataset (str): Name of dataset.
        directory (str): Directory to clear data from.
        clear_parents (bool): Clear all empty parent directories of dataset.
        verbose (int): Verbosity: v=INFO, vv=DUBUG.
        quiet (bool): Minimal logging.
        force (bool): Automatically download files.
    """
    # Set logging level.
    set_log_level(logger, verbose, quiet)
    logger.debug("`clear` called with:")
    logger.debug(f"scope: {scope} [{type(scope)}]")
    logger.debug(f"dataset: {dataset} [{type(dataset)}]")
    logger.debug(f"directory: {directory} [{type(directory)}]")
    logger.debug(f"clear_parents: {clear_parents} [{type(clear_parents)}]")
    logger.debug(f"verbose: {verbose} [{type(verbose)}]")
    logger.debug(f"quiet: {quiet} [{type(quiet)}]")

    # Load configuration.
    try:
        logger.debug("Loading configuration.")
        config = procure()
        site = config["site"]
        logger.debug(f"Site set to: {site}")
        if directory is None:
            directory = config["root_mounts"][site]
            logger.info(f"No directory, setting to: {directory}")
        elif not directory.endswith("/"):
            directory += "/"
    except Exception:
        logger.exception("Configuration missing!! Run `dtcli config init`.")
        raise click.Abort()

    if site not in ["local", "canfar"]:
        raise RuntimeError("Clear command not permitted at Chime or Outriggers!")

    try:
        if not validate_scope(scope):
            error_console.print("Scope does not exist!")
            console.print("Valid scopes are:")
            ctx.invoke(list)
            return None
    except ConnectionError as error:
        error_console.print(error)
        return None

    # Find number of files in common directory and size.
    console.print(f"\nSearching for files for {dataset} {scope}...\n")
    common_path = find_dataset_common_path(scope, dataset, site, verbose, quiet)
    if common_path:
        common_path = (directory + common_path).replace("//", "/")
    if not common_path:
        console.print("Either dataset not found on Datatrail or no config found.")
        raise click.Abort()
    elif not os.path.exists(common_path):
        console.print(
            f"Path {common_path} does not exist. No files to clear.", style="bold red"
        )
        raise click.Abort()
    files = os.listdir(common_path)
    size = sum(os.path.getsize(os.path.join(common_path, f)) for f in files)

    console.print(f"Directory: {common_path}", style="bold")
    console.print(f" - Found {len(files)} files.")
    console.print(f" - Total size: {size / 1024**3:.2f} GB.\n")

    # Confirm deletion.
    if force:
        is_delete = True
    else:
        message = (
            "⚠️  Delete files and empty parent directories?"
            if clear_parents
            else "⚠️  Delete files?"
        )
        is_delete = Confirm.ask(message)

    # Delete files.
    if is_delete:
        clear_dataset_path(common_path, clear_parents, verbose, quiet)
    else:
        console.print("Roger roger, no files deleted.")
