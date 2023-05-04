"""Datatrail CLI Configuration."""

from pathlib import Path
from typing import Any, Dict

import click
import yaml
from mergedeep import merge
from rich import print, prompt

CONFIG: Path = Path.home() / ".datatrail" / "config.yaml"


@click.group()
def config():
    """Datatrail CLI Configuration."""
    pass


@config.command(name="set", help="Set a configuration value.")
@click.argument("key", type=click.STRING, required=True, nargs=1)
@click.argument("value", type=click.STRING, required=True, nargs=1)
def set(key: str, value: str):
    print(f"Setting {key} to {value}")
    """Set a configuration value."""
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
    """Get a configuration value."""
    with open(CONFIG) as stream:
        try:
            config = yaml.safe_load(stream)
            print(f"site -> {config[key]}")
        except yaml.YAMLError as exc:
            print(exc)


@config.command(name="list", help="List all configuration values.")
def list():
    """List all configuration values."""
    with open(CONFIG) as stream:
        try:
            print(yaml.safe_load(stream))
        except yaml.YAMLError as exc:
            print(exc)


@config.command(name="init", help="Initialize configuration.")
@click.option(
    "--site", "-s", type=click.STRING, help="Site to initialize.", required=True
)
def init(site: str):
    """Initialize configuration."""
    # Default configuration.
    defaults: Dict[str, Any] = {
        "server": "https://frb.chimenet.ca/datatrail",
        "vospace_certfile": f"{Path.home()}/.ssl/cadcproxy.pem",
        "root_mounts": {
            "chime": "/",
            "canfar": "/arc/project/chime_frb/",
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
        print(f"Use **datatrail config set** to change individual values.")
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


def procure(config: Path = CONFIG) -> Dict[str, Any]:
    with open(CONFIG) as stream:
        config = yaml.safe_load(stream)
    return config
