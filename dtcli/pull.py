"""Datatrail Pull Command."""

import click
from chime_frb_api import get_logger
from rich.console import Console
from rich.prompt import Confirm

from dtcli.config import procure
from dtcli.src.functions import find_missing_dataset_files, get_files

logger = get_logger()


@click.command(name="pull", help="Download a dataset.")
@click.argument("scope", type=click.STRING, required=True, nargs=1)
@click.argument("dataset", type=click.STRING, required=True, nargs=1)
@click.option(
    "--directory",
    "-d",
    type=click.Path(exists=True),
    help="Directory to pull data to.",
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output.")
@click.option("--force", "-f", is_flag=True, help="No questions asked.")
def pull(scope, dataset, directory, verbose, force):
    """Download a dataset."""
    try:
        config = procure()
        SITE = config["site"]
    except Exception:
        logger.error(
            "No configuration file found. Create one with `datatrail config init`.",
        )
        return None
    console = Console()
    console.print(f"Searching for files for {dataset} {scope}...")
    files = find_missing_dataset_files(scope, dataset)
    console.print(
        f"\t- {len(files['existing'])} files found at {SITE}.",
    )
    console.print(
        f"\t- {len(files['missing'])} files can be downloaded from minoc.\n",
    )
    if force:
        is_download = True
    else:
        is_download = Confirm.ask(
            f"Download {len(files['missing'])} files?",
        )

    if is_download:
        obtained = get_files(files["missing"], directory)
        console.print(obtained)
