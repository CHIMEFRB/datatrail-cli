"""Class to facilitate data transfer on CANFAR using the CADC tools."""

import logging
import os
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor
from io import StringIO
from multiprocessing import Pipe, Process  # Use the standard library only
from multiprocessing.connection import Connection
from typing import Any, Dict, List, Optional, Tuple

import cadcutils
import dill
import requests
from cadcdata import StorageInventoryClient
from cadctap import CadcTapClient
from cadcutils import net
from requests.exceptions import HTTPError
from rich.traceback import install
from tenacity import Retrying, stop_after_attempt, wait_exponential

from dtcli.config import procure
from dtcli.utilities.utilities import split

logger = logging.getLogger("cadcclient")
install()

TransferFailure = Dict[str, str]


class DillProcess(Process):
    """A Process class that uses dill to serialize the target function before execution.

    Args:
        Process (object): Python Process class.
    """

    def __init__(self, *args: Any, **kwargs: Any):
        """Initialize the DillProcess class."""
        super().__init__(*args, **kwargs)
        self._target = dill.dumps(self._target)  # type: ignore

    def run(self):
        """Run the DillProcess."""
        if self._target:
            self._target = dill.loads(self._target)  # type: ignore
            self._target(*self._args, **self._kwargs)  # type: ignore


def _connect(
    certfile: Optional[str] = None,
    storage_resource_id: str = "ivo://cadc.nrc.ca/uvic/minoc",
    query_resource_id: str = "ivo://cadc.nrc.ca/uvic/luskan",
) -> Tuple[net.Subject, StorageInventoryClient, CadcTapClient]:
    """Connect to the CADC storage and query servers.

    Args:
        certfile (Optional[str], optional): X509 Certificate.
            Defaults to None.
        storage_resource_id (_type_, optional): Storage ID.
            Defaults to "ivo://cadc.nrc.ca/uvic/minoc".
        query_resource_id (_type_, optional): Query ID.
            Defaults to "ivo://cadc.nrc.ca/uvic/luskan".

    Returns:
        Tuple[net.Subject, StorageInventoryClient, CadcTapClient]:
            Returns a tuple of the cert, storage, and query clients.
    """
    try:
        if not certfile:
            certfile = procure(key="vospace_certfile")
        cert = net.Subject(certificate=certfile)
        storage = StorageInventoryClient(cert, resource_id=storage_resource_id)
        query = CadcTapClient(cert, resource_id=query_resource_id)
        return cert, storage, query
    except ValueError as error:
        logger.error(
            "Authorization failed: The provided CANFAR certificate is "
            "invalid or expired. Please ensure you have a valid "
            "certificate and try again."
        )
        raise ValueError("Invalid or expired CANFAR certificate.") from error


def get(
    source: List[str],
    destination: List[str],
    certfile: Optional[str] = None,
    namespace: str = "cadc:CHIMEFRB",
    verbose: int = 0,
) -> List[TransferFailure]:
    """Retrieve a file, stored on the CANFAR file server, and copy it locally.

    Args:
        source (List[str]): List of source files to retrieve.
        destination (List[str]): List of destination files to copy to.
        certfile (Optional[str], optional): Certificate. Defaults to None.
        namespace (str): Minoc Namespace. Defaults to "cadc:CHIMEFRB".
        verbose (int): Verbosity level. Defaults to 0.

    Returns:
        List[TransferFailure]: Files that could not be downloaded.
    """
    # Set logging level.
    logger.setLevel("WARNING")
    if verbose == 1:
        logger.setLevel("INFO")
    elif verbose > 1:
        logger.setLevel("DEBUG")

    logger.debug("Checking source and destination length match.")
    logger.debug(f"Source length: {len(source)}")
    logger.debug(f"Destination length: {len(destination)}")
    if len(source) != len(destination):
        raise ValueError(
            "The number of source files must match the number of destination files. "
            f"Got {len(source)} source files and {len(destination)} destination files."
        )
    logger.info("Connecting to CADC...")
    try:
        _, storage, _ = _connect(certfile=certfile)
    except Exception as error:
        logger.error(f"CADC connection failed: {error}")
        return [
            _transfer_failure(filename, destination[index], error)
            for index, filename in enumerate(source)
        ]

    failures: List[TransferFailure] = []
    for index, filename in enumerate(source):
        uri = namespace + "/" + filename
        try:
            expected_size = _get_expected_size(storage, uri)
            _download_file(storage, uri, destination[index], expected_size)
            logger.debug(f"{uri} -> {destination[index]}")
        except Exception as error:
            logger.error(f"Could not download {uri}: {error}")
            failures.append(_transfer_failure(filename, destination[index], error))

    if failures:
        logger.error(f"Number of failed downloads: {len(failures)}")
    logger.info(f"Process {os.getpid()} finished.")
    return failures


