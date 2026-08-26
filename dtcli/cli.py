"""Datatrail Command Line Interface."""

from importlib.metadata import version as package_version

import click
from click_aliasing import ClickAliasedGroup
from rich import console, pretty

from dtcli import clear, config, ls, ps, pull, scout, unregistered, verify
from dtcli.utilities import utilities

pretty.install()
terminal = console.Console()
terminal_stderr = console.Console(stderr=True)


# Main CLI
@click.group(cls=ClickAliasedGroup)
def cli():
    """Datatrail Command Line Interface."""
    try:
        check_version()
    except Exception:
        pass


@cli.command(name="version", help="Show versions.")
def version():
    """Show version."""
    terminal.print(
        "Datatrail Versions",
        style="bold",
    )
    terminal.print(
        f"datatrail-cli {package_version('datatrail-cli')}",
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
cli.add_command(unregistered.unregistered)
cli.add_command(verify.verify)


def check_version() -> None:
    """Check if CLI is latest release.

    The banner goes to stderr so that stdout stays parseable, e.g. for
    `--json` output piped into another tool.
    """
    if not utilities.cli_is_latest_release():
        current_version = package_version("datatrail-cli")
        latest_version = utilities.get_latest_released_version()
        terminal_stderr.print(
            f"A new release of datatrail-cli is available: {current_version} -> {latest_version}",  # noqa: E501
            style="bold yellow",
        )
        terminal_stderr.print()


if __name__ == "__main__":
    cli()
