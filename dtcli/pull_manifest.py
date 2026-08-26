"""Download files from an inventory manifest."""

import json
import os
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Optional, Tuple

import click

from dtcli.config import procure
from dtcli.utilities import cadcclient

INVENTORY_SCHEMA = "datatrail.inventory/v1"
STATE_SCHEMA = "datatrail.pull/v1"
MINOC_PREFIX = "cadc:CHIMEFRB/"
FILE_STATUSES = {"pending", "complete", "failed"}
INVENTORY_STATUSES = {"pending", "ready", "empty", "failed"}


@click.command(name="pull-manifest", help="Download files from an inventory manifest.")
@click.argument(
    "manifest",
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
        path_type=Path,
    ),
)
@click.option(
    "--directory",
    "-d",
    type=click.Path(
        file_okay=False,
        dir_okay=True,
        writable=True,
        resolve_path=True,
        path_type=Path,
    ),
    default=None,
    help="Directory to pull data to.",
)
@click.option(
    "--state",
    type=click.Path(
        file_okay=True,
        dir_okay=False,
        writable=True,
        resolve_path=True,
        path_type=Path,
    ),
    default=None,
    help="Transfer state path.",
)
@click.option(
    "--cores",
    "-c",
    type=click.IntRange(min=1, max=os.cpu_count() or 1),
    default=1,
    show_default=True,
    help="Maximum parallel transfers.",
)
@click.option("-v", "--verbose", count=True, help="Verbosity: v=INFO, vv=DEBUG.")
@click.option("--force", "-f", is_flag=True, help="Do not prompt for confirmation.")
@click.pass_context
def pull_manifest(
    ctx: click.Context,
    manifest: Path,
    directory: Optional[Path],
    state: Optional[Path],
    cores: int,
    verbose: int,
    force: bool,
) -> None:
    """Download the Minoc files listed in an inventory manifest."""
    try:
        directory = directory or _default_directory()
        state = state or manifest.with_name(f"{manifest.stem}.pull.json")
        transfer = prepare_transfer(manifest, directory, state)
    except (OSError, ValueError, KeyError) as error:
        raise click.ClickException(str(error)) from error

    pending = sum(entry["status"] != "complete" for entry in transfer["files"])
    if pending and not force:
        click.confirm(f"Download {pending} files?", abort=True)

    if pending:
        run_transfer(transfer, state, cores=cores, verbose=verbose)

    completed = sum(entry["status"] == "complete" for entry in transfer["files"])
    failed = sum(entry["status"] == "failed" for entry in transfer["files"])
    click.echo(f"Transfer state {state}: {completed} complete, {failed} failed.")
    if not transfer["complete"]:
        if transfer["unavailable_datasets"]:
            click.echo(
                f"No Minoc files for {len(transfer['unavailable_datasets'])} datasets.",
                err=True,
            )
        if not transfer["inventory_complete"]:
            click.echo("The inventory is incomplete.", err=True)
        ctx.exit(1)


def prepare_transfer(
    manifest_path: Path, directory: Path, state_path: Path
) -> Dict[str, Any]:
    """Load an inventory and prepare resumable transfer state."""
    manifest_path = manifest_path.resolve()
    directory = directory.resolve()
    state_path = state_path.resolve()
    if manifest_path == state_path:
        raise ValueError("The inventory and transfer state paths must differ.")
    directory.mkdir(parents=True, exist_ok=True)

    inventory = _read_json(manifest_path, "inventory manifest")
    files, unavailable = _inventory_files(inventory)
    previous = _load_state(state_path, manifest_path, directory)
    previous_files = {entry["uri"]: entry for entry in previous.get("files", [])}

    entries = []
    for uri, relative in files:
        destination = _destination(directory, relative)
        old = previous_files.get(uri)
        if old and old["path"] != relative:
            raise ValueError(f"Transfer path changed for {uri}.")
        entries.append(_resume_entry(uri, relative, destination, old))

    transfer = {
        "schema": STATE_SCHEMA,
        "inventory": str(manifest_path),
        "directory": str(directory),
        "inventory_complete": inventory.get("complete") is True,
        "unavailable_datasets": unavailable,
        "complete": False,
        "files": entries,
    }
    _set_complete(transfer)
    _write_json(state_path, transfer)
    return transfer


def run_transfer(
    transfer: Dict[str, Any], state_path: Path, cores: int, verbose: int = 0
) -> Dict[str, Any]:
    """Download pending files and checkpoint each bounded batch."""
    directory = Path(transfer["directory"])
    pending = [entry for entry in transfer["files"] if entry["status"] != "complete"]
    for offset in range(0, len(pending), cores):
        batch = pending[offset : offset + cores]  # noqa: E203
        for entry in batch:
            entry["status"] = "pending"
            entry.pop("error", None)
            entry.pop("bytes", None)
        _set_complete(transfer)
        _write_json(state_path, transfer)

        sources = [entry["path"] for entry in batch]
        destinations = [str(_destination(directory, path)) for path in sources]
        for destination in destinations:
            Path(destination).parent.mkdir(parents=True, exist_ok=True)
        failures = cadcclient.pget(
            source=sources,
            destination=destinations,
            processors=cores,
            verbose=verbose,
        )
        failed_by_source = {failure["source"]: failure for failure in failures}
        for entry, destination in zip(batch, destinations):
            failure = failed_by_source.get(entry["path"])
            if failure:
                entry["status"] = "failed"
                entry["error"] = failure["error"]
                continue
            destination_path = Path(destination)
            if not destination_path.is_file():
                entry["status"] = "failed"
                entry["error"] = "download did not create the destination file"
                continue
            entry["status"] = "complete"
            entry["bytes"] = destination_path.stat().st_size
            entry.pop("error", None)
        _set_complete(transfer)
        _write_json(state_path, transfer)
    return transfer


