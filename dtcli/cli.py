"""Datatrail Command Line Interface."""

import click
from pkg_resources import get_distribution
from rich import console, pretty

from dtcli import ls, ps, pull

pretty.install()
terminal = console.Console()


@click.group()
def cli():
    """Datatrail Command Line Interface."""
    pass


@cli.command(name="version", help="Show versions.")
def version():
    """Show version."""
    terminal.print(
        "Datatrail Versions",
        style="bold",
    )
    terminal.print(
        f"{get_distribution('datatrail-cli')}",
        style="green",
    )
    terminal.print(
        f"datatrail-server {'0.1.1'}",
        style="green",
    )


cli.add_command(ls.ls)
cli.add_command(ps.ps)
cli.add_command(pull.pull)

if __name__ == "__main__":
    cli()
