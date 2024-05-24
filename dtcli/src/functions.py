"""Functions for CLI."""

import logging
import os
import shutil
import time
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
    # Set logging level.
    utilities.set_log_level(logger, verbose, quiet)
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
            utilities.validate_request_response(response, dataset, scope)
            return {"datasets": response["contains"]}  # type: ignore
        except requests.exceptions.ConnectionError as e:
            logger.error(e)
            return {"error": "Datatrail Server at CHIME is not responding."}
        except Exception as e:
            logger.error(e)
            return {"error": e}
    else:
        return {}


def ps(
    scope: str,
    dataset: str,
    verbose: int = 0,
    quiet: bool = False,
    base_url: Optional[str] = None,
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """List detailed information about a dataset.

    Args:
        scope (Optional[str], optional): Scope of dataset. Defaults to None.
        dataset (Optional[str], optional): Name of dataset. Defaults to None.
        verbose (int, optional): Verbosity. Defaults to 0.
        quiet (bool, optional): Minimal logging. Defaults to False.
        base_url (Optional[str], optional): Datatrail URL. Defaults to None.

    Returns:
        Tuple[Dict[str, Any], Dict[str, Any]]: Dictionary of dataset files,
            and dictionary of dataset's policies.
    """
    # Set logging level.
    utilities.set_log_level(logger, verbose, quiet)

    # Load configuration.
    logger.debug("Loading configuration.")
    try:
        config = procure()
        server = config["server"]
        logger.debug("Configuration loaded successfully.")
    except Exception:
        raise FileNotFoundError(
            "No configuration file found. Create one with `datatrail config init`."
        )
    if not base_url:
        logger.debug(f"Setting base_url to {server}.")
        base_url = server
    try:
        files_response = get_dataset_file_info(scope, dataset, verbose, quiet)

        logger.info(f"Getting policy for {dataset} in {scope}.")
        url: str = str(base_url) + f"/query/dataset/{scope}/{dataset}"
        logger.debug(f"URL: {url}")
        r = requests.get(url)
        logger.debug(f"Status: {r.status_code}.")
        policy_response = utilities.decode_response(r)
        utilities.validate_request_response(policy_response, dataset, scope)
        if "error" in files_response:
            return None, policy_response  # type: ignore
        return files_response, policy_response  # type: ignore

    except requests.exceptions.ConnectionError as e:
        logger.error(e)
        raise ConnectionError("Datatrail Server at CHIME is not responding.")
    except Exception as e:
        logger.error(e)
        raise Exception(e)


def get_dataset_file_info(
    scope: str,
    dataset: str,
    verbose: int = 0,
    quiet: bool = False,
    base_url: Optional[str] = None,
) -> Dict[str, Any]:
    """List detailed information about a dataset.

    Args:
        scope (Optional[str], optional): Scope of dataset. Defaults to None.
        dataset (Optional[str], optional): Name of dataset. Defaults to None.
        verbose (int, optional): Verbosity. Defaults to 0.
        quiet (bool, optional): Minimal logging. Defaults to False.
        base_url (Optional[str], optional): Datatrail URL. Defaults to None.

    Returns:
        Dict[str, Any]: JSON response from server or error string.
    """
    # Set logging level.
    utilities.set_log_level(logger, verbose, quiet)

    # Load configuration.
    config = procure()
    server = config["server"]
    if not base_url:
        base_url = server
    try:
        logger.info(f"Finding files for {dataset} in {scope}.")
        payload = {"scope": scope, "name": dataset}
        logger.debug(f"Payload: {payload}")
        url = str(base_url) + "/query/dataset/find"
        logger.debug(f"URL: {url}")
        r = requests.post(url, json=payload)
        logger.debug(f"Status: {r.status_code}.")
        logger.debug("Decoding response.")
        response = utilities.decode_response(r)
        utilities.validate_request_response(response, dataset, scope)
        return response  # type: ignore
    except requests.exceptions.ConnectionError as e:
        logger.error(e)
        return {"error": "Datatrail Server at CHIME is not responding."}
    except Exception as e:
        logger.error(e)
        return {"error": e}


def find_missing_dataset_files(
    scope: str, dataset: str, root_path: Optional[str] = None, verbose: int = 0
) -> Dict:
    """List missing files for a dataset.

    Args:
        scope (str): Scope of dataset. Defaults to None.
        dataset (str): Name of dataset. Defaults to None.
        root_path (Optional[str]): Path to download files to. Defaults to None.
        verbose (int): Verbosity. Defaults to 0.

    Returns:
        Dict: Dictionary of results.
    """
    # Set logging level.
    utilities.set_log_level(logger, verbose)

    # find dataset
    dataset_locations = get_dataset_file_info(scope, dataset, verbose=verbose)
    if "error" in dataset_locations:
        return {"error": dataset_locations["error"]}

    # check for local copy of the data.
    logger.info("Checking for local copies of files.")
    if dataset_locations["file_replica_locations"].get("minoc"):
        file_uris = dataset_locations["file_replica_locations"]["minoc"]
        file_paths = []
        # Clean up file paths
        for f in file_uris:
            if f.startswith("data/"):
                file_paths.append(f)
            elif f.startswith("cadc:CHIMEFRB/"):
                file_paths.append(f.replace("//", "/").replace("cadc:CHIMEFRB/", ""))
            elif f.startswith("/"):
                file_paths.append(f.replace("//", "/")[1:])
        # check for missing files
        missing_files = []
        existing_files = []
        for f in file_paths:
            if Path(root_path + f).exists():
                logger.debug(f"- {f} : ✔")
                existing_files.append(f)
            else:
                logger.debug(f"- {f} : ✘")
                missing_files.append(f)

    else:
        missing_files = []
        existing_files = []
    return {"missing": missing_files, "existing": existing_files}


def get_files(
    files: List[str],
    site: str,
    directory: str,
    cores: int,
    verbose: int,
) -> None:
    """Download all files from a dataset which only contains files.

    Args:
        files (List[str]): Paths of files to download.
        site (str): Local machine.
        directory (str): Path to download files to. Default depends on site.
        cores (int): Number of processors to initiate download on.
        verbose (int): Verbosity level.

    Returns:
        None
    """
    # Set logging level.
    utilities.set_log_level(logger, verbose)

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
        if not directory.endswith("/"):
            directory += "/"
        destinations = [(directory + f).replace("//", "/") for f in files]
        # make directory structure if it does not exist.
        folders = {os.path.dirname(path) for path in destinations}
        if site == "canfar":
            for folder in folders:
                os.makedirs(folder, exist_ok=True)
                os.system(f"chgrp -R chime-frb-rw {folder}")  # nosec
                os.system(f"chmod -R g+w {folder}")  # nosec
        else:
            for folder in folders:
                os.makedirs(folder, exist_ok=True)
        cadcclient.pget(
            source=files, destination=destinations, processors=cores, verbose=verbose
        )
    return None


def clear_dataset_path(
    path: str, clear_parents: bool, verbose: int, quiet: bool
) -> bool:
    """Delete a path provided.

    Args:
        path (str): Path to delete.
        clear_parents (bool): Clear empty parent directories recursively.
        verbose (int): Verbosity level.
        quiet (bool): Quiet mode.

    Returns:
        bool: True if path was deleted.
    """
    # Set logging level.
    utilities.set_log_level(logger, verbose, quiet)

    logger.debug(f"clear_parents: {clear_parents}")

    # Check if path exists.
    p = Path(path)
    logger.debug(f"Checking if path {path} exists.")
    exists = p.exists()

    # Delete files.
    if exists:
        config = procure()
        site = config["site"]
        min_parents = 4
        if site == "canfar":
            min_parents = 7
        if len(p.parents) < min_parents:
            logger.critical("Path is a core directory! Cannot delete.")
            return False
        else:
            shutil.rmtree(p)
            logger.info("Path successfully removed.")
        time.sleep(0.1)
    else:
        logger.info(f"Path {path} not found.")
        return False

    # Clear empty parent directories.
    parent = p.parent
    if clear_parents:
        logger.debug(f"Clearing parent directories of {parent}.")
    while clear_parents:
        files: List[Path] = [f for f in parent.iterdir()]
        logger.debug(f"files: {files}")
        if files:
            logger.debug(f"{parent}: ✗")
            clear_parents = False
        else:
            logger.debug(f"{parent}: ✔")
            parent.rmdir()
            time.sleep(0.1)
        parent = parent.parent
    return True


def find_dataset_common_path(
    scope: str, dataset: str, site: str, verbose: int, quiet: bool
) -> Optional[str]:
    """Find common path for a dataset.

    Args:
        scope (str): Scope of dataset.
        dataset (str): Name of dataset.
        site (str): Local machine.
        verbose (int): Verbosity level.
        quiet (bool): Quiet mode.

    Returns:
        Optional[str]: Common path for dataset.
    """
    # Set logging level.
    utilities.set_log_level(logger, verbose, quiet)

    # Load configuration.
    logger.debug("Loading configuration.")
    try:
        config = procure()
        server = config["server"]
        logger.debug(f"Server: {server}")
        logger.debug("Configuration loaded successfully.")
    except Exception:
        logger.error("No config. Create one with `datatrail config init`.")
        return None
    # Query Datatrail Central Server.
    logger.info(f"Querying Datatrail for {dataset} {scope}.")
    payload = {"name": dataset, "scope": scope}
    url = server + "/query/dataset/find"
    logger.debug(f"URL: {url}")
    try:
        r = requests.post(url, json=payload)
        dataset_locations = utilities.decode_response(r)  # type: ignore
        utilities.validate_request_response(dataset_locations, dataset, scope)
    except ConnectionError:
        return "The Datatrail Central Server at CHIME at is not reachable!!!"
    except Exception as e:
        logger.error(e)
        return None

    # Build data paths.
    if dataset_locations["file_replica_locations"].get("minoc"):  # type: ignore
        file_uris = dataset_locations["file_replica_locations"]["minoc"]  # type: ignore
        file_paths = [f.replace("cadc:CHIMEFRB/", "") for f in file_uris]

        common_path = os.path.commonprefix(file_paths).replace("//", "/")
        if common_path[-1] != "/":
            common_path = "/".join(common_path.split("/")[:-1])

    else:
        logger.info(f"Dataset {dataset} {scope} not found on Minoc.")
        logger.info("Cannot clear dataset.")
        return None

    return common_path


def view_results(
    pipeline: str,
    query: Dict[str, Any],
    projection: Dict[str, Any],
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """View results from a pipeline.

    Args:
        pipeline (str): Name of pipeline.
        query (Dict[str, Any]): Query for pipeline.
        projection (Dict[str, Any]): Projection for pipeline.
        limit (int): Limit number of results.

    Returns:
        List[Dict[str, Any]]: Results from pipeline.
    """
    response = requests.post(
        "https://frb.chimenet.ca/results/view",
        json={
            "query": {"pipeline": pipeline, **query},
            "projection": projection,
            "limit": limit,
        },
    )
    return response.json()


def get_unregistered_dataset(dataset: str, scope: str) -> Optional[Dict[str, Any]]:
    """Get unregistered dataset from Datatrail.

    Args:
        dataset (str): Name of dataset.

    Returns:
        Optional[Dict[str, Any]]: Unregistered dataset information.
    """
    site = scope.split(".")[0]
    assert site in ["chime", "kko", "gbo", "hco"]
    response = view_results(
        "datatrail-unregistered-datasets",
        query={
            "site": "chime",
            "results.dataset_name": dataset,
        },
        projection={"results.files": 0},
        limit=1,
    )

    if len(response) == 0:
        return None
    else:
        return response[0]