def _get_expected_size(storage: Any, uri: str) -> Optional[int]:
    """Return the remote size when Minoc provides one."""
    try:
        size = storage.cadcinfo(uri).size
    except cadcutils.exceptions.NotFoundException:  # type: ignore
        raise
    except cadcutils.exceptions.HttpException as error:  # type: ignore
        logger.warning(f"Could not get the size of {uri}: {error}")
        return None

    if isinstance(size, int) and not isinstance(size, bool) and size >= 0:
        return size
    return None


def _download_file(
    storage: Any, uri: str, destination: str, expected_size: Optional[int]
) -> None:
    """Download and atomically publish one file."""
    for attempt in Retrying(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
    ):
        with attempt:
            temporary = _create_temporary_sibling(destination)
            try:
                storage.cadcget(uri, temporary)
                actual_size = os.path.getsize(temporary)
                if expected_size is not None and actual_size != expected_size:
                    raise OSError(
                        f"size mismatch: expected {expected_size} bytes, "
                        f"received {actual_size}"
                    )
                os.replace(temporary, destination)
            except BaseException:
                try:
                    os.unlink(temporary)
                except FileNotFoundError:
                    pass
                raise


def _create_temporary_sibling(destination: str) -> str:
    """Create a temporary transfer path beside its destination."""
    destination_dir = os.path.dirname(destination) or "."
    name = os.path.basename(destination)
    temporary = os.path.join(destination_dir, f".{name}.{uuid.uuid4().hex}.part")
    descriptor = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o666)
    os.close(descriptor)
    return temporary


def _transfer_failure(
    source: str, destination: str, error: BaseException
) -> TransferFailure:
    """Describe one failed transfer."""
    detail = str(error) or type(error).__name__
    return {"source": source, "destination": destination, "error": detail}


def _send_get_results(
    connection: Connection,
    source: List[str],
    destination: List[str],
    certfile: Optional[str],
    namespace: str,
    verbose: int,
) -> None:
    """Send one worker's failures to its parent."""
    try:
        connection.send(get(source, destination, certfile, namespace, verbose))
    finally:
        connection.close()


def _terminate_workers(
    workers: List[Tuple[DillProcess, Connection, List[str], List[str]]]
) -> None:
    """Stop unfinished download workers."""
    for proc, _, _, _ in workers:
        if proc.is_alive():
            proc.terminate()
    for proc, _, _, _ in workers:
        proc.join()


def pget(
    source: List[str],
    destination: List[str],
    certfile: Optional[str] = None,
    namespace: str = "cadc:CHIMEFRB",
    processors: int = os.cpu_count() or 1,
    verbose: int = 0,
) -> List[TransferFailure]:
    """Parallelly retrieve files, stored on the CANFAR file server, and copy it locally.

    Args:
        source (List[str]): List of source files to retrieve.
        destination (List[str]): List of destination files to copy to.
        certfile (Optional[str], optional): Certificate. Defaults to None.
        namespace (_type_, optional): Minoc Namespace. Defaults to "cadc:CHIMEFRB".
        processors (int, optional): Number of processes to use.
            Defaults to os.cpu_count() or 1.
        verbose (int, optional): Verbosity level. Defaults to 0.

    Returns:
        List[TransferFailure]: Files that could not be downloaded.
    """
    # Set logging level.
    logger.setLevel("WARNING")
    if verbose == 1:
        logger.setLevel("INFO")
    elif verbose > 1:
        logger.setLevel("DEBUG")

    if len(source) != len(destination):
        raise ValueError(
            "The number of source files must match the number of destination files. "
            f"Got {len(source)} source files and {len(destination)} destination files."
        )
    if not source:
        return []
    if processors < 1:
        raise ValueError("processors must be greater than 0")

    # Do not start more workers than there are files.
    processors = min(processors, len(source))
    sources: List[List[Any]] = split(source, processors)
    destinations: List[List[Any]] = split(destination, processors)
    logger.info(f"Starting {processors} processes.")
    workers: List[Tuple[DillProcess, Connection, List[str], List[str]]] = []
    for process in range(processors):
        receiver, sender = Pipe(duplex=False)
        mp = DillProcess(
            target=_send_get_results,
            args=(
                sender,
                sources[process],
                destinations[process],
                certfile,
                namespace,
                verbose,
            ),
        )
        mp.start()
        sender.close()
        workers.append((mp, receiver, sources[process], destinations[process]))

    failures: List[TransferFailure] = []
    try:
        for proc, receiver, worker_sources, worker_destinations in workers:
            try:
                failures.extend(receiver.recv())
            except EOFError:
                proc.join()
                error = RuntimeError(f"download worker exited with code {proc.exitcode}")
                failures.extend(
                    _transfer_failure(filename, worker_destinations[index], error)
                    for index, filename in enumerate(worker_sources)
                    if not os.path.exists(worker_destinations[index])
                )
        for proc, _, _, _ in workers:
            proc.join()
    except BaseException:
        _terminate_workers(workers)
        raise
    finally:
        for _, receiver, _, _ in workers:
            receiver.close()

    return failures


