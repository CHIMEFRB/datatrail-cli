"""Datatrail Pull Command."""

import logging
from os import cpu_count, path

import click
from requests.exceptions import ConnectionError, SSLError
from rich.console import Console
from rich.prompt import Confirm

from dtcli.config import procure
from dtcli.src.functions import find_missing_dataset_files, get_files
from dtcli.utilities import cadcclient
from dtcli.utilities.utilities import set_log_level, validate_scope

logger = logging.getLogger("pull")

console = Console()
error_console = Console(stderr=True, style="bold red")


@click.command(name="pull", help="Download a dataset.")
@click.argument("scope", type=click.STRING, required=True, nargs=1)
@click.argument("dataset", type=click.STRING, required=True, nargs=1)
@click.option(
    "--directory",
    "-d",
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True, writable=True, resolve_path=True
    ),
    default=None,
    help="Directory to pull data to.",
)
@click.option(
    "--cores",
    "-c",
    type=click.IntRange(min=1, max=cpu_count() or 1),
    default=1,
    help="Number of parallel fetch processes to use.",
)
@click.option("-v", "--verbose", count=True, help="Verbosity: v=INFO, vv=DEBUG.")
@click.option("-q", "--quiet", is_flag=True, help="Set log level to ERROR.")
@click.option("--force", "-f", is_flag=True, help="Do not prompt for confirmation.")
@click.pass_context
def pull(  # noqa: C901
    ctx: click.Context,
    scope: str,
    dataset: str,
    directory: str,
    cores: int,
    verbose: int,
    quiet: bool,
    force: bool,
) -> None:
    """Download a dataset.

    Args:
        ctx (click.Context): Click context.
        scope (str): Scope of dataset.
        dataset (str): Name of dataset.
        directory (str): Directory to pull data to.
        cores(int): Number of parallel fetch processes to use.
        verbose (int): Verbosity: v=INFO, vv=DUBUG.
        quiet (bool): Minimal logging.
        force (bool): Automatically download files.
    """
    # Set logging level.
    set_log_level(logger, verbose, quiet)
    logger.debug("`pull` called with:")
    logger.debug(f"scope: {scope} [{type(scope)}]")
    logger.debug(f"dataset: {dataset} [{type(dataset)}]")
    logger.debug(f"verbose: {verbose} [{type(verbose)}]")
    logger.debug(f"quiet: {quiet} [{type(quiet)}]")

    # Load configuration file.
    try:
        logger.debug("Loading config.")
        config = procure()
        site = config["site"]
        logger.debug(f"Site set to: {site}.")
        if directory is None:
            directory = config["root_mounts"][site]
            logger.info(f"No directory, setting to: {directory}.")
    except Exception:
        logger.exception(
            "Configuration Missing!! Run `datatrail config init`.",
        )
        raise click.Abort()

    try:
        if not validate_scope(scope):
            error_console.print("Scope does not exist!")
            console.print("Valid scopes are:")
            ctx.invoke(list)
            return None
    except ConnectionError as e:
        error_console.print(e)
        return None

    # Check Canfar status.
    canfar_up = cadcclient.status()
    if not canfar_up:
        error_console.print(
            "Either Minoc is down or certificate is invalid.", style="bold yellow"
        )

    # Find files missing from localhost.
    console.print(f"\nSearching for files for {dataset} {scope}...\n")
    files = find_missing_dataset_files(scope, dataset, directory, verbose)
    if files.get("error"):
        error_console.print(files["error"])
        return None
    elif len(files["missing"]) == 0 and len(files["existing"]) == 0:
        console.print("No files found at minoc.", style="bold red")
        return None
    files_paths = [f.replace("cadc:CHIMEFRB", "") for f in files["missing"]]
    to_download_size = 0.0
    if len(files_paths) > 0:
        common_path = path.commonpath(["/" + f for f in files_paths])
        try:
            to_download_size = cadcclient.size(common_path)
        except SSLError:
            error_console.print(
                """
No valid CADC certificate found.
Create one using 'cadc-get-cert -u <USERNAME>'.
"""
            )
            return None
    console.print(
        f" - {len(files['existing'])} files found at {site}.",
        style="green",
    )
    console.print(
        f" - {len(files['missing'])} files can be downloaded from minoc.",
        style="yellow",
    )
    console.print(
        f"     - Size to download: {to_download_size:.2f} GB.\n",
        style="yellow",
    )

    # Confirm download.
    if force:
        is_download = True
    elif to_download_size == 0:
        return None
    else:
        is_download = Confirm.ask(
            f"Download {len(files['missing'])} files?",
        )

    # Download missing files.
    if is_download:
        get_files(
            files["missing"],
            site=site,
            directory=directory,
            cores=cores,
            verbose=verbose,
        )
    return None
