"""Datatrail Inventory Command."""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import click

from dtcli.src import functions

SCHEMA = "datatrail.inventory/v1"
FINISHED_STATUSES = {"ready", "empty"}
ENTRY_STATUSES = FINISHED_STATUSES | {"pending", "failed"}


@click.command(name="inventory", help="Build a resumable dataset file inventory.")
@click.argument("scope", required=False, type=click.STRING)
@click.option(
    "--match",
    type=click.STRING,
    default=None,
    help="Comma-separated terms a larger dataset must all contain.",
)
@click.option(
    "--parent",
    type=click.STRING,
    default=None,
    help="Start at this dataset within SCOPE.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(
        file_okay=True,
        dir_okay=False,
        writable=True,
        resolve_path=True,
        path_type=Path,
    ),
    default=Path("datatrail-inventory.json"),
    show_default=True,
    help="Manifest path.",
)
@click.option(
    "--allow-incomplete",
    is_flag=True,
    help="Exit successfully while unresolved entries remain.",
)
@click.option("-v", "--verbose", count=True, help="Verbosity: v=INFO, vv=DEBUG.")
@click.option("-q", "--quiet", is_flag=True, help="Only errors shown in logs.")
@click.pass_context
def inventory(
    ctx: click.Context,
    scope: Optional[str],
    match: Optional[str],
    parent: Optional[str],
    output: Path,
    allow_incomplete: bool,
    verbose: int,
    quiet: bool,
) -> None:
    """Build a durable inventory of dataset replica URIs.

    Args:
        ctx (click.Context): Click context.
        scope (Optional[str]): Scope to inventory.
        match (Optional[str]): Terms used to select larger datasets.
        parent (Optional[str]): Dataset where traversal starts.
        output (Path): Manifest path.
        allow_incomplete (bool): Exit zero with unresolved entries.
        verbose (int): Verbosity level.
        quiet (bool): Minimal logging.
    """
    try:
        manifest = build_inventory(
            scope=scope,
            match=match,
            parent=parent,
            output=output,
            verbose=verbose,
            quiet=quiet,
        )
    except (OSError, ValueError) as error:
        raise click.ClickException(str(error)) from error

    ready = sum(entry["status"] == "ready" for entry in manifest["datasets"])
    empty = sum(entry["status"] == "empty" for entry in manifest["datasets"])
    files = sum(len(entry["replicas"]) for entry in manifest["datasets"])
    click.echo(f"Wrote {output}: {ready} ready, {empty} empty, {files} replica URIs.")
    if not manifest["complete"]:
        unresolved = sum(
            entry["status"] not in FINISHED_STATUSES for entry in manifest["datasets"]
        )
        discovery = len(manifest["discovery_failures"])
        click.echo(
            f"Inventory incomplete: {unresolved} dataset entries and "
            f"{discovery} discovery branches unresolved.",
            err=True,
        )
        if not allow_incomplete:
            ctx.exit(1)


def build_inventory(
    scope: Optional[str],
    match: Optional[str],
    parent: Optional[str],
    output: Path,
    verbose: int = 0,
    quiet: bool = False,
) -> Dict[str, Any]:
    """Build or resume an inventory manifest."""
    selection = _selection(scope, match, parent)
    manifest = _load_manifest(output, selection)
    rows, discovery_failures = _discover(selection, verbose, quiet)
    manifest["discovery_failures"] = discovery_failures
    _merge_rows(manifest, rows)
    _set_complete(manifest)
    _write_manifest(output, manifest)

    for entry in manifest["datasets"]:
        if entry["status"] in FINISHED_STATUSES:
            continue
        replacement = _inspect_dataset(entry, verbose, quiet)
        entry.clear()
        entry.update(replacement)
        _set_complete(manifest)
        _write_manifest(output, manifest)

    _set_complete(manifest)
    _write_manifest(output, manifest)
    return manifest


def _selection(
    scope: Optional[str], match: Optional[str], parent: Optional[str]
) -> Dict[str, Any]:
    """Normalize and validate the traversal boundary."""
    clean_scope = scope.strip() if scope else None
    clean_parent = parent.strip() if parent else None
    terms = sorted(
        {term.strip().lower() for term in (match or "").split(",") if term.strip()}
    )
    if match is not None and not terms:
        raise ValueError("--match must contain at least one non-empty term.")
    if clean_parent and not clean_scope:
        raise ValueError("--parent requires SCOPE.")
    if clean_parent and terms:
        raise ValueError("Use either --parent or --match, not both.")
    if not clean_scope and not terms:
        raise ValueError("Give SCOPE, --match, or SCOPE with --parent.")
    return {"scope": clean_scope, "match": terms, "parent": clean_parent}


def _discover(
    selection: Dict[str, Any], verbose: int, quiet: bool
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Discover terminal datasets within the selected boundary."""
    scope = selection["scope"]
    parent = selection["parent"]
    try:
        if parent:
            return functions._discover_descendants(
                scope, [parent], verbose=verbose, quiet=quiet
            )
        result = functions.discover_datasets(
            scope=scope,
            match=",".join(selection["match"]) or None,
            recursive=True,
            verbose=verbose,
            quiet=quiet,
        )
    except Exception as error:
        return [], [f"discovery failed: {_error_text(error)}"]
    if "error" in result:
        return [], [f"discovery failed: {_error_text(result['error'])}"]
    rows = result.get("results")
    failures = result.get("failed")
    if not isinstance(rows, list) or not isinstance(failures, list):
        return [], ["discovery failed: unexpected result shape"]
    return rows, [str(failure) for failure in failures]


def _inspect_dataset(entry: Dict[str, Any], verbose: int, quiet: bool) -> Dict[str, Any]:
    """Fetch and normalize one dataset's replica URIs."""
    context = {key: entry[key] for key in ("scope", "dataset", "parent", "path")}
    try:
        response = functions.get_dataset_file_info(
            entry["scope"], entry["dataset"], verbose=verbose, quiet=quiet
        )
        replicas = _replicas(response)
    except Exception as error:
        return {
            **context,
            "status": "failed",
            "replicas": [],
            "error": _error_text(error),
        }
    return {
        **context,
        "status": "ready" if replicas else "empty",
        "replicas": replicas,
    }


def _replicas(response: Any) -> List[Dict[str, str]]:
    """Normalize a Datatrail file response."""
    if not isinstance(response, dict):
        raise ValueError("Datatrail returned an unexpected file response.")
    if "error" in response:
        raise ValueError(_error_text(response["error"]))
    locations = response.get("file_replica_locations")
    if not isinstance(locations, dict):
        raise ValueError("Datatrail file response has no replica locations.")

    replicas: List[Dict[str, str]] = []
    for storage_element in sorted(locations):
        uris = locations[storage_element]
        if not isinstance(storage_element, str) or not storage_element.strip():
            raise ValueError("Datatrail returned an invalid storage element.")
        if not isinstance(uris, list) or any(
            not isinstance(uri, str) or not uri.strip() for uri in uris
        ):
            raise ValueError(
                f"Datatrail returned invalid replica URIs for {storage_element}."
            )
        replicas.extend(
            {"storage_element": storage_element, "uri": uri} for uri in sorted(set(uris))
        )
    return replicas


def _load_manifest(path: Path, selection: Dict[str, Any]) -> Dict[str, Any]:
    """Load a compatible manifest or create a new one."""
    if not path.exists():
        return {
            "schema": SCHEMA,
            "selection": selection,
            "complete": False,
            "discovery_failures": [],
            "datasets": [],
        }
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Cannot read inventory manifest {path}: {error}") from error
    if not isinstance(manifest, dict) or manifest.get("schema") != SCHEMA:
        raise ValueError(f"Unsupported inventory manifest schema in {path}.")
    if manifest.get("selection") != selection:
        raise ValueError(f"Inventory selection does not match {path}.")
    datasets = manifest.get("datasets")
    if not isinstance(datasets, list):
        raise ValueError(f"Inventory manifest datasets are invalid in {path}.")
    _validate_entries(datasets, path)
    manifest["discovery_failures"] = []
    manifest["complete"] = False
    return manifest


def _validate_entries(entries: List[Any], path: Path) -> None:
    """Validate resumable dataset entries."""
    seen = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError(f"Inventory manifest contains an invalid entry in {path}.")
        key = (entry.get("scope"), entry.get("dataset"))
        if (
            not all(isinstance(value, str) and value for value in key)
            or key in seen
            or not _valid_entry(entry)
        ):
            raise ValueError(f"Inventory manifest contains an invalid entry in {path}.")
        seen.add(key)


def _valid_entry(entry: Dict[str, Any]) -> bool:
    """Check one saved dataset entry."""
    dataset = entry["dataset"]
    parent = entry.get("parent")
    path = entry.get("path")
    replicas = entry.get("replicas")
    status = entry.get("status")
    if (
        status not in ENTRY_STATUSES
        or not isinstance(path, list)
        or not path
        or any(not isinstance(part, str) or not part for part in path)
        or path[-1] != dataset
        or (parent is not None and (not isinstance(parent, str) or not parent))
        or parent != (path[-2] if len(path) > 1 else None)
        or not isinstance(replicas, list)
        or any(not _valid_replica(replica) for replica in replicas)
    ):
        return False
    if status == "ready":
        return bool(replicas)
    if replicas:
        return False
    return status != "failed" or (
        isinstance(entry.get("error"), str) and bool(entry["error"])
    )


def _valid_replica(replica: Any) -> bool:
    """Check one saved replica row."""
    return (
        isinstance(replica, dict)
        and isinstance(replica.get("storage_element"), str)
        and bool(replica["storage_element"])
        and isinstance(replica.get("uri"), str)
        and bool(replica["uri"])
    )


def _merge_rows(manifest: Dict[str, Any], rows: List[Dict[str, Any]]) -> None:
    """Add newly discovered datasets without resetting finished entries."""
    by_key = {
        (entry["scope"], entry["dataset"]): entry for entry in manifest["datasets"]
    }
    for row in rows:
        context = _row_context(row)
        key = (context["scope"], context["dataset"])
        if key in by_key:
            by_key[key]["parent"] = context["parent"]
            by_key[key]["path"] = context["path"]
            continue
        entry = {**context, "status": "pending", "replicas": []}
        manifest["datasets"].append(entry)
        by_key[key] = entry
    _sort_entries(manifest)


def _row_context(row: Dict[str, Any]) -> Dict[str, Any]:
    """Validate a recursive discovery row."""
    if not isinstance(row, dict):
        raise ValueError("Recursive discovery returned an invalid dataset row.")
    scope = row.get("scope")
    dataset = row.get("dataset")
    parent = row.get("parent")
    path = row.get("path")
    if (
        not isinstance(scope, str)
        or not scope
        or not isinstance(dataset, str)
        or not dataset
        or (parent is not None and (not isinstance(parent, str) or not parent))
        or not isinstance(path, list)
        or not path
        or any(not isinstance(part, str) or not part for part in path)
        or path[-1] != dataset
        or parent != (path[-2] if len(path) > 1 else None)
    ):
        raise ValueError("Recursive discovery returned an invalid dataset row.")
    return {"scope": scope, "dataset": dataset, "parent": parent, "path": path}


def _set_complete(manifest: Dict[str, Any]) -> None:
    """Update the manifest completion flag."""
    manifest["complete"] = not manifest["discovery_failures"] and all(
        entry["status"] in FINISHED_STATUSES for entry in manifest["datasets"]
    )


def _sort_entries(manifest: Dict[str, Any]) -> None:
    """Keep manifest output deterministic."""
    manifest["datasets"].sort(
        key=lambda entry: (
            entry["scope"],
            tuple(entry["path"]),
            entry["dataset"],
        )
    )


def _write_manifest(path: Path, manifest: Dict[str, Any]) -> None:
    """Atomically write the manifest beside its temporary file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    _sort_entries(manifest)
    descriptor, temporary = tempfile.mkstemp(
        dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(manifest, handle, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _error_text(error: Any) -> str:
    """Return a useful error string."""
    text = str(error).strip()
    return text if text else type(error).__name__
