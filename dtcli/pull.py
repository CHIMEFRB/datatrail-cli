"""Datatrail Pull Command."""

from os import cpu_count, path

import click
from chime_frb_api import get_logger
from rich.console import Console
from rich.prompt import Confirm

from dtcli.config import procure
from dtcli.src.functions import find_missing_dataset_files, get_files
from dtcli.utilities.cadcclient import size

logger = get_logger()
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
@click.option("--verbose", "-v", is_flag=True, help="Verbose output.")
@click.option("--force", "-f", is_flag=True, help="Do not prompt for confirmation.")
def pull(
    scope: str, dataset: str, directory: str, cores: int, verbose: bool, force: bool
) -> None:
    """Download a dataset.

    Args:
        scope (str): Scope of dataset.
        dataset (str): Name of dataset.
        directory (str): Directory to pull data to.
        verbose (bool): Verbosity.
        force (bool): Automatically download files.
        cores(int): Number of parallel fetch processes to use.
    """
    # Load configuration file.
    try:
        config = procure()
        site = config["site"]
        if directory is None:
            directory = config["root_mounts"][site]
    except Exception:
        logger.exception(
            "Configuration Missing!! Run `datatrail config init`.",
        )
        raise click.Abort()

    # Find files missing from localhost.
    console.print(f"Searching for files for {dataset} {scope}...")
    files = find_missing_dataset_files(scope, dataset)
    to_download_size = size(path.commonpath(files["missing"]))
    console.print(
        f"\t- {len(files['existing'])} files found at {site}.",
    )
    console.print(
        f"\t- {len(files['missing'])} files can be downloaded from minoc.",
    )
    console.print(f"\t\t- Size to download: {to_download_size:.2f} GB.\n")

    # Confirm download.
    if force:
        is_download = True
    else:
        is_download = Confirm.ask(
            f"Download {len(files['missing'])} files?",
        )

    # Download missing files.
    if is_download:
        obtained = get_files(
            files["missing"], site=site, directory=directory, cores=cores
        )
        console.print(obtained)
