"""Datatrail Pull Command."""

import logging
from os import cpu_count, path

import click
from rich.console import Console
from rich.prompt import Confirm

from dtcli.config import procure
from dtcli.src.functions import find_missing_dataset_files, get_files
from dtcli.utilities.cadcclient import size

logger = logging.getLogger("pull")

console = Console()


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
def pull(
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
        scope (str): Scope of dataset.
        dataset (str): Name of dataset.
        directory (str): Directory to pull data to.
        cores(int): Number of parallel fetch processes to use.
        verbose (int): Verbosity: v=INFO, vv=DUBUG.
        quiet (bool): Minimal logging.
        force (bool): Automatically download files.
    """
    # Set logging level.
    logger.setLevel("WARNING")
    if verbose == 1:
        logger.setLevel("INFO")
    elif verbose > 1:
        logger.setLevel("DEBUG")
    elif quiet:
        logger.setLevel("ERROR")
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

    # Find files missing from localhost.
    console.print(f"\nSearching for files for {dataset} {scope}...\n")
    files = find_missing_dataset_files(scope, dataset)
    common_path = path.commonpath(files["missing"])
    if common_path.startswith("cadc:CHIMEFRB"):
        common_path = common_path.replace("cadc:CHIMEFRB", "")
    to_download_size = size(common_path)
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
    else:
        is_download = Confirm.ask(
            f"Download {len(files['missing'])} files?",
        )

    # Download missing files.
    if is_download:
        get_files(files["missing"], site=site, directory=directory, cores=cores)
    return None