def _default_directory() -> Path:
    """Return the configured local root."""
    config = procure()
    site = config["site"]
    return Path(config["root_mounts"][site])


def _inventory_files(
    inventory: Dict[str, Any]
) -> Tuple[List[Tuple[str, str]], List[Dict[str, str]]]:
    """Return unique Minoc files and datasets without Minoc replicas."""
    if inventory.get("schema") != INVENTORY_SCHEMA:
        raise ValueError("Unsupported inventory manifest schema.")
    if not isinstance(inventory.get("complete"), bool):
        raise ValueError("Inventory completion status is invalid.")
    datasets = inventory.get("datasets")
    if not isinstance(datasets, list):
        raise ValueError("Inventory datasets are invalid.")

    files: Dict[str, str] = {}
    unavailable = []
    for dataset in datasets:
        minoc, unavailable_dataset = _dataset_files(dataset)
        for uri, relative in minoc:
            files[uri] = relative
        if unavailable_dataset:
            unavailable.append(unavailable_dataset)
    return sorted(files.items()), sorted(
        unavailable, key=lambda item: (item["scope"], item["dataset"])
    )


def _dataset_files(
    dataset: Any,
) -> Tuple[List[Tuple[str, str]], Optional[Dict[str, str]]]:
    """Return one ready dataset's Minoc files."""
    if not isinstance(dataset, dict):
        raise ValueError("Inventory contains an invalid dataset entry.")
    status = dataset.get("status")
    if status not in INVENTORY_STATUSES:
        raise ValueError("Inventory contains an invalid dataset status.")
    if status != "ready":
        return [], None
    replicas = dataset.get("replicas")
    if not isinstance(replicas, list):
        raise ValueError("Inventory contains invalid replicas.")

    minoc = []
    for replica in replicas:
        if not isinstance(replica, dict):
            raise ValueError("Inventory contains an invalid replica.")
        storage_element = replica.get("storage_element")
        if not isinstance(storage_element, str):
            raise ValueError("Inventory contains an invalid storage element.")
        if storage_element.lower() != "minoc":
            continue
        uri = replica.get("uri")
        if not isinstance(uri, str):
            raise ValueError("Inventory contains an invalid Minoc URI.")
        minoc.append((uri, _relative_path(uri)))
    if minoc:
        return minoc, None

    scope = dataset.get("scope")
    name = dataset.get("dataset")
    if not isinstance(scope, str) or not isinstance(name, str):
        raise ValueError("Inventory contains an invalid dataset name.")
    return [], {"scope": scope, "dataset": name}


def _relative_path(uri: str) -> str:
    """Convert a Minoc URI to a safe relative path."""
    if not uri.startswith(MINOC_PREFIX):
        raise ValueError(f"Unsupported Minoc URI: {uri}")
    relative = uri[len(MINOC_PREFIX) :]  # noqa: E203
    parts = relative.split("/")
    pure = PurePosixPath(relative)
    if (
        not relative
        or relative.startswith("/")
        or "\\" in relative
        or any(part in {"", ".", ".."} for part in parts)
    ):
        raise ValueError(f"Unsafe Minoc URI: {uri}")
    return pure.as_posix()


def _destination(directory: Path, relative: str) -> Path:
    """Keep a destination within its requested directory."""
    destination = directory.joinpath(*PurePosixPath(relative).parts)
    if os.path.commonpath((str(directory), str(destination.resolve()))) != str(
        directory
    ):
        raise ValueError(f"Transfer path escapes the destination: {relative}")
    return destination


def _load_state(
    state_path: Path, manifest_path: Path, directory: Path
) -> Dict[str, Any]:
    """Load compatible transfer state when it exists."""
    if not state_path.exists():
        return {"files": []}
    state = _read_json(state_path, "transfer state")
    if state.get("schema") != STATE_SCHEMA:
        raise ValueError(f"Unsupported transfer state schema in {state_path}.")
    if state.get("inventory") != str(manifest_path):
        raise ValueError(f"Transfer state inventory does not match {state_path}.")
    if state.get("directory") != str(directory):
        raise ValueError(f"Transfer state directory does not match {state_path}.")
    files = state.get("files")
    if not isinstance(files, list):
        raise ValueError(f"Transfer state files are invalid in {state_path}.")
    seen = set()
    for entry in files:
        if (
            not isinstance(entry, dict)
            or not isinstance(entry.get("uri"), str)
            or not isinstance(entry.get("path"), str)
            or entry.get("status") not in FILE_STATUSES
            or entry["uri"] in seen
        ):
            raise ValueError(f"Transfer state contains an invalid file in {state_path}.")
        seen.add(entry["uri"])
    return state


def _resume_entry(
    uri: str, relative: str, destination: Path, old: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Reuse a completed file only when its recorded size still matches."""
    if old and old["status"] == "complete":
        size = old.get("bytes")
        if (
            isinstance(size, int)
            and not isinstance(size, bool)
            and size >= 0
            and destination.is_file()
            and destination.stat().st_size == size
        ):
            return {"uri": uri, "path": relative, "status": "complete", "bytes": size}
    return {"uri": uri, "path": relative, "status": "pending"}


def _set_complete(transfer: Dict[str, Any]) -> None:
    """Update the transfer completion flag."""
    transfer["complete"] = (
        transfer["inventory_complete"]
        and not transfer["unavailable_datasets"]
        and all(entry["status"] == "complete" for entry in transfer["files"])
    )


def _read_json(path: Path, label: str) -> Dict[str, Any]:
    """Read a JSON object."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Cannot read {label} {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"The {label} {path} is invalid.")
    return value


def _write_json(path: Path, value: Dict[str, Any]) -> None:
    """Atomically write JSON state."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise
