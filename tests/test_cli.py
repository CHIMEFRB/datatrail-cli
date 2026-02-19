"""Tests for Datatrail CLI."""

import shutil
from os import cpu_count
from pathlib import Path

import pytest
from click.testing import CliRunner

from dtcli.cli import cli as datatrail


@pytest.fixture(scope="module")
def directory():
    """Create a temporary directory.

    Yields:
        directory (Path): Path to temporary directory.
    """
    directory = Path("tmp_test")
    directory.mkdir(exist_ok=True)
    yield directory
    shutil.rmtree(directory)


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
    result = runner.invoke(datatrail, "--help")
    expected_response = """Usage: cli [OPTIONS] COMMAND [ARGS]...

  Datatrail Command Line Interface.
"""
    assert result.exit_code == 0
    assert expected_response in result.output


def test_cli_config_help(runner: CliRunner) -> None:
    """Test CLI config help page.

    Args:
        runner (CliRunner) -> None: Click runner.
    """
    result = runner.invoke(datatrail, ["config", "--help"])
    expected_response = """Usage: cli config [OPTIONS] COMMAND [ARGS]...

  Datatrail CLI Configuration.

  For initialising and modifying the Datatrail CLI configuration file.

Options:
  --help  Show this message and exit.

Commands:
  get        Get a configuration value.
  init       Initialise configuration.
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
  -v, --verbose     Verbosity: v=INFO, vv=DEBUG.
  -q, --quiet       Set log level to ERROR.
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
  -s, --specific FILE        Specific files to pull
  -c, --cores INTEGER RANGE  Number of parallel fetch processes to use.
                             [1<=x<={cpu_count()}]
  -v, --verbose              Verbosity: v=INFO, vv=DEBUG.
  -q, --quiet                Set log level to ERROR.
  -f, --force                Do not prompt for confirmation.
  --help                     Show this message and exit.
"""
    assert result.exit_code == 0
    assert result.output == expected_response


def test_cli_scout_help(runner: CliRunner) -> None:
    """Test CLI scout help page.
    Args:
        runner (CliRunner): Click runner.
    """
    result = runner.invoke(datatrail, ["scout", "--help"])
    expected_response = """Usage: cli scout [OPTIONS] [SCOPES]... DATASET

  Scout a dataset.

Options:
  -v, --verbose  Verbosity: v=INFO, vv=DEBUG.
  -q, --quiet    Set log level to ERROR.
  --help         Show this message and exit.
"""
    assert result.exit_code == 0
    assert result.output == expected_response


