"""Datatrail commands as functions for Workflow pipelines.

Workflow runs a pipeline step's function in the session's own process, so what the
command prints is the step's logs. Each function runs the CLI command, then checks
what it did and raises if it failed: the commands report some failures only on the
console, which a Workflow step can't see. They return (results, products, plots),
the shape Workflow expects of a function.

Example step:

    function: dtcli.workflow.pull_dataset
    parameters:
      scope: chime.event.baseband.raw
      dataset: "123456789"
      cores: 4
      site: canfar
"""

import logging
import os
from typing import Any, Dict, List, Optional, Tuple

import click

from dtcli.clear import clear
from dtcli.config import CONFIG, init, procure
from dtcli.pull import pull
from dtcli.src.functions import find_dataset_common_path, find_missing_dataset_files

logger = logging.getLogger("workflow")

Outcome = Tuple[Dict[str, Any], List[str], List[str]]


def _configure(site: Optional[str]) -> Dict[str, Any]:
    """The Datatrail configuration, created for `site` if there's none.

    Raises:
        RuntimeError: If there's no configuration and no site to create one for,
            or it's set up for another site.
    """
    if not CONFIG.exists():
        if not site:
            raise RuntimeError(
                f"There's no Datatrail configuration at {CONFIG}; "
                "give a site to create one."
            )
        # init only asks questions when a configuration exists
        init.callback(site=site)
    config = procure()
    if not config:
        raise RuntimeError(f"The Datatrail configuration at {CONFIG} can't be read.")
    if site and config.get("site") != site:
        raise RuntimeError(
            f"The Datatrail configuration at {CONFIG} is for {config.get('site')}, "
            f"not {site}."
        )
    return config


def _run(command: click.Command, args: List[str]) -> None:
    """Run a CLI command in this process.

    Raises:
        RuntimeError: If it exits with an error code.
    """
    code = command.main(args=args, standalone_mode=False)
    # with standalone_mode=False, an exit code is returned rather than raised
    if code:
        raise RuntimeError(f"datatrail {command.name} exited with {code}.")


def pull_dataset(
    scope: str,
    dataset: str,
    cores: int = 1,
    site: Optional[str] = None,
    verbose: int = 1,
    directory: Optional[str] = None,
) -> Outcome:
    """Download a dataset, then check that all its files are here.

    Args:
        scope (str): Scope of the dataset.
        dataset (str): Name of the dataset.
        cores (int): Number of parallel fetch processes. Defaults to 1.
        site (Optional[str]): Site this runs at; the configuration is created for it
            if there's none. Defaults to the configured site.
        verbose (int): Verbosity: 1=INFO, 2=DEBUG. Defaults to 1.
        directory (Optional[str]): Directory to pull to, created if it isn't there;
            the files go under it at their Datatrail paths. Defaults to the site's
            root mount.

    Returns:
        Outcome: Results (scope, dataset, number of files and where they are), no
            products and no plots.

    Raises:
        RuntimeError: If the dataset can't be found, or any of its files is missing
            after the pull.
    """
    config = _configure(site)
    dataset = str(dataset)
    args = [scope, dataset, "--force", "--cores", str(cores)] + ["-v"] * verbose
    if directory:
        os.makedirs(directory, exist_ok=True)
        args += ["--directory", directory]
        # the file paths are added to it as they are
        directory = os.path.join(directory, "")
    else:
        directory = config["root_mounts"][config["site"]]
    _run(pull, args)

    files = find_missing_dataset_files(scope, dataset, directory, verbose)
    if files.get("error"):
        raise RuntimeError(f"Could not check {scope} {dataset}: {files['error']}")
    if files["missing"]:
        raise RuntimeError(
            f"{len(files['missing'])} of {scope} {dataset}'s files weren't pulled, "
            f"e.g. {files['missing'][0]}."
        )
    if not files["existing"]:
        raise RuntimeError(f"Datatrail has no files for {scope} {dataset}.")
    results = {
        "scope": scope,
        "dataset": dataset,
        "files": len(files["existing"]),
        "directory": directory,
    }
    return results, [], []


def clear_dataset(
    scope: str,
    dataset: str,
    site: Optional[str] = None,
    clear_parents: bool = False,
    verbose: int = 1,
) -> Outcome:
    """Delete a dataset's local copy, then check that it's gone.

    A dataset with no local copy is left as it is, and isn't a failure.

    Args:
        scope (str): Scope of the dataset.
        dataset (str): Name of the dataset.
        site (Optional[str]): Site this runs at; the configuration is created for it
            if there's none. Defaults to the configured site.
        clear_parents (bool): Also delete empty parent directories. Defaults to False.
        verbose (int): Verbosity: 1=INFO, 2=DEBUG. Defaults to 1.

    Returns:
        Outcome: Results (scope, dataset, the path and whether it was cleared), no
            products and no plots.

    Raises:
        RuntimeError: If the dataset can't be found, or its files are still there.
    """
    config = _configure(site)
    directory = config["root_mounts"][config["site"]]
    dataset = str(dataset)
    common = find_dataset_common_path(scope, dataset, config["site"], verbose, False)
    # it returns a message rather than a path when the server isn't reachable
    if not common or not common.startswith(("data/", "/")):
        raise RuntimeError(f"Could not find where {scope} {dataset} is: {common}")
    # as `datatrail clear` builds it
    path = (directory + common).replace("//", "/")
    results: Dict[str, Any] = {"scope": scope, "dataset": dataset, "path": path}
    if not os.path.exists(path):
        logger.info(f"{path} doesn't exist; nothing to clear.")
        return {**results, "cleared": False}, [], []

    args = [scope, dataset, "--force"] + ["-v"] * verbose
    if clear_parents:
        args.append("--clear-parents")
    _run(clear, args)

    if os.path.exists(path):
        raise RuntimeError(f"{path} is still there after clearing it.")
    return {**results, "cleared": True}, [], []
