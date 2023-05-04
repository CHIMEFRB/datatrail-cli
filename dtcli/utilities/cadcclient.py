"""Class to facilitate data transfer on CANFAR using the CADC tools."""

import io
import logging
import os
import sys
from multiprocessing import Process

import cadcutils
import numpy
from cadcdata import StorageInventoryClient
from cadctap import CadcTapClient
from cadcutils import net

from dtcli.config import procure

LOG_FORMAT: str = "[%(asctime)s] %(levelname)s "
LOG_FORMAT += "%(module)s::%(funcName)s():l%(lineno)d: "
LOG_FORMAT += "%(message)s"
logging.basicConfig(format=LOG_FORMAT, level=logging.ERROR)
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

try:
    config = procure()
    CERTFILE = config["vospace_certfile"]
except Exception as e:
    log.error(e)
    CERTFILE = None

default_cadcprox_config = CERTFILE

resource_id_minoc = (
    "ivo://cadc.nrc.ca/uvic/minoc"  # Used to get/put/delete via minoc REST API.
)
resource_id_luskan = (
    "ivo://cadc.nrc.ca/uvic/luskan"  # Used to query inventory via luskan REST API.
)

chime_frb_namespace = "cadc:CHIMEFRB"


class CADCClient:
    """Class for CANFAR CADC API."""

    def __init__(self, cadcprox_config=None):
        """Cadc client API for managing data on Minoc."""
        self.certSubject, self.storageClient, self.queryClient = self.connect(
            cadcprox_config=cadcprox_config
        )

    def connect(
        self,
        cadcprox_config=default_cadcprox_config,
        default_storage_resource_id=resource_id_minoc,
        default_query_resource_id=resource_id_luskan,
    ):
        """Connect to the CANFAR file server."""
        if cadcprox_config is None:
            cadcprox_config = default_cadcprox_config
        certSubject = net.Subject(
            certificate=os.path.join(os.environ["HOME"], cadcprox_config)
        )

        storageClient = StorageInventoryClient(
            certSubject, resource_id=default_storage_resource_id
        )
        queryClient = CadcTapClient(certSubject, resource_id=default_query_resource_id)

        return certSubject, storageClient, queryClient

    def put(
        self,
        source_file,
        destination_file,
        overwrite=False,
        namespace=chime_frb_namespace,
        num_processors=1,
    ):
        """Copy a file, stored locally, to the CANFAR file server.

        Supports a source_file [list or numpy.ndarray],
        destination_file [list or numpy.ndarray], and running in parallel.
        Assumes a 1-to-1 mapping between the names in source_file and
        destination_file, if a list or numpy.ndarray is provided.
        """
        try:
            if not isinstance(source_file, (list, numpy.ndarray)) and not isinstance(
                destination_file, (list, numpy.ndarray)
            ):
                destination_uri = namespace + "/" + destination_file
                self.storageClient.cadcput(
                    destination_uri, source_file, replace=overwrite
                )
                log.debug(
                    f"[PUT ✔] Source file {source_file} uploaded to {chime_frb_namespace}."  # noqa
                )
            elif (
                isinstance(source_file, (list, numpy.ndarray))
                and isinstance(destination_file, (list, numpy.ndarray))
                and len(source_file) == len(destination_file)
            ):
                for ibatch in range(0, int(len(source_file) / num_processors)):
                    threads = []
                    for iprocess in range(0, num_processors):
                        ifile1 = iprocess + (ibatch * num_processors)
                        destination_uri = namespace + "/" + destination_file[ifile1]
                        t = Process(
                            target=self.storageClient.cadcput,
                            args=(destination_uri, source_file[ifile1]),
                            kwargs={"replace": overwrite},
                        )
                        threads.append(t)
                        log.debug(
                            f"[PUT ✔] Source file {source_file[ifile1]} uploaded to {chime_frb_namespace}."  # noqa
                        )
                    for job in threads:
                        job.start()
                    for job in threads:
                        job.join()
                if len(source_file) % num_processors:
                    threads = []
                    for ifile2 in range(ifile1 + 1, len(source_file)):
                        destination_uri = namespace + "/" + destination_file[ifile2]
                        t = Process(
                            target=self.storageClient.cadcput,
                            args=(destination_uri, source_file[ifile2]),
                            kwargs={"replace": overwrite},
                        )
                        threads.append(t)
                        log.debug(
                            f"[PUT ✔] Source file {source_file[ifile2]} uploaded to {chime_frb_namespace}."  # noqa
                        )
                    for job in threads:
                        job.start()
                    for job in threads:
                        job.join()
            else:
                log.debug("[ERROR ✘] len(source_file) != len(destination_file).")
        except AttributeError as error:
            error_msg = str(error)
            if "without using the replace flag" in error_msg:
                log.debug(
                    f"[ERROR ✘] Source file {source_file} already exists on {chime_frb_namespace}. Specify overwrite=True in put()."  # noqa
                )
            else:
                log.debug(
                    f"[ERROR ✘] Source file {source_file} does not exist on {chime_frb_namespace}. Specify overwrite=False in put()."  # noqa
                )
            raise

    def get(
        self,
        source_file,
        destination_file,
        namespace=chime_frb_namespace,
        num_processors=1,
    ):
        """Retrieve a file, stored on the CANFAR file server, and copy it locally.

        Supports a source_file [list or numpy.ndarray],
        destination_file [list or numpy.ndarray], and running in parallel.
        Assumes a 1-to-1 mapping between the names in source_file and
        destination_file, if a list or numpy.ndarray is provided.
        """
        try:
            if not isinstance(source_file, (list, numpy.ndarray)) and not isinstance(
                destination_file, (list, numpy.ndarray)
            ):
                source_uri = namespace + "/" + source_file
                self.storageClient.cadcget(source_uri, destination_file)
                log.debug(
                    f"[GET ✔] Source file {source_file} downloaded from {namespace} and saved locally to {destination_file}."  # noqa
                )
            elif (
                isinstance(source_file, (list, numpy.ndarray))
                and isinstance(destination_file, (list, numpy.ndarray))
                and len(source_file) == len(destination_file)
            ):
                for ibatch in range(0, int(len(source_file) / num_processors)):
                    threads = []
                    for iprocess in range(0, num_processors):
                        ifile1 = iprocess + (ibatch * num_processors)
                        source_uri = namespace + "/" + source_file[ifile1]
                        t = Process(
                            target=self.storageClient.cadcget,
                            args=(source_uri, destination_file[ifile1]),
                        )
                        threads.append(t)
                        log.debug(
                            f"[GET ✔] Source file {source_file[ifile1]} downloaded from {namespace} and saved locally to {destination_file[ifile1]}."  # noqa
                        )
                    for job in threads:
                        job.start()
                    for job in threads:
                        job.join()
                if len(source_file) % num_processors:
                    threads = []
                    for ifile2 in range(ifile1 + 1, len(source_file)):
                        source_uri = namespace + "/" + source_file[ifile2]
                        t = Process(
                            target=self.storageClient.cadcget,
                            args=(source_uri, destination_file[ifile2]),
                        )
                        threads.append(t)
                        log.debug(
                            f"[GET ✔] Source file {source_file[ifile2]} downloaded from {namespace} and saved locally to {destination_file[ifile2]}."  # noqa
                        )
                    for job in threads:
                        job.start()
                    for job in threads:
                        job.join()
            else:
                log.debug("[ERROR ✘] len(source_file) != len(destination_file).")
        except cadcutils.exceptions.NotFoundException:
            log.debug(
                f"[ERROR ✘] Source file {source_file} does not exist on {namespace}."
            )
            raise

    def delete(self, filename, namespace=chime_frb_namespace, num_processors=1):
        """Delete a file from the CANFAR file server.

        Supports a filename [list or numpy.ndarray] and running in parallel.
        """
        try:
            if not isinstance(filename, (list, numpy.ndarray)):
                file_uri = namespace + "/" + filename
                self.storageClient.cadcremove(file_uri)
                log.debug(f"[DELETE ✔] File {filename} deleted from {namespace}.")
            elif isinstance(filename, (list, numpy.ndarray)):
                for ibatch in range(0, int(len(filename) / num_processors)):
                    threads = []
                    for iprocess in range(0, num_processors):
                        ifile1 = iprocess + (ibatch * num_processors)
                        file_uri = namespace + "/" + filename[ifile1]
                        t = Process(
                            target=self.storageClient.cadcremove, args=(file_uri,)
                        )
                        threads.append(t)
                        log.debug(
                            f"[DELETE ✔] File {filename[ifile1]} deleted from {namespace}."  # noqa
                        )
                    for job in threads:
                        job.start()
                    for job in threads:
                        job.join()
                if len(filename) % num_processors:
                    threads = []
                    for ifile2 in range(ifile1 + 1, len(filename)):
                        file_uri = namespace + "/" + filename[ifile2]
                        t = Process(
                            target=self.storageClient.cadcremove, args=(file_uri,)
                        )
                        threads.append(t)
                        log.debug(
                            f"[DELETE ✔] File {filename[ifile2]} deleted from {namespace}."  # noqa
                        )
                    for job in threads:
                        job.start()
                    for job in threads:
                        job.join()
        except cadcutils.exceptions.HttpException:
            log.debug(f"[ERROR ✘] {filename} does not exist on {namespace}.")
            raise

    def info(self, file, namespace=chime_frb_namespace):
        """Query the CANFAR file server and retrieve information about a specific file, if it exists."""  # noqa
        file_uri = namespace + "/" + file
        try:
            log.debug(f"[INFO ✔] Getting info. for file {file} on {namespace}.")
            file_info = self.storageClient.cadcinfo(file_uri)
            # Parse the info. that is returned by CANFAR and return them as variables.
            file_id = vars(file_info)["id"]  # String
            file_name = vars(file_info)["name"]  # String
            file_size = vars(file_info)["size"]  # String
            file_type = vars(file_info)["file_type"]  # String
            file_encoding = vars(file_info)["encoding"]  # String
            file_last_modified = vars(file_info)["lastmod"]  # Datetime object
            file_md5sum = vars(file_info)["md5sum"]  # String
            return (
                file_id,
                file_name,
                file_size,
                file_type,
                file_encoding,
                file_last_modified,
                file_md5sum,
            )
        except cadcutils.exceptions.NotFoundException:
            log.debug(f"[ERROR ✘] {file} does not exist on {namespace}.")
            raise

    def query(
        self,
        query_directory="",
        namespace=chime_frb_namespace,
        output_file=None,
        format_type="tsv",
        tmptable=None,
        timeout_value=10,
        quiet=False,
    ):
        """Query the CANFAR file server and retrieve information about all files in a specific path."""  # noqa
        # Pythonic way of running the command-line tool analogous to:
        # cadc-tap query -s uvic/luskan "select * from inventory.Artifact where uri like 'cadc:CHIMEFRB%'" # noqa
        # query_string = "select * from inventory.Artifact where uri like \'" + namespace + "%\'" # noqa
        query_string = (
            "select * from inventory.Artifact where uri like '"
            + namespace
            + "/"
            + query_directory
            + "%'"
        )
        log.debug(f"[QUERY ✔] Querying files in {namespace}/{query_directory}")
        old_stdout = sys.stdout
        new_stdout = io.StringIO()
        sys.stdout = new_stdout
        self.queryClient.query(
            query_string,
            output_file,
            format_type,
            tmptable,
            timeout=timeout_value,
            no_column_names=quiet,
        )
        query_output = new_stdout.getvalue()
        sys.stdout = old_stdout
        query_output_lines = query_output.splitlines()
        uri = []
        uriBucket = []
        contentChecksum = []
        contentLastModified = []
        contentLength = []
        contentType = []
        contentEncoding = []
        lastModified = []
        metaChecksum = []
        id = []
        if len(query_output_lines) > 4:
            for idx in range(2, len(query_output_lines) - 2):
                file_info = query_output_lines[idx].split("\t")
                uri.append(file_info[0])
                uriBucket.append(file_info[1])
                contentChecksum.append(file_info[2])
                contentLastModified.append(file_info[3])
                contentLength.append(file_info[4])
                contentType.append(file_info[5])
                contentEncoding.append(file_info[6])
                lastModified.append(file_info[7])
                metaChecksum.append(file_info[8])
                id.append(file_info[9])

        return (
            uri,
            uriBucket,
            contentChecksum,
            contentLastModified,
            contentLength,
            contentType,
            contentEncoding,
            lastModified,
            metaChecksum,
            id,
        )

    def disk_usage(
        self,
        query_directory="",
        namespace=chime_frb_namespace,
        output_file=None,
        format_type="tsv",
        tmptable=None,
        timeout_value=10,
        quiet=False,
    ):
        """Check the amount of disk space used up by the files."""
        query_string = "select sum(contentLength/1024.0/1024.0/1024.0) as numGB from inventory.Artifact where uri like 'cadc:CHIMEFRB/%'"  # noqa
        old_stdout = sys.stdout
        new_stdout = io.StringIO()
        sys.stdout = new_stdout
        self.queryClient.query(
            query_string,
            output_file,
            format_type,
            tmptable,
            timeout=timeout_value,
            no_column_names=quiet,
        )
        query_output = new_stdout.getvalue()
        sys.stdout = old_stdout
        query_output_lines = query_output.splitlines()
        print(query_output_lines)

    def exist(self, file, namespace=chime_frb_namespace):
        """Check if the file exists on the CANFAR file server."""
        file_uri = namespace + "/" + file
        log.debug(f"[EXIST ✔] Checking if file {file} exists on {namespace}.")
        existFlag = "ERROR"
        try:
            self.storageClient.cadcinfo(file_uri)
            existFlag = True
        except cadcutils.exceptions.NotFoundException:
            existFlag = False
        return existFlag

    def mkdir(self):
        """Create a directory on the CANFAR file server."""
        # No notion of directories. Encoded in the file uri.

    def rename(self, source_file, destination_file):
        """Move a file on the CANFAR file server to a different location."""
        # Cannot rename a file uri on CANFAR.

    def copy(self, source_file, destination_file):
        """Copy a file to a different location on the CANFAR file server."""
        # Cannot copy a file uri to a different uri on CANFAR.

    def chmod(self, node, mode):
        """Change global permissions of the file on the CANFAR file server."""
        # Cannot change the permissions of an individual file on CANFAR.

    def make_writable_by_chime_frb_admin(self, node):
        """Make a file writable by the chime frb admin group on the CANFAR file server."""  # noqa
        # Cannot change the permissions of an individual file to be writable by the chime frb admin group on CANFAR. # noqa

    def make_writable_by_chime_frb(self, node):
        """Make a file writable by the chime frb group on the CANFAR file server."""  # noqa
        # Cannot change the permissions of an individual file to be writable by the chime frb group on CANFAR. # noqa