def test_cli_clear_help(runner: CliRunner) -> None:
    """Test CLI clear help page.

    Args:
        runner (CliRunner): Click runner.
    """
    result = runner.invoke(datatrail, ["clear", "--help"])
    expected_response = """Usage: cli clear [OPTIONS] SCOPE DATASET

  Clear a dataset.

Options:
  -d, --directory DIRECTORY  Root directory to use. Default: None, will use the
                             value set in the config.
  --clear-parents            Clear all empty parent directories of dataset.
  -v, --verbose              Verbosity: v=INFO, vv=DEBUG.
  -q, --quiet                Set log level to ERROR.
  -f, --force                Will not prompt for confirmation.
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
        'canfar': '/arc/projects/chime_frb/',
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


def test_cli_config_set(runner: CliRunner) -> None:
    """Test for config set.

    Sets the site config to chime.

    Args:
        runner (CliRunner): Click runner.
    """
    runner.invoke(datatrail, ["config", "set", "site", "chime"])
    result = runner.invoke(datatrail, ["config", "ls"])
    home = Path.home().as_posix()
    expected_response = f"""Filename: {home}/.datatrail/config.yaml
{{
    'root_mounts': {{
        'canfar': '/arc/projects/chime_frb/',
        'chime': '/',
        'gbo': '/',
        'hco': '/',
        'kko': '/',
        'local': './'
    }},
    'server': 'https://frb.chimenet.ca/datatrail',
    'site': 'chime',
    'vospace_certfile': '{home}/.ssl/cadcproxy.pem'
}}
"""
    assert result.exit_code == 0
    assert result.output == expected_response
    runner.invoke(datatrail, ["config", "set", "site", "local"])
    result = runner.invoke(datatrail, ["config", "ls"])
    home = Path.home().as_posix()
    expected_response = f"""Filename: {home}/.datatrail/config.yaml
{{
    'root_mounts': {{
        'canfar': '/arc/projects/chime_frb/',
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


def test_cli_pull_no(runner: CliRunner) -> None:
    """Test for CLI pull command.

    Answer 'no' to prompt for confirmation.

    Args:
        runner (CliRunner): Click runner.
    """
    result = runner.invoke(
        datatrail,
        [
            "pull",
            "chime.event.intensity.raw",
            "222266914",
        ],
        input="n\n",
    )
    expect = """Searching for files for 222266914 chime.event.intensity.raw..."""
    assert expect in result.output


def test_cli_pull_yes(runner: CliRunner, directory: Path) -> None:
    """Test for CLI pull command.

    Answer 'yes' to prompt for confirmation.

    Args:
        runner (CliRunner): Click runner.
        directory (Path): Path to downloaded data to.
    """
    result = runner.invoke(
        datatrail,
        [
            "pull",
            "chime.event.intensity.raw",
            "222266914",
            "-d",
            f"{directory.as_posix()}",
        ],
        input="y\n",
    )
    assert result.exit_code == 0
    assert Path(
        "tmp_test/data/chime/intensity/raw/2022/04/25/astro_222266914/0104/astro_222266914_20220425105208347783_beam0104_00475476_01.msgpack"  # noqa
    ).exists()


def test_cli_clear_no(runner: CliRunner, directory: Path) -> None:
    """Test for CLI clear command.

    Answer 'no' to prompt for confirmation.

    Args:
        runner (CliRunner): Click runner.
    """
    result = runner.invoke(
        datatrail,
        [
            "clear",
            "chime.event.intensity.raw",
            "222266914",
            "-d",
            f"{directory.as_posix()}",
        ],
        input="n\n",
    )
    assert result.exit_code == 0
    assert "Roger roger, no files deleted" in result.output


def test_cli_clear_yes(runner: CliRunner, directory: Path) -> None:
    """Test for CLI clear command.

    Answer 'yes' to prompt for confirmation.

    Args:
        runner (CliRunner): Click runner.
        directory (Path): Path to remove data from.
    """
    assert Path(
        "tmp_test/data/chime/intensity/raw/2022/04/25/astro_222266914/0104/astro_222266914_20220425105208347783_beam0104_00475476_01.msgpack"  # noqa
    ).exists()
    result = runner.invoke(
        datatrail,
        [
            "clear",
            "chime.event.intensity.raw",
            "222266914",
            "-d",
            f"{directory.as_posix()}",
        ],
        input="y\n",
    )
    assert result.exit_code == 0
    assert not Path(
        "tmp_test/data/chime/intensity/raw/2022/04/25/astro_222266914/0104/astro_222266914_20220425105208347783_beam0104_00475476_01.msgpack"  # noqa
    ).exists()


def test_cli_pull_force(runner: CliRunner, directory: Path) -> None:
    """Test for CLI pull command.

    Use '-f' to force download.

    Args:
        runner (CliRunner): Click runner.
        directory (Path): Path to downloaded data to.
    """
    result = runner.invoke(
        datatrail,
        [
            "pull",
            "chime.event.intensity.raw",
            "222266914",
            "-f",
            "-d",
            f"{directory.as_posix()}",
        ],
    )
    assert result.exit_code == 0
    assert Path(
        "tmp_test/data/chime/intensity/raw/2022/04/25/astro_222266914/0104/astro_222266914_20220425105208347783_beam0104_00475476_01.msgpack"  # noqa
    ).exists()


def test_cli_clear_force(runner: CliRunner, directory: Path) -> None:
    """Test for CLI clear command.

    Use '-f' to force clear data.

    Args:
        runner (CliRunner): Click runner.
        directory (Path): Path to remove data from.
    """
    assert Path(
        "tmp_test/data/chime/intensity/raw/2022/04/25/astro_222266914/0104/astro_222266914_20220425105208347783_beam0104_00475476_01.msgpack"  # noqa
    ).exists()
    result = runner.invoke(
        datatrail,
        [
            "clear",
            "chime.event.intensity.raw",
            "222266914",
            "-f",
            "-d",
            f"{directory.as_posix()}",
        ],
    )
    assert result.exit_code == 0
    assert not Path(
        "tmp_test/data/chime/intensity/raw/2022/04/25/astro_222266914/0104/astro_222266914_20220425105208347783_beam0104_00475476_01.msgpack"  # noqa
    ).exists()


def test_cli_pull_force_2cores(runner: CliRunner, directory: Path) -> None:
    """Test for CLI pull command.

    Use '-f' to force download and use 2 cores.

    Args:
        runner (CliRunner): Click runner.
        directory (Path): Path to downloaded data to.
    """
    result = runner.invoke(
        datatrail,
        [
            "pull",
            "chime.event.intensity.raw",
            "222266914",
            "-f",
            "-d",
            f"{directory.as_posix()}",
            "-c",
            "2",
        ],
    )
    assert result.exit_code == 0
    assert Path(
        "tmp_test/data/chime/intensity/raw/2022/04/25/astro_222266914/0104/astro_222266914_20220425105208347783_beam0104_00475476_01.msgpack"  # noqa
    ).exists()


def test_cli_clear_bad_site(runner: CliRunner) -> None:
    """Test for CLI clear command.

    Use site that clear does not work with.

    Args:
        runner (CliRunner): Click runner.
    """
    runner.invoke(datatrail, ["config", "set", "site", "chime"])
    result = runner.invoke(
        datatrail, ["clear", "chime.event.intensity.raw", "222266914"]
    )
    assert result.exit_code == 1
    assert isinstance(result.exception, RuntimeError)
    runner.invoke(datatrail, ["config", "set", "site", "local"])


def test_cli_clear_no_files_found(runner: CliRunner) -> None:
    """Test for CLI clear command.

    No files to clear.

    Args:
        runner (CliRunner): Click runner.
    """
    result = runner.invoke(
        datatrail, ["clear", "chime.event.intensity.raw", "222266914"]
    )
    assert result.exit_code == 1
    assert "No files to clear" in result.output


def test_cli_version(runner: CliRunner) -> None:
    """Test for CLI version.

    Args:
        runner (CliRunner): Click runner.
    """
    result = runner.invoke(datatrail, ["version"])
    assert result.exit_code == 0
    assert "Datatrail Versions" in result.output
