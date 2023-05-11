"""Class to facilitate data transfer on CANFAR using the CADC tools."""

import logging
import os
import sys
from io import StringIO
from multiprocessing import Process  # Use the standard library only
from typing import Any, Dict, List, Optional, Tuple

import cadcutils
import dill
from cadcdata import StorageInventoryClient
from cadctap import CadcTapClient
from cadcutils import net
from rich.traceback import install

from dtcli.config import procure
from dtcli.utilities.utilities import split

logger = logging.getLogger("cadcclient")
install()


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
    # TODO: Handle invalid cert
    except ValueError as error:
        logger.error(error)
        raise error


def get(
    source: List[str],
    destination: List[str],
    certfile: Optional[str] = None,
    namespace: str = "cadc:CHIMEFRB",
):
    """Retrieve a file, stored on the CANFAR file server, and copy it locally.

    Args:
        source (List[str]): List of source files to retrieve.
        destination (List[str]): List of destination files to copy to.
        certfile (Optional[str], optional): Certificate. Defaults to None.
        namespace (str): Minoc Namespace. Defaults to "cadc:CHIMEFRB".
    """
    _, storage, _ = _connect(certfile=certfile)
    try:
        assert len(source) == len(destination), (
            "The number of source files must match the number of destination files."
            f"Got {len(source)} source files and {len(destination)} destination files."
        )
        for index, filename in enumerate(source):
            filename = namespace + "/" + filename
            storage.cadcget(filename, destination[index])  # type: ignore
            logger.debug(f"{filename} ➜ {destination[index]} ✔")
    except cadcutils.exceptions.NotFoundException as error:  # type: ignore
        logger.error(f"CADC Exception: {error}")
        raise error
    except cadcutils.exceptions.HttpException as error:  # type: ignore
        logger.error(f"CADC Exception: {error}")
        raise error
    except Exception as error:
        logger.error(f"Error: {error}")
        raise error
    logger.info(f"Process {os.getpid()} finished.")


def pget(
    source: List[str],
    destination: List[str],
    certfile: Optional[str] = None,
    namespace: str = "cadc:CHIMEFRB",
    processors: int = os.cpu_count() or 1,
):
    """Parallelly retrieve files, stored on the CANFAR file server, and copy it locally.

    Args:
        source (List[str]): List of source files to retrieve.
        destination (List[str]): List of destination files to copy to.
        certfile (Optional[str], optional): Certificate. Defaults to None.
        namespace (_type_, optional): Minoc Namespace. Defaults to "cadc:CHIMEFRB".
        processors (int, optional): Number of processes to use.
            Defaults to os.cpu_count() or 1.
    """
    sources: List[List[Any]] = split(source, processors)
    destinations: List[List[Any]] = split(destination, processors)
    logger.info(f"Starting {processors} processes.")
    processes: List[DillProcess] = []
    for process in range(processors):
        mp = DillProcess(
            target=get,
            args=(sources[process], destinations[process], certfile, namespace),
        )
        processes.append(mp)
    for proc in processes:
        proc.start()
    for proc in processes:
        proc.join()


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
    sys.stdout = sys.__stdout__
    return float(content.split("\n")[0])