def info(
    filenames: List[str], namespace: str = "cadc:CHIMEFRB", summary: bool = False
) -> List[Dict[str, Any]]:
    """Get the metadata for a list of files.

    Args:
        filenames (List[str]): List of filenames to get metadata for.
        namespace (_type_, optional): Minoc Namespace. Defaults to "cadc:CHIMEFRB".
        aggregate (bool, optional): Aggregate the results. Defaults to False.

    Returns:
        List[Dict[str, Any]]: List of metadata for each file.
    """
    _, storageClient, _ = _connect()
    information: List[Dict[str, Any]] = []
    uris: List[str] = []
    for filename in filenames:
        uris.append(namespace + "/" + filename)
    logger.info(f"Getting info for {len(uris)} files on {namespace}.")
    for uri in uris:
        try:
            information.append(storageClient.cadcinfo(uri).__dict__)  # type: ignore
        except cadcutils.exceptions.NotFoundException as error:  # type: ignore
            logger.debug(f"CADC Exception: {error}")
    if summary:
        aggregate: Dict[str, Any] = {
            "ids": set(),
            "size": 0,
            "names": set(),
            "md5sums": set(),
            "file_types": set(),
            "encodings": set(),
            "oldestmod": None,
            "newestmod": None,
        }
        for fileinfo in information:
            aggregate["id"].add(fileinfo["id"])
            aggregate["size"] += fileinfo["size"]
            aggregate["name"].add(fileinfo["name"])
            aggregate["md5sum"].add(fileinfo["md5sum"])
            aggregate["filetype"].add(fileinfo["file_type"])
            aggregate["encoding"].add(fileinfo["encoding"])
            if aggregate["oldest"] is None or fileinfo["lastmod"] < aggregate["oldest"]:
                aggregate["oldest"] = fileinfo["lastmod"]
            if aggregate["newest"] is None or fileinfo["lastmod"] > aggregate["newest"]:
                aggregate["newest"] = fileinfo["lastmod"]
        return [aggregate]
    return information


def size(directory: str, namespace: str = "cadc:CHIMEFRB", timeout: int = 60) -> float:
    """Get the size of a directory in GB.

    Args:
        directory (str): Directory to get the size of.
        namespace (_type_, optional): Minoc Namespace. Defaults to "cadc:CHIMEFRB".
        timeout (int, optional): Timeout. Defaults to 60.

    Returns:
        float: Size of the directory in GB.

    Example:
        >>> size("/data/chime/intensity/raw/2023/01/01/")
    """
    logger.info("Getting size of {directory}...")
    query = f"select sum(contentLength/1024.0/1024.0/1024.0) as numGB from inventory.Artifact where uri like '{namespace}/{directory}%'"  # noqa
    query = query.replace("//", "/")
    logger.info(f"Running query: {query}")
    buffer = StringIO()
    original_stdout = sys.stdout
    try:
        sys.stdout = buffer
        _, _, queryClient = _connect()
        queryClient.query(  # type: ignore
            query=query,
            output_file=None,
            response_format="csv",
            tmptable=None,
            lang="ADQL",
            timeout=timeout,
            data_only=True,
            no_column_names=True,
        )
        content = buffer.getvalue()
    finally:
        sys.stdout = original_stdout
    return float(content.split("\n")[0])


