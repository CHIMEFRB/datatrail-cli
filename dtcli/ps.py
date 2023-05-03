"""Datatrail Detailed Status Command."""

import click


@click.command(name="ps", help="Details of a dataset.")
@click.argument("dataset", type=click.STRING, required=True, nargs=1)
def ps(dataset):
    """Detailed status of a dataset."""
    pass
