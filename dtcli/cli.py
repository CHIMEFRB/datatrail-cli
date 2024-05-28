"""Datatrail Command Line Interface."""

import click
from click_aliasing import ClickAliasedGroup
from pkg_resources import get_distribution
from rich import console, pretty

from dtcli import clear, config, ls, ps, pull, scout
from dtcli.utilities import utilities

pretty.install()
terminal = console.Console()


# Main CLI
@click.group(cls=ClickAliasedGroup)
def cli():
    """Datatrail Command Line Interface."""
    check_version()


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


cli.add_command(clear.clear)
cli.add_command(config.config)
cli.add_command(ls.list, aliases=["ls"])
cli.add_command(ps.ps)
cli.add_command(pull.pull)
cli.add_command(scout.scout)


def check_version() -> None:
    """Check if CLI is latest release."""
    if not utilities.cli_is_latest_release():
        current_version = get_distribution("datatrail-cli").version
        latest_version = utilities.get_latest_released_version()
        terminal.print(
            f"A new release of datatrail-cli is available: {current_version} → {latest_version}",  # noqa: E501
            style="bold yellow",
        )
        terminal.print()


if __name__ == "__main__":
    cli()
