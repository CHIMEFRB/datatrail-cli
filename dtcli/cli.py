"""Datatrail Command Line Interface."""

import click
from click_aliasing import ClickAliasedGroup
from pkg_resources import get_distribution
from rich import console, pretty

from dtcli import config, ls, ps, pull

pretty.install()
terminal = console.Console()


# Main CLI
@click.group(cls=ClickAliasedGroup)
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


cli.add_command(ls.list, aliases=["ls"])
cli.add_command(ps.ps)
cli.add_command(pull.pull)
cli.add_command(config.config)

if __name__ == "__main__":
    cli()
