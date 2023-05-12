"""Functions for CLI."""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

from dtcli.config import procure
from dtcli.utilities import cadcclient, utilities

logger = logging.getLogger("functions")


def list(  # noqa: C901
    scope: Optional[str] = None,
    dataset: Optional[str] = None,
    verbose: int = 0,
    quiet: bool = False,
) -> Dict[str, Any]:
    """List Datatrail Scopes & Datasets.

    Args:
        scope (Optional[str], optional): Scope of dataset. Defaults to None.
        dataset (Optional[str], optional): Name of dataset. Defaults to None.
        verbose (int, optional): Verbosity. Defaults to 0.
        quiet (bool, optional): Minimal logging. Defaults to False.

    Returns:
        Dict[str, Any]: Keys 'error', 'scopes', or 'datasets'. Values are the
            results or error message.
    """
    logger.setLevel("WARNING")
    if verbose == 1:
        logger.setLevel("INFO")
    elif verbose > 1:
        logger.setLevel("DEBUG")
    elif quiet:
        logger.setLevel("ERROR")
    # Load configuration.
    logger.debug("Loading configuration.")
    try:
        config = procure()
        server = config["server"]
        logger.debug("Configuration loaded successfully.")
    except Exception:
        logger.error(
            "No configuration file found. Create one with `datatrail config init`."
        )
        return {"error": "No config. Create one with `datatrail config init`."}
    # List all scopes.
    if not scope:
        logger.info("Finding all scopes in Datatrail.")
        try:
            url = server + "/query/dataset/scopes"
            r = requests.get(url)
            response = utilities.decode_response(r)
            return {"scopes": response}
        except requests.exceptions.ConnectionError as e:
            logger.error(e)
            return {"error": "Datatrail Server at CHIME is not responding."}

    # TODO:
    # If scope defined, list all datasets in scope.

    # List all top-level datasets in scope.
    elif scope and not dataset:
        logger.info("Finding all larger datasets in Datatrail.")
        try:
            url = server + f"/query/dataset/larger?scope={scope}"
            r = requests.get(url)
            response = utilities.decode_response(r)
            if isinstance(response, dict):
                return response
            else:
                raise requests.exceptions.ConnectionError(response)
        except requests.exceptions.ConnectionError as error:
            logger.error(error)
            return {"error": f"{error}"}

    # List all datasets in dataset for scope.
    elif scope and dataset:
        logger.info(f"Finding all child datasets for: {dataset} in {scope}.")
        try:
            url = server + f"/query/dataset/children/{scope}/{dataset}"
            logger.debug(f"URL: {url}")
            r = requests.get(url)
            logger.debug(f"Status: {r.status_code}.")
            response = utilities.decode_response(r)
            logger.debug(f"Reponse: {response}")
            if "object has no attribute" in response:
                return {"error": f"The dataset {dataset} has no children."}
            return {"datasets": response["contains"]}  # type: ignore
        except requests.exceptions.ConnectionError as e:
            logger.error(e)
            return {"error": "Datatrail Server at CHIME is not responding."}

    else:
        return {}


def ps(
    scope: str, dataset: str, base_url: Optional[str] = None
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """List detailed information about a dataset.

    Args:
        scope (Optional[str], optional): Scope of dataset. Defaults to None.
        dataset (Optional[str], optional): Name of dataset. Defaults to None.
        base_url (Optional[str], optional): Datatrail URL. Defaults to None.

    Returns:
        Tuple[Dict[str, Any], Dict[str, Any]]: Dictionary of dataset files,
            and dictionary of dataset's policies.
    """
    # Load configuration.
    try:
        config = procure()
        server = config["server"]
    except Exception:
        raise FileNotFoundError(
            "No configuration file found. Create one with `datatrail config init`."
        )
    if not base_url:
        base_url = server
    try:
        files_response = get_dataset_file_info(scope, dataset)

        url: str = str(base_url) + f"/query/dataset/{scope}/{dataset}"
        r = requests.get(url)
        policy_response = utilities.decode_response(r)
        if "object has no attribute" in policy_response or isinstance(
            files_response, str
        ):
            raise Exception(f"Could not find {dataset} {scope} in Datatrail.")

        return files_response, policy_response  # type: ignore

    except requests.exceptions.ConnectionError as e:
        logger.error(e)
        raise ConnectionError("Datatrail Server at CHIME is not responding.")


def get_dataset_file_info(
    scope: str, dataset: str, base_url: Optional[str] = None
) -> Dict[str, Any]:
    """List detailed information about a dataset.

    Args:
        scope (Optional[str], optional): Scope of dataset. Defaults to None.
        dataset (Optional[str], optional): Name of dataset. Defaults to None.
        base_url (Optional[str], optional): Datatrail URL. Defaults to None.

    Returns:
        Dict[str, Any]: JSON response from server or error string.
    """
    # Load configuration.
    config = procure()
    server = config["server"]
    if not base_url:
        base_url = server
    try:
        payload = {"scope": scope, "name": dataset}
        url = str(base_url) + "/query/dataset/find"
        r = requests.post(url, json=payload)
        response = utilities.decode_response(r)
        if "object has no attribute" in response:
            return {"error": f"Could not find {dataset} {scope} in Datatrail."}
        return response  # type: ignore
    except requests.exceptions.ConnectionError as e:
        logger.error(e)
        return {"error": "Datatrail Server at CHIME is not responding."}


def find_missing_dataset_files(scope: str, dataset: str) -> Dict:
    """List missing files for a dataset.

    Args:
        scope (str): Scope of dataset. Defaults to None.
        dataset (str): Name of dataset. Defaults to None.

    Returns:
        Dict: Dictionary of results.
    """
    # Load configuration.
    config = procure()
    SITE = config["site"]
    # find dataset
    dataset_locations = get_dataset_file_info(scope, dataset)
    if isinstance(dataset_locations, str):
        print(f"Could not find the dataset: {scope}, {dataset}")
        return {}

    # stage dataset
    site_locations = ["chime", "allenby", "gbo", "hatcreek", "canfar"]

    # check for local copy of the data.
    if SITE in site_locations and dataset_locations["file_replica_locations"].get(SITE):
        file_uris = dataset_locations["file_replica_locations"][SITE]
        print(f"Files found at {SITE}")
        # check for missing files
        missing_files = []
        existing_files = []
        for f in file_uris:
            if Path(f).exists():
                existing_files.append(f)
            else:
                missing_files.append(f)

    # For local, assume no files exist.
    else:
        missing_files = dataset_locations["file_replica_locations"]["minoc"]
        existing_files = []
    return {"missing": missing_files, "existing": existing_files}


def get_files(
    files: List[str],
    site: str,
    directory: str,
    cores: int,
) -> None:
    """Download all files from a dataset which only contains files.

    Args:
        files (List[str]): Paths of files to download.
        site (str): Local machine.
        directory (str): Path to download files to. Default depends on site.
        cores (int): Number of processors to initiate download on.

    Returns:
        None
    """
    # Load configuration.
    config = procure()
    mounts = config["root_mounts"]
    # download missing files.
    if len(files) > 0:
        print(f"{len(files)} files missing.")
        print(f"Downloading {len(files)} missing files.")
        files = [f.replace("cadc:CHIMEFRB/", "") for f in files]
        if not directory:
            directory = mounts[site]
        destinations = [directory + "/" + f for f in files]
        # make directory structure if it does not exist.
        folders = {os.path.dirname(path) for path in destinations}
        for folder in folders:
            os.makedirs(folder, exist_ok=True)
        cadcclient.pget(source=files, destination=destinations, processors=cores)
    return None
