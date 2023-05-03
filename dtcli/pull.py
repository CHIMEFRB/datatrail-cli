"""Datatrail Pull Command."""

import click


@click.command(name="pull", help="Download a dataset.")
@click.argument("scope", type=click.STRING, required=True, nargs=1)
@click.argument("dataset", type=click.STRING, required=True, nargs=1)
@click.option(
    "--directory",
    "-d",
    type=click.Path(exists=True),
    help="Directory to pull data to.",
    default=".",
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--force", "-f", is_flag=True, help="No questions asked")
def pull(scope, dataset):
    """Download a dataset."""
    pass
