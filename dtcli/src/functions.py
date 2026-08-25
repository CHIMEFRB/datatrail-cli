"""Functions for CLI."""

import logging
import os
import re
import shutil
import subprocess
import time
from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

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
            r = requests.get(url, timeout=utilities.REQUEST_TIMEOUT)
            response = utilities.decode_response(r)
            if isinstance(response, str) or not isinstance(response, Sequence):
                # decode_response passes a non-JSON body (a proxy error page,
                # a 5xx message) through as text; report it, or any other
                # non-list shape, as an error instead of presenting it as
                # the scopes list. NB: the builtin list is shadowed by this
                # module's list(), hence the Sequence check.
                logger.error(f"Scopes query not answered: {response}")
                return {"error": "Datatrail did not answer the scopes query."}
            return {"scopes": response}
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
        ) as e:
            logger.error(e)
            return {"error": "Datatrail Server at CHIME is not responding."}

    # TODO:
    # If scope defined, list all datasets in scope.

    # List all top-level datasets in scope.
    elif scope and not dataset:
        logger.info("Finding all larger datasets in Datatrail.")
        try:
            url = server + f"/query/dataset/larger?scope={scope}"
            r = requests.get(url, timeout=utilities.REQUEST_TIMEOUT)
            response = utilities.decode_response(r)
            if isinstance(response, dict):
                return response
            else:
                raise requests.exceptions.ConnectionError(response)
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
        ) as error:
            logger.error(error)
            return {"error": f"{error}"}

    # List all datasets in dataset for scope.
    elif scope and dataset:
        logger.info(f"Finding all child datasets for: {dataset} in {scope}.")
        try:
            url = server + f"/query/dataset/children/{scope}/{dataset}"
            logger.debug(f"URL: {url}")
            r = requests.get(url, timeout=utilities.REQUEST_TIMEOUT)
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


def discover_datasets(
    scope: Optional[str] = None,
    match: Optional[str] = None,
    expand: bool = False,
    verbose: int = 0,
    quiet: bool = False,
    recursive: bool = False,
) -> Dict[str, Any]:
    """Map larger datasets across scopes, with filtering and expansion.

    Walks one scope, or every scope when none is given, and keeps the larger
    datasets whose "scope dataset" text contains every comma-separated,
    case-insensitive match term. With expand, each kept dataset is opened one
    level and its children become the rows, recording the opened dataset as
    their parent. With recursive, each kept dataset is opened until terminal
    datasets are reached. A dataset whose children cannot be listed keeps its
    own row. A scope or dataset Datatrail does not answer for is reported in
    'failed' rather than shown as empty.

    Args:
        scope (Optional[str], optional): Scope to walk. Defaults to None,
            which walks every scope.
        match (Optional[str], optional): Comma-separated terms a dataset must
            all contain. Defaults to None.
        expand (bool, optional): Open each kept dataset one level. Defaults
            to False.
        verbose (int, optional): Verbosity. Defaults to 0.
        quiet (bool, optional): Minimal logging. Defaults to False.
        recursive (bool, optional): Open all descendants of each kept dataset.
            Defaults to False.

    Returns:
        Dict[str, Any]: Keys 'results', rows of scope, dataset and parent,
            plus path for recursive rows, and 'failed', the branches Datatrail
            did not answer. Key 'error' on a configuration or connection
            failure.
    """
    # Set logging level.
    utilities.set_log_level(logger, verbose, quiet)
    terms = [t.strip().lower() for t in (match or "").split(",") if t.strip()]
    if scope:
        scopes = [scope]
    else:
        found = list(verbose=verbose, quiet=quiet)
        if "error" in found:
            return found
        answer = found.get("scopes")
        # A non-200 response body is passed through as a string; never walk
        # it, or any other non-list shape, as if it were the scopes list.
        # NB: isinstance against the builtin list is unavailable here, since
        # this module's list() shadows it.
        if isinstance(answer, str) or not isinstance(answer, Sequence):
            return {"error": "Datatrail did not answer the scopes query."}
        if not answer:
            return {
                "error": "Datatrail reports zero scopes: an account or "
                "configuration problem, not an empty archive."
            }
        scopes = sorted(answer)
    results: List[Dict[str, Optional[str]]] = []
    failed: List[str] = []
    for s in scopes:
        listed = list(s, verbose=verbose, quiet=quiet)
        datasets = None if "error" in listed else listed.get("larger_datasets")
        if datasets is None:
            failed.append(f"datasets in {s}")
            continue
        kept = [
            d for d in sorted(datasets) if all(t in f"{s} {d}".lower() for t in terms)
        ]
        if recursive:
            rows, branch_failures = _discover_descendants(
                s, kept, verbose=verbose, quiet=quiet
            )
            results.extend(rows)
            failed.extend(branch_failures)
            continue
        for d in kept:
            if not expand:
                results.append({"scope": s, "dataset": d, "parent": None})
                continue
            opened = list(s, d, verbose=verbose, quiet=quiet)
            children = None if "error" in opened else opened.get("datasets")
            if children is None:
                failed.append(f"children of {s} {d}")
                results.append({"scope": s, "dataset": d, "parent": None})
            elif children:
                for c in sorted(children, reverse=True):
                    results.append({"scope": s, "dataset": c, "parent": d})
            else:
                results.append({"scope": s, "dataset": d, "parent": None})
    return {"results": results, "failed": failed}


