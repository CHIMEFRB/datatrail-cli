"""Tests for Datatrail CLI."""

from os import cpu_count
from pathlib import Path

import pytest
from click.testing import CliRunner

from dtcli.cli import cli as datatrail


@pytest.fixture
def runner() -> CliRunner:
    """Click CLI runner for testing.

    Returns:
        (CliRunner) -> None:
    """
    return CliRunner()


def test_cli_help(runner: CliRunner) -> None:
    """Test the CLI help page.

    Args:
        runner (CliRunner) -> None: Click runner.
    """
    result = runner.invoke(datatrail)
    expected_response = """Usage: cli [OPTIONS] COMMAND [ARGS]...

  Datatrail Command Line Interface.

Options:
  --help  Show this message and exit.

Commands:
  config     Datatrail CLI Configuration.
  list (ls)  List scopes & datasets
  ps         Details of a dataset.
  pull       Download a dataset.
  version    Show versions.
"""
    assert result.exit_code == 0
    assert result.output == expected_response


def test_cli_config_help(runner: CliRunner) -> None:
    """Test CLI config help page.

    Args:
        runner (CliRunner) -> None: Click runner.
    """
    result = runner.invoke(datatrail, ["config"])
    expected_response = """Usage: cli config [OPTIONS] COMMAND [ARGS]...

  Datatrail CLI Configuration.

Options:
  --help  Show this message and exit.

Commands:
  get        Get a configuration value.
  init       Initialize configuration.
  list (ls)  List all configuration values.
  set        Set a configuration value.
"""
    assert result.exit_code == 0
    assert result.output == expected_response


def test_cli_list_help(runner: CliRunner) -> None:
    """Test CLI list help page.

    Args:
        runner (CliRunner) -> None: Click runner.
    """
    result = runner.invoke(datatrail, ["ls", "--help"])
    expected_response = """Usage: cli list [OPTIONS] [SCOPE] [DATASETS]

  List scopes & datasets

Options:
  -v, --verbose  Verbosity: v=INFO, vv=DEBUG.
  -q, --quiet    Only errors shown in logs.
  --write        Write the events to file.
  --help         Show this message and exit.
"""
    assert result.exit_code == 0
    assert result.output == expected_response


def test_cli_ps_help(runner: CliRunner) -> None:
    """Test CLI ps help page.

    Args:
        runner (CliRunner) -> None: Click runner.
    """
    result = runner.invoke(datatrail, ["ps", "--help"])
    expected_response = """Usage: cli ps [OPTIONS] SCOPE DATASET

  Details of a dataset.

Options:
  -s, --show-files  Show file names.
  --help            Show this message and exit.
"""
    assert result.exit_code == 0
    assert result.output == expected_response


def test_cli_pull_help(runner: CliRunner) -> None:
    """Test CLI pull help page.

    Args:
        runner (CliRunner): Click runner.
    """
    result = runner.invoke(datatrail, ["pull", "--help"])
    expected_response = f"""Usage: cli pull [OPTIONS] SCOPE DATASET

  Download a dataset.

Options:
  -d, --directory DIRECTORY  Directory to pull data to.
  -c, --cores INTEGER RANGE  Number of parallel fetch processes to use.
                             [1<=x<={cpu_count()}]
  -v, --verbose              Verbosity: v=INFO, vv=DEBUG.
  -q, --quiet                Set log level to ERROR.
  -f, --force                Do not prompt for confirmation.
  --help                     Show this message and exit.
"""
    assert result.exit_code == 0
    assert result.output == expected_response


def test_cli_config_init(runner: CliRunner) -> None:
    """Test CLI configuration initialisation.

    Args:
        runner (CliRunner): Click runner.
    """
    result = runner.invoke(datatrail, ["config", "init", "--site", "local"], input="y\n")
    home = Path.home().as_posix()
    assert result.exit_code == 0
    assert (
        f"Datatrail config file {home}/.datatrail/config.yaml created." in result.output
    )


def test_cli_config_list(runner: CliRunner) -> None:
    """Test for CLI config list.

    Args:
        runner (CliRunner): Click runner.
    """
    result = runner.invoke(datatrail, ["config", "ls"])
    home = Path.home().as_posix()
    expected_response = f"""Filename: {home}/.datatrail/config.yaml
{{
    'root_mounts': {{
        'canfar': '/arc/project/chime_frb/',
        'chime': '/',
        'gbo': '/',
        'hco': '/',
        'kko': '/',
        'local': './'
    }},
    'server': 'https://frb.chimenet.ca/datatrail',
    'site': 'local',
    'vospace_certfile': '{home}/.ssl/cadcproxy.pem'
}}
"""
    assert result.exit_code == 0
    assert result.output == expected_response


def test_cli_config_get(runner: CliRunner) -> None:
    """Test for config get.

    Fetches the site configuration.

    Args:
        runner (CliRunner): Click runner.
    """
    result = runner.invoke(datatrail, ["config", "get", "site"])
    assert result.exit_code == 0
    assert "local" in result.output


def test_cli_list_scopes(runner: CliRunner) -> None:
    """Test for CLI list to give scopes.

    Args:
        runner (CliRunner): Click runner.
    """
    result = runner.invoke(datatrail, ["ls"])
    assert result.exit_code == 0
    assert "chime.event.intensity.raw" in result.output


def test_cli_list_larger(runner: CliRunner) -> None:
    """Test for CLI to list larger datasets.

    Args:
        runner (CliRunner): Click runner.
    """
    result = runner.invoke(datatrail, ["ls", "chime.event.baseband.raw"])
    assert result.exit_code == 0
    assert "classified.FRB" in result.output


def test_cli_list_children(runner: CliRunner) -> None:
    """Test for CLI list to show child datasets.

    Args:
        runner (CliRunner): Click runner.
    """
    result = runner.invoke(
        datatrail, ["ls", "chime.event.baseband.raw", "classified.FRB"]
    )
    assert result.exit_code == 0
    assert "289007650" in result.output


def test_cli_ps(runner: CliRunner) -> None:
    """Test for CLI ps command.

    Args:
        runner (CliRunner): Click runner.
    """
    result = runner.invoke(datatrail, ["ps", "chime.event.baseband.raw", "289007650"])
    assert result.exit_code == 0


def test_cli_version(runner: CliRunner) -> None:
    """Test for CLI version.

    Args:
        runner (CliRunner): Click runner.
    """
    result = runner.invoke(datatrail, ["version"])
    assert result.exit_code == 0
    assert "Datatrail Versions" in result.output