def dataset_md5s(
    directory: str,
    namespace: str = "cadc:CHIMEFRB",
    timeout: int = 60,
    verbose: int = 0,
) -> Dict[str, str]:
    """Get list of files in a directory.

    Args:
        directory (str): Directory to get the size of.
        certfile (str, optional): Certificate file. Defaults to None.
        namespace (str, optional): Minoc Namespace. Defaults to "cadc:CHIMEFRB".
        timeout (int, optional): Timeout. Defaults to 60.
        verbose (int, optional): Verbosity. Defaults to 0.

    Returns:
        Dict[str, str]: Dictionary of file paths and their md5 checksums.

    Example:
        >>> dataset_md5s("data/gbo/baseband/raw/2024/01/10/astro_350955086")
    """
    # Set logging level.
    logger.setLevel("WARNING")
    if verbose == 1:
        logger.setLevel("INFO")
    elif verbose > 1:
        logger.setLevel("DEBUG")

    query = f"select uri,contentChecksum from inventory.Artifact where uri like '{namespace}/{directory}%'"  # noqa
    query = query.replace("//", "/")
    logger.info(f"Running query: {query}")
    buffer = StringIO()
    original_stdout = sys.stdout
    try:
        sys.stdout = buffer
        _, _, queryClient = _connect()
        queryClient.query(  # type: ignore
            query=query,
            output_file=None,
            response_format="csv",
            tmptable=None,
            lang="ADQL",
            timeout=timeout,
            data_only=True,
            no_column_names=True,
        )
        content = buffer.getvalue()
    finally:
        sys.stdout = original_stdout
    paths = []
    md5s = []
    for line in content.split("\n"):
        if line == "":
            continue
        path = line.split(",")[0].replace(namespace + "/", "")
        try:
            md5 = line.split(",")[1].replace("md5:", "")
        except IndexError:
            md5 = ""
        paths.append(path)
        md5s.append(md5)
    data: Dict[str, str] = {}
    for p, m in zip(paths, md5s):
        data[p] = m
    return data


def query(
    query: str,
    namespace: str = "cadc:CHIMEFRB",
    timeout: int = 60,
    verbose: int = 0,
) -> List[Any]:
    """Get list of files in a directory.

    Args:
        query (str): SQL query.
        certfile (str, optional): Certificate file. Defaults to None.
        namespace (str, optional): Minoc Namespace. Defaults to "cadc:CHIMEFRB".
        timeout (int, optional): Timeout. Defaults to 60.
        verbose (int, optional): Verbosity. Defaults to 0.

    Returns:
        List[str]: List of files in the directory.

    Example:
        >>> size("/data/chime/intensity/raw/2023/01/01/")
    """
    # Set logging level.
    logger.setLevel("WARNING")
    if verbose == 1:
        logger.setLevel("INFO")
    elif verbose > 1:
        logger.setLevel("DEBUG")

    query = query.replace("//", "/")
    logger.info(f"Running query: {query}")
    buffer = StringIO()
    original_stdout = sys.stdout
    try:
        sys.stdout = buffer
        _, _, queryClient = _connect()
        queryClient.query(  # type: ignore
            query=query,
            output_file=None,
            response_format="csv",
            tmptable=None,
            lang="ADQL",
            timeout=timeout,
            data_only=True,
            no_column_names=True,
        )
        content = buffer.getvalue()
    finally:
        sys.stdout = original_stdout
    return [line.split(",") for line in content.split("\n")]


def status(
    certfile: Optional[str] = None,
) -> Tuple[bool, bool]:
    """Check the status of Minoc.

    Args:
        certfile: Canfar certificate file.

    Returns:
        bool: True if Minoc is up, False otherwise.
    """
    urls: List[str] = [
        "https://ws-uv.canfar.net/minoc/capabilities",
        "https://ws-uv.canfar.net/luskan/capabilities",
    ]
    if not certfile:
        certfile = procure(key="vospace_certfile")

    def check_url(url: str) -> bool:
        try:
            # Health probe: fail fast, and read a wedged or unreachable
            # endpoint as "down" rather than crashing the caller.
            response = requests.get(
                url, cert=certfile, allow_redirects=True, timeout=(10, 30)
            )
            response.raise_for_status()
            authorised = response.headers.get("x-vo-authenticated")
            if isinstance(authorised, str):
                return True
            else:
                raise TypeError
        except (HTTPError, requests.exceptions.RequestException) as error:
            logger.warning(error)
            logger.warning(f"{url.split('/')[3]} is down.")
            return False
        except TypeError:
            logger.error("Canfar certificate is not valid.")
            return False

    with ThreadPoolExecutor(max_workers=len(urls)) as executor:
        results = list(executor.map(check_url, urls))

    return results[0], results[1]
