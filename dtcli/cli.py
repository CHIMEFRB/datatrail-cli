"""Datatrail Command Line Interface."""

import click

from dtcli import ls, ps, pull


@click.group()
def cli():
    """Datatrail Command Line Interface."""
    pass


cli.add_command(ls.ls)
cli.add_command(ps.ps)
cli.add_command(pull.pull)

if __name__ == "__main__":
    cli()
