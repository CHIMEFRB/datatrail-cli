"""Datatrail CLI Configuration."""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

import click
import yaml
from click_aliasing import ClickAliasedGroup
from mergedeep import merge
from rich import print, prompt

log = logging.getLogger("config")

CONFIG: Path = Path.home() / ".datatrail" / "config.yaml"


@click.group(cls=ClickAliasedGroup)
def config():
    """Datatrail CLI Configuration.

    For initialising and modifying the Datatrail CLI configuration file.
    """
    pass


@config.command(name="set", help="Set a configuration value.")
@click.argument("key", type=click.STRING, required=True, nargs=1)
@click.argument("value", type=click.STRING, required=True, nargs=1)
def set(key: str, value: str):
    """Set a configuration value.

    Args:
        key (str): Key to set.
        value (str): Value to set.
    """
    print(f"Attempting to set {key} to {value}")
    with open(CONFIG) as stream:
        config = yaml.safe_load(stream)
    with open(CONFIG, "w") as stream:
        update = {key: value}
        merge(config, update)
        yaml.safe_dump(config, stream)
    print(f"Set {key} to {value}")


@config.command(name="get", help="Get a configuration value.")
@click.argument("key", type=click.STRING, required=True, nargs=1)
def get(key: str):
    """Get a configuration value.

    Args:
        key (str): Key to get.
    """
    with open(CONFIG) as stream:
        try:
            config = yaml.safe_load(stream)
            print(f"site -> {config[key]}")
        except yaml.YAMLError as exc:
            print(exc)


@config.command(name="list", aliases=["ls"], help="List all configuration values.")
def list():
    """List all configuration values."""
    print(f"Filename: {CONFIG}")
    with open(CONFIG) as stream:
        try:
            print(yaml.safe_load(stream))
        except yaml.YAMLError as exc:
            print(exc)


@config.command(
    name="init",
    help="""Initialise configuration.

    This will create a configuration file in the home directory under `.datatrail`.
    Datatrail MUST be initialised before is can be used.
""",
)
@click.option(
    "--site",
    "-s",
    type=click.Choice(["chime", "canfar", "kko", "gbo", "hco", "local"]),
    help="Site to initialise Datatrail CLI for.",
    required=True,
)
def init(site: str):
    """Initialise configuration.

    Args:
        site (str): Site to initialise.
    """
    # Default configuration.
    defaults: Dict[str, Any] = {
        "server": "https://frb.chimenet.ca/datatrail",
        "vospace_certfile": f"{Path.home()}/.ssl/cadcproxy.pem",
        "root_mounts": {
            "chime": "/",
            "canfar": "/arc/projects/chime_frb/",
            "kko": "/",
            "gbo": "/",
            "hco": "/",
            "local": "./",
        },
    }
    defaults["site"] = site
    # Check if config file exists.
    if CONFIG.exists():
        print(f"Datatrail config file {CONFIG} already exists.")
        print("Use **datatrail config set** to change individual values.")
        if prompt.Confirm.ask("Would you like to overwrite it?"):
            # Delete the coinfig file.
            CONFIG.unlink()

    # Create a new config file.
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG.as_posix(), "w") as stream:
        try:
            yaml.safe_dump(defaults, stream)
        except yaml.YAMLError as exc:
            print(exc)
    print(f"Datatrail config file {CONFIG} created.")


def procure(config: Path = CONFIG, key: Optional[str] = None) -> Any:
    """Procure the configuration file.

    Args:
        config (Path, optional): Configuration. Defaults to CONFIG.

    Returns:
        Dict[str, Any]: Configuration.
    """
    try:
        with open(config.as_posix()) as stream:
            configuration = yaml.safe_load(stream)
        if key:
            return configuration[key]
        return configuration
    except Exception as exception:
        log.exception(exception)
        configuration = None