def _discover_descendants(
    scope: str,
    roots: Sequence[str],
    verbose: int = 0,
    quiet: bool = False,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Return unique terminal datasets below the given roots."""
    results: List[Dict[str, Any]] = []
    failed: List[str] = []
    visited: Set[str] = set()
    emitted: Set[str] = set()
    stack: List[Tuple[str, Optional[str], Tuple[str, ...]]] = [
        (root, None, (root,)) for root in reversed(sorted(set(roots)))
    ]

    def add_row(dataset: str, parent: Optional[str], path: Tuple[str, ...]) -> None:
        if dataset in emitted:
            return
        results.append(
            {
                "scope": scope,
                "dataset": dataset,
                "parent": parent,
                "path": [*path],
            }
        )
        emitted.add(dataset)

    while stack:
        dataset, parent, path = stack.pop()
        if dataset in visited:
            continue
        visited.add(dataset)
        opened = list(scope, dataset, verbose=verbose, quiet=quiet)
        children = None if "error" in opened else opened.get("datasets")
        if (
            children is None
            or isinstance(children, str)
            or not isinstance(children, Sequence)
            or any(not isinstance(child, str) or not child.strip() for child in children)
        ):
            failed.append(f"children of {scope} {' / '.join(path)}")
            add_row(dataset, parent, path)
            continue

        child_names = sorted(set(children))
        if not child_names:
            add_row(dataset, parent, path)
            continue

        cycle_found = False
        for child in reversed(child_names):
            if child in path:
                failed.append(f"cycle in {scope}: {' / '.join(path + (child,))}")
                cycle_found = True
                continue
            if child not in visited:
                stack.append((child, dataset, path + (child,)))
        if cycle_found:
            add_row(dataset, parent, path)

    return results, failed


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
        r = requests.get(url, timeout=utilities.REQUEST_TIMEOUT)
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
        r = requests.post(url, json=payload, timeout=utilities.REQUEST_TIMEOUT)
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
                subprocess.run(["chgrp", "-R", "chime-frb-rw", folder])
                subprocess.run(["chmod", "-R", "g+w", folder])
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
        r = requests.post(url, json=payload, timeout=utilities.REQUEST_TIMEOUT)
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
        file_paths = [
            f.replace("//", "/").replace("cadc:CHIMEFRB/", "") for f in file_uris
        ]

        common_path = os.path.commonprefix(file_paths)
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
        timeout=utilities.REQUEST_TIMEOUT,
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


def find_unregistered_datasets(
    event: str,
    scope: Optional[str] = None,
    partial: bool = False,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Find unregistered datasets recorded for an event.

    Args:
        event (str): Name of the event, i.e. the dataset name.
        scope (Optional[str]): Only return records for this scope.
        partial (bool): Match events containing `event` rather than exactly.
        limit (int): Maximum number of records to return.

    Returns:
        List[Dict[str, Any]]: Unregistered dataset records for the event.
    """
    name: Any = {"$regex": re.escape(event)} if partial else event
    query: Dict[str, Any] = {"results.dataset_name": name}
    if scope:
        query["results.dataset_scope"] = scope
    return view_results(
        pipeline="datatrail-unregistered-datasets",
        query=query,
        projection={"results.files": 0},
        limit=limit,
    )


ATTACH_RE = re.compile(
    r"Could not attach datasets: .+? ERROR: \"?dataset (.+?), (.+?) not found"  # noqa: E501
)

CREATE_RE = re.compile(
    r"Could not create dataset: (.+?), scope: (.+?)\. .*UniqueViolation"  # noqa: E501
)


def signature(msg: str) -> str:
    """Create a signature for a reason unregistered message.

    Args:
        msg: Reason message for unregistered dataset.

    Returns:
        str: Signature for error message.
    """
    msg = msg.strip()

    # Attach-dataset errors
    m = ATTACH_RE.search(msg)
    if m:
        larger_dataset, scope = m.groups()
        return f"ATTACH_MISSING:{larger_dataset}:{scope}"

    # Create-dataset unique violation
    m = CREATE_RE.search(msg)
    if m:
        dataset, scope = m.groups()
        dataset = re.sub(r"\d+", "<ID>", dataset)
        return f"CREATE_DUPLICATE:{dataset}:{scope}"

    # PostgreSQL violation
    if "psycopg" in msg:
        msg = re.sub(r"\s+", " ", msg)
        return f"POSTGRES:{msg[:120]}"

    # Short status / token messages
    if len(msg) < 80 and "\n" not in msg:
        return f"STATUS:{msg}"

    # Fallback: normalized text
    msg = re.sub(r"\d+", "<ID>", msg)
    msg = re.sub(r"\s+", " ", msg)
    return f"OTHER:{msg[:120]}"


def get_all_unregistered_datasets() -> List[Dict[str, Any]]:
    """Get all unregistered datasets from Workflow Results.

    Returns:
        List[Dict[str, Any]]: List of unregistered dataset information.
    """
    return view_results(
        pipeline="datatrail-unregistered-datasets", query={}, projection={}, limit=10000
    )


def summarise_unregistered_datasets() -> Dict[str, int]:
    """Create a summary of unregistered datasets by grouping similar error messages.

    Returns:
        Dict[str, int]: Dictionary of error message signatures and their counts.
    """
    response = get_all_unregistered_datasets()
    return Counter(signature(str(r["results"]["reason"])) for r in response)
