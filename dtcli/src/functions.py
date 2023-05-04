"""Functions for CLI."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from chime_frb_api import get_logger

from dtcli import CERTFILE, MOUNTS, SERVER, SITE
from dtcli.utilities import utilities
from dtcli.utilities.cadcclient import CADCClient

logger = get_logger()


def list(scope: Optional[str] = None, *args) -> Dict[str, Any]:
    """List scopes and datasets."""
    # List all scopes.
    if not scope:
        try:
            url = SERVER + "/query/dataset/scopes"
            r = requests.get(url)
            response = utilities.decode_response(r)
            return {"scopes": response}
        except requests.exceptions.ConnectionError as e:
            logger.error(e)
            return {"error": "Datatrail Server at CHIME is not responding."}

    # TODO:
    # If scope defined, list all datasets in scope.

    # List all top-level datasets in scope.
    elif scope and len(args) == 0:
        return {"error": "Please provide a dataset."}

    # List all datasets in dataset for scope.
    elif scope and len(args) == 1:
        return {}

    else:
        return {}


def ps(scope: str, dataset: str, base_url: str = SERVER):
    """List detailed information about a dataset."""
    try:
        files_response = get_dataset_file_info(scope, dataset)

        url = base_url + f"/query/dataset/{scope}/{dataset}"
        r = requests.get(url)
        policy_response = utilities.decode_response(r)

        return files_response, policy_response

    except requests.exceptions.ConnectionError as e:
        logger.error(e)
        return "Datatrail Server at CHIME is not responding."


def get_dataset_file_info(scope: str, dataset: str, base_url: str = SERVER):
    """List detailed information about a dataset."""
    try:
        payload = {"scope": scope, "name": dataset}
        url = base_url + "/query/dataset/find"
        r = requests.post(url, json=payload)
        return utilities.decode_response(r)
    except requests.exceptions.ConnectionError as e:
        logger.error(e)
        return "Datatrail Server at CHIME is not responding."


def find_missing_dataset_files(scope: str, dataset: str) -> Dict:
    """List missing files for a dataset."""
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
    root_dir: str = MOUNTS[SITE],
) -> Dict[str, Any]:
    """Download all files from a dataset which only contains files."""
    # download missing files.
    if len(files) > 0:
        print(f"{len(files)} files missing.")
        print(f"Downloading {len(files)} missing files.")
        files = [f.replace("cadc:CHIMEFRB/", "") for f in files]
        root_dir = MOUNTS[SITE]
        destinations = [root_dir + f for f in files]

        # make directory structure if it does not exist.
        dir_path = os.path.join(*(destinations[0].split("/")[:-1]))
        if SITE != "local":
            dir_path = "/" + dir_path
        os.makedirs(dir_path, exist_ok=True)

        # copy files.
        c = CADCClient(cadcprox_config=CERTFILE)
        c.get(files, destinations, num_processors=1)
        if SITE != "local":
            os.system(f"chgrp -R chime-frb-rw {dir_path}")
            os.system(f"chmod -R g+w {dir_path}")
        print(f"Missing files copied to folder {dir_path}")

    else:
        print("There are no files for this dataset at the Minoc server at CANFAR!!!")
