"""Datatrail dataset verification command."""

import json
from typing import Any, Dict, List, Optional, Set, Tuple

import click

from dtcli.src import functions
from dtcli.utilities import cadcclient

NAMESPACE = "cadc:CHIMEFRB"
QUERY_BATCH_SIZE = 100
RESULT_CATEGORIES = (
    "present",
    "missing",
    "size_mismatch",
    "checksum_mismatch",
    "unavailable",
)


def _normalise_uri(path: str) -> str:
    """Return a full CADC URI."""
    path = path.replace("//", "/").lstrip("/")
    prefix = NAMESPACE + "/"
    if path.startswith(prefix):
        return path
    return prefix + path


def _relative_path(uri: str) -> str:
    """Return the path below the CADC namespace."""
    start = len(NAMESPACE) + 1
    return _normalise_uri(uri)[start:]


def _checksum(value: Any) -> Optional[str]:
    """Normalise an MD5 checksum."""
    if value is None:
        return None
    checksum = str(value).strip().lower()
    if checksum.startswith("md5:"):
        checksum = checksum[4:]
    return checksum or None


def _size(value: Any) -> Optional[int]:
    """Convert a size value to bytes."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _minoc_metadata(
    uris: List[str],
) -> Tuple[Dict[str, Dict[str, Any]], Set[str]]:
    """Read object metadata from Minoc."""
    if not uris:
        return {}, set()
    try:
        response = cadcclient.info([_relative_path(uri) for uri in uris])
    except Exception:
        return {}, set(uris)

    metadata: Dict[str, Dict[str, Any]] = {}
    for item in response:
        item_uri = item.get("id")
        if isinstance(item_uri, str):
            metadata[_normalise_uri(item_uri)] = {
                "size": _size(item.get("size")),
                "checksum": _checksum(item.get("md5sum")),
            }
    return metadata, set()


def _inventory_metadata(
    uris: List[str],
) -> Tuple[Dict[str, Dict[str, Any]], Set[str]]:
    """Read object metadata from Luskan."""
    metadata: Dict[str, Dict[str, Any]] = {}
    unavailable: Set[str] = set()
    for offset in range(0, len(uris), QUERY_BATCH_SIZE):
        end = offset + QUERY_BATCH_SIZE
        batch = uris[offset:end]
        quoted = ",".join("'" + uri.replace("'", "''") + "'" for uri in batch)
        query = (
            "select uri,contentLength,contentChecksum "
            "from inventory.Artifact where uri in (" + quoted + ")"
        )
        try:
            rows = cadcclient.query(query)
        except Exception:
            unavailable.update(batch)
            continue
        batch_set = set(batch)
        for row in rows:
            if len(row) < 3 or not row[0]:
                continue
            uri = _normalise_uri(str(row[0]))
            if uri in batch_set:
                metadata[uri] = {
                    "size": _size(row[1]),
                    "checksum": _checksum(row[2]),
                }
    return metadata, unavailable


def _empty_report(scope: str, dataset: str) -> Dict[str, Any]:
    """Create an empty verification report."""
    return {
        "scope": scope,
        "dataset": dataset,
        "registered": 0,
        "ok": False,
        "summary": {category: 0 for category in RESULT_CATEGORIES},
        "results": {category: [] for category in RESULT_CATEGORIES},
    }


def verify_dataset(scope: str, dataset: str) -> Dict[str, Any]:
    """Compare registered files with Minoc and Luskan metadata."""
    report = _empty_report(scope, dataset)
    results = report["results"]
    try:
        dataset_info = functions.get_dataset_file_info(scope, dataset)
    except Exception:
        dataset_info = None
    if not isinstance(dataset_info, dict) or dataset_info.get("error"):
        results["unavailable"].append(
            {
                "uri": None,
                "services": ["datatrail"],
                "reason": "Dataset information is unavailable.",
            }
        )
        _finish_report(report)
        return report

    locations = dataset_info.get("file_replica_locations")
    if not isinstance(locations, dict):
        results["unavailable"].append(
            {
                "uri": None,
                "services": ["datatrail"],
                "reason": "Dataset file information is invalid.",
            }
        )
        _finish_report(report)
        return report
    minoc_files = locations.get("minoc", [])
    if not isinstance(minoc_files, list) or not all(
        isinstance(path, str) for path in minoc_files
    ):
        results["unavailable"].append(
            {
                "uri": None,
                "services": ["datatrail"],
                "reason": "Registered Minoc files are invalid.",
            }
        )
        _finish_report(report)
        return report

    uris = sorted({_normalise_uri(path) for path in minoc_files})
    report["registered"] = len(uris)
    minoc, minoc_unavailable = _minoc_metadata(uris)
    inventory, inventory_unavailable = _inventory_metadata(uris)
    for uri in uris:
        unavailable_services = []
        if uri in minoc_unavailable:
            unavailable_services.append("minoc")
        if uri in inventory_unavailable:
            unavailable_services.append("luskan")
        if unavailable_services:
            results["unavailable"].append(
                {
                    "uri": uri,
                    "services": unavailable_services,
                    "reason": "Metadata service is unavailable.",
                }
            )
            continue

        missing_services = []
        if uri not in minoc:
            missing_services.append("minoc")
        if uri not in inventory:
            missing_services.append("luskan")
        if missing_services:
            results["missing"].append({"uri": uri, "services": missing_services})
            continue

        _compare_metadata(uri, minoc[uri], inventory[uri], results)

    _finish_report(report)
    return report


def _compare_metadata(
    uri: str,
    minoc: Dict[str, Any],
    inventory: Dict[str, Any],
    results: Dict[str, List[Dict[str, Any]]],
) -> None:
    """Add one file to its result categories."""
    incomplete = []
    incomplete_services = []
    for field in ("size", "checksum"):
        if minoc.get(field) is None:
            if "minoc" not in incomplete_services:
                incomplete_services.append("minoc")
            incomplete.append(field)
        if inventory.get(field) is None:
            if "luskan" not in incomplete_services:
                incomplete_services.append("luskan")
            if field not in incomplete:
                incomplete.append(field)
    if incomplete:
        results["unavailable"].append(
            {
                "uri": uri,
                "services": incomplete_services,
                "fields": incomplete,
                "reason": "Metadata is incomplete.",
            }
        )

    mismatch = False
    if minoc.get("size") is not None and inventory.get("size") is not None:
        if minoc["size"] != inventory["size"]:
            mismatch = True
            results["size_mismatch"].append(
                {
                    "uri": uri,
                    "minoc": minoc["size"],
                    "luskan": inventory["size"],
                }
            )
    if minoc.get("checksum") is not None and inventory.get("checksum") is not None:
        if minoc["checksum"] != inventory["checksum"]:
            mismatch = True
            results["checksum_mismatch"].append(
                {
                    "uri": uri,
                    "minoc": minoc["checksum"],
                    "luskan": inventory["checksum"],
                }
            )
    if not incomplete and not mismatch:
        results["present"].append(
            {
                "uri": uri,
                "size": minoc["size"],
                "checksum": minoc["checksum"],
            }
        )


def _finish_report(report: Dict[str, Any]) -> None:
    """Set report totals and status."""
    results = report["results"]
    report["summary"] = {
        category: len(results[category]) for category in RESULT_CATEGORIES
    }
    report["ok"] = not any(
        results[category]
        for category in (
            "missing",
            "size_mismatch",
            "checksum_mismatch",
            "unavailable",
        )
    )


def _show_report(report: Dict[str, Any]) -> None:
    """Print a concise verification report."""
    click.echo(f"{report['scope']} {report['dataset']}")
    click.echo(f"registered: {report['registered']}")
    for category in RESULT_CATEGORIES:
        label = category.replace("_", "-")
        click.echo(f"{label}: {report['summary'][category]}")
    for category in RESULT_CATEGORIES[1:]:
        for item in report["results"][category]:
            target = item.get("uri") or ",".join(item.get("services", []))
            click.echo(f"{category.replace('_', '-')}: {target}")


@click.command(name="verify", help="Verify registered Minoc files.")
@click.argument("scope", required=True, type=click.STRING, nargs=1)
@click.argument("dataset", required=True, type=click.STRING, nargs=1)
@click.option("--json", "output_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def verify(ctx: click.Context, scope: str, dataset: str, output_json: bool) -> None:
    """Verify registered Minoc files against CADC metadata."""
    report = verify_dataset(scope, dataset)
    if output_json:
        click.echo(json.dumps(report, indent=2))
    else:
        _show_report(report)
    if not report["ok"]:
        ctx.exit(2 if report["results"]["unavailable"] else 1)
