"""Tests for manifest-driven downloads."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from dtcli import pull_manifest as pull_manifest_module
from dtcli.cli import cli as datatrail


def write_inventory(path: Path, files, complete: bool = True) -> None:
    """Write a small inventory manifest."""
    replicas = [
        {"storage_element": "minoc", "uri": f"cadc:CHIMEFRB/{name}"} for name in files
    ]
    path.write_text(
        json.dumps(
            {
                "schema": "datatrail.inventory/v1",
                "complete": complete,
                "datasets": [
                    {
                        "scope": "test.scope",
                        "dataset": "test-dataset",
                        "status": "ready",
                        "replicas": replicas,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def test_transfer_resumes_only_failed_files(tmp_path: Path, monkeypatch) -> None:
    """A rerun keeps completed files and retries failures."""
    manifest = tmp_path / "inventory.json"
    state = tmp_path / "pull.json"
    destination = tmp_path / "data"
    write_inventory(manifest, ["first.dat", "second.dat"])
    calls = []

    def first_attempt(source, destination, processors, verbose):
        calls.append((source, processors))
        Path(destination[0]).write_bytes(b"first")
        return [
            {
                "source": "second.dat",
                "destination": destination[1],
                "error": "service unavailable",
            }
        ]

    monkeypatch.setattr(pull_manifest_module.cadcclient, "pget", first_attempt)
    transfer = pull_manifest_module.prepare_transfer(manifest, destination, state)
    pull_manifest_module.run_transfer(transfer, state, cores=2)

    assert transfer["complete"] is False
    assert [entry["status"] for entry in transfer["files"]] == [
        "complete",
        "failed",
    ]
    assert json.loads(state.read_text()) == transfer

    def second_attempt(source, destination, processors, verbose):
        calls.append((source, processors))
        assert source == ["second.dat"]
        Path(destination[0]).write_bytes(b"second")
        return []

    monkeypatch.setattr(pull_manifest_module.cadcclient, "pget", second_attempt)
    resumed = pull_manifest_module.prepare_transfer(manifest, destination, state)
    pull_manifest_module.run_transfer(resumed, state, cores=2)

    assert resumed["complete"] is True
    assert [entry["status"] for entry in resumed["files"]] == [
        "complete",
        "complete",
    ]
    assert calls == [(["first.dat", "second.dat"], 2), (["second.dat"], 2)]


def test_missing_completed_file_is_downloaded_again(tmp_path: Path, monkeypatch) -> None:
    """A missing destination invalidates its completed state."""
    manifest = tmp_path / "inventory.json"
    state = tmp_path / "pull.json"
    destination = tmp_path / "data"
    write_inventory(manifest, ["file.dat"])

    def download(source, destination, processors, verbose):
        Path(destination[0]).write_bytes(b"contents")
        return []

    monkeypatch.setattr(pull_manifest_module.cadcclient, "pget", download)
    transfer = pull_manifest_module.prepare_transfer(manifest, destination, state)
    pull_manifest_module.run_transfer(transfer, state, cores=1)
    (destination / "file.dat").unlink()

    resumed = pull_manifest_module.prepare_transfer(manifest, destination, state)

    assert resumed["files"][0]["status"] == "pending"
    assert resumed["complete"] is False


def test_interruption_keeps_previous_checkpoint(tmp_path: Path, monkeypatch) -> None:
    """An interruption keeps earlier batches completed."""
    manifest = tmp_path / "inventory.json"
    state = tmp_path / "pull.json"
    destination = tmp_path / "data"
    write_inventory(manifest, ["first.dat", "second.dat"])
    attempts = 0

    def download(source, destination, processors, verbose):
        nonlocal attempts
        attempts += 1
        if attempts == 2:
            raise KeyboardInterrupt
        Path(destination[0]).write_bytes(b"first")
        return []

    monkeypatch.setattr(pull_manifest_module.cadcclient, "pget", download)
    transfer = pull_manifest_module.prepare_transfer(manifest, destination, state)
    with pytest.raises(KeyboardInterrupt):
        pull_manifest_module.run_transfer(transfer, state, cores=1)

    saved = json.loads(state.read_text())
    assert [entry["status"] for entry in saved["files"]] == [
        "complete",
        "pending",
    ]
    assert saved["complete"] is False


@pytest.mark.parametrize(
    "uri",
    [
        "cadc:OTHER/file.dat",
        "cadc:CHIMEFRB/../file.dat",
        "cadc:CHIMEFRB//file.dat",
        "cadc:CHIMEFRB/folder\\file.dat",
        "data/../file.dat",
        "/../file.dat",
        "//file.dat",
        "cadc:CHIMEFRB/invalid\0file.dat",
    ],
)
def test_unsafe_or_unsupported_uri_is_rejected(tmp_path: Path, uri: str) -> None:
    """Only safe paths in the expected Minoc namespace are accepted."""
    manifest = tmp_path / "inventory.json"
    manifest.write_text(
        json.dumps(
            {
                "schema": "datatrail.inventory/v1",
                "complete": True,
                "datasets": [
                    {
                        "scope": "test.scope",
                        "dataset": "test-dataset",
                        "status": "ready",
                        "replicas": [{"storage_element": "minoc", "uri": uri}],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        pull_manifest_module.prepare_transfer(
            manifest, tmp_path / "data", tmp_path / "pull.json"
        )


def test_destination_symlink_escape_is_rejected(tmp_path: Path) -> None:
    """A symlink cannot redirect a transfer outside its root."""
    manifest = tmp_path / "inventory.json"
    destination = tmp_path / "data"
    outside = tmp_path / "outside"
    destination.mkdir()
    outside.mkdir()
    (destination / "linked").symlink_to(outside, target_is_directory=True)
    write_inventory(manifest, ["linked/file.dat"])

    with pytest.raises(ValueError, match="escapes the destination"):
        pull_manifest_module.prepare_transfer(
            manifest, destination, tmp_path / "pull.json"
        )


def test_command_fails_when_inventory_is_incomplete(tmp_path: Path, monkeypatch) -> None:
    """Available files can finish without hiding an inventory gap."""
    manifest = tmp_path / "inventory.json"
    destination = tmp_path / "data"
    write_inventory(manifest, ["file.dat"], complete=False)

    def download(source, destination, processors, verbose):
        Path(destination[0]).parent.mkdir(parents=True, exist_ok=True)
        Path(destination[0]).write_bytes(b"contents")
        return []

    monkeypatch.setattr(pull_manifest_module.cadcclient, "pget", download)
    runner = CliRunner()
    result = runner.invoke(
        pull_manifest_module.pull_manifest,
        [str(manifest), "--directory", str(destination), "--force"],
    )

    assert result.exit_code == 1
    assert "The inventory is incomplete" in result.output
    assert (destination / "file.dat").read_bytes() == b"contents"


def test_dataset_without_minoc_replica_stays_incomplete(tmp_path: Path) -> None:
    """A ready dataset without Minoc files is reported in transfer state."""
    manifest = tmp_path / "inventory.json"
    manifest.write_text(
        json.dumps(
            {
                "schema": "datatrail.inventory/v1",
                "complete": True,
                "datasets": [
                    {
                        "scope": "test.scope",
                        "dataset": "archive-only",
                        "status": "ready",
                        "replicas": [
                            {"storage_element": "archive", "uri": "archive:file.dat"}
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    transfer = pull_manifest_module.prepare_transfer(
        manifest, tmp_path / "data", tmp_path / "pull.json"
    )

    assert transfer["files"] == []
    assert transfer["unavailable_datasets"] == [
        {"scope": "test.scope", "dataset": "archive-only"}
    ]
    assert transfer["complete"] is False


def test_command_is_registered() -> None:
    """The root command exposes manifest downloads."""
    result = CliRunner().invoke(datatrail, ["pull-manifest", "--help"])

    assert result.exit_code == 0
    assert "MANIFEST" in result.output
    assert "--cores" in result.output


@pytest.mark.parametrize("shared", ["state", "directory", "alias"])
def test_competing_command_cannot_change_active_transfer(
    tmp_path: Path, monkeypatch, shared: str
) -> None:
    """Shared state or a destination is rejected before preparation or download."""
    manifest = tmp_path / "inventory.json"
    directory = tmp_path / "data"
    state = tmp_path / "pull.json"
    write_inventory(manifest, ["file.dat"])
    other_directory = directory if shared != "state" else tmp_path / "other-data"
    other_state = state if shared == "state" else tmp_path / "other-pull.json"
    if shared == "alias":
        other_directory = tmp_path / "alias"
        try:
            other_directory.symlink_to(directory, target_is_directory=True)
        except OSError:
            pytest.skip("This platform does not permit creating symlinks")

    def unexpected_download(**kwargs):
        pytest.fail("A competing transfer started downloading")

    monkeypatch.setattr(pull_manifest_module.cadcclient, "pget", unexpected_download)
    with pull_manifest_module.transfer_session(manifest, directory, state):
        original = state.read_bytes()
        result = CliRunner().invoke(
            pull_manifest_module.pull_manifest,
            [
                str(manifest),
                "-d",
                str(other_directory),
                "--state",
                str(other_state),
                "-f",
            ],
        )
        assert result.exit_code == 1
        assert "already in use" in result.output
        assert state.read_bytes() == original
        if other_state != state:
            assert not other_state.exists()
        assert not (directory / "file.dat").exists()


def test_command_holds_locks_through_download_and_releases_after_interrupt(
    tmp_path: Path, monkeypatch
) -> None:
    """Interruption releases both locks and permits a resumable retry."""
    manifest = tmp_path / "inventory.json"
    directory = tmp_path / "data"
    state = tmp_path / "pull.json"
    write_inventory(manifest, ["file.dat"])

    def interrupted_download(**kwargs):
        with pytest.raises(OSError, match="already in use"):
            with pull_manifest_module.transfer_session(
                manifest, directory, tmp_path / "other.json"
            ):
                pytest.fail("The command released its destination too soon")
        raise KeyboardInterrupt

    monkeypatch.setattr(pull_manifest_module.cadcclient, "pget", interrupted_download)
    arguments = [str(manifest), "-d", str(directory), "--state", str(state), "-f"]
    result = CliRunner().invoke(pull_manifest_module.pull_manifest, arguments)
    assert result.exit_code == 1
    assert json.loads(state.read_text())["complete"] is False

    def download(source, destination, processors, verbose):
        Path(destination[0]).write_bytes(b"complete")
        return []

    monkeypatch.setattr(pull_manifest_module.cadcclient, "pget", download)
    resumed = CliRunner().invoke(pull_manifest_module.pull_manifest, arguments)
    assert resumed.exit_code == 0, resumed.output
    assert json.loads(state.read_text())["complete"] is True
    assert (directory / "file.dat").read_bytes() == b"complete"


def test_failed_second_lock_releases_first_lock(tmp_path: Path) -> None:
    """A refused session cannot strand another state or destination lock."""
    manifest = tmp_path / "inventory.json"
    directory = tmp_path / "data"
    state = tmp_path / "a-state.json"
    write_inventory(manifest, ["file.dat"])
    with pull_manifest_module.output_lock(directory / "datatrail-pull"):
        with pytest.raises(OSError, match="already in use"):
            with pull_manifest_module.transfer_session(manifest, directory, state):
                pytest.fail("A competing session acquired the destination")
        with pull_manifest_module.output_lock(state):
            assert not state.exists()


@pytest.mark.parametrize(
    "reserved",
    ["inventory.json", "pull.json", ".pull.json.lock", ".datatrail-pull.lock"],
)
def test_transfer_rejects_files_that_replace_its_metadata(tmp_path, reserved):
    """Downloads cannot overwrite their inventory, checkpoint, or active locks."""
    manifest = tmp_path / "inventory.json"
    state = tmp_path / "pull.json"
    write_inventory(manifest, [reserved])
    original = manifest.read_bytes()

    with pytest.raises(ValueError, match="control file"):
        with pull_manifest_module.transfer_session(manifest, tmp_path, state):
            pytest.fail("A download could overwrite transfer metadata")

    assert manifest.read_bytes() == original
    assert not state.exists()


def test_transfer_normalizes_legacy_minoc_paths(tmp_path):
    """Inventories produced from supported Datatrail Minoc paths remain usable."""
    manifest = tmp_path / "inventory.json"
    state = tmp_path / "pull.json"
    write_inventory(manifest, ["data/file.dat"])
    inventory = json.loads(manifest.read_text())
    inventory["datasets"][0]["replicas"].extend(
        {"storage_element": "minoc", "uri": uri}
        for uri in ["data/file.dat", "/data/file.dat"]
    )
    manifest.write_text(json.dumps(inventory))

    transfer = pull_manifest_module.prepare_transfer(manifest, tmp_path / "data", state)

    assert transfer["files"] == [
        {
            "uri": "cadc:CHIMEFRB/data/file.dat",
            "path": "data/file.dat",
            "status": "pending",
        }
    ]


def test_transfer_rejects_conflicting_destination_paths(tmp_path):
    """A file cannot also be a directory for another file in the same manifest."""
    manifest = tmp_path / "inventory.json"
    state = tmp_path / "pull.json"
    write_inventory(manifest, ["folder", "folder/file.dat"])

    with pytest.raises(ValueError, match="conflicting destination"):
        pull_manifest_module.prepare_transfer(manifest, tmp_path / "data", state)

    assert not state.exists()


def test_transfer_rejects_destinations_aliased_through_symlinks(tmp_path):
    """Distinct remote files cannot overwrite the same local path through an alias."""
    manifest = tmp_path / "inventory.json"
    state = tmp_path / "pull.json"
    destination = tmp_path / "data"
    (destination / "actual").mkdir(parents=True)
    (destination / "alias").symlink_to(destination / "actual", target_is_directory=True)
    write_inventory(manifest, ["actual/file.dat", "alias/file.dat"])

    with pytest.raises(ValueError, match="conflicting destination"):
        pull_manifest_module.prepare_transfer(manifest, destination, state)

    assert not state.exists()


@pytest.mark.parametrize("state_name", [".inventory.json.lock", ".datatrail-pull.lock"])
def test_transfer_checkpoint_cannot_replace_a_lock(tmp_path, state_name):
    """Checkpoint updates must never replace an inode providing active ownership."""
    manifest = tmp_path / "inventory.json"
    write_inventory(manifest, ["file.dat"])
    original = manifest.read_bytes()

    with pytest.raises(ValueError, match="control file"):
        with pull_manifest_module.transfer_session(
            manifest, tmp_path, tmp_path / state_name
        ):
            pytest.fail("A checkpoint could replace an active lock")

    assert manifest.read_bytes() == original


def test_command_without_configuration_has_actionable_error(tmp_path, monkeypatch):
    """A missing default destination reports a CLI error without a traceback."""
    manifest = tmp_path / "inventory.json"
    write_inventory(manifest, ["file.dat"])
    monkeypatch.setattr(pull_manifest_module, "procure", lambda: None)
    result = CliRunner().invoke(
        pull_manifest_module.pull_manifest, [str(manifest), "-f"]
    )

    assert result.exit_code == 1
    assert "use --directory" in result.output
    assert not manifest.with_suffix(".pull.json").exists()


@pytest.mark.parametrize("filename", ["datatrail-pull", ".owner.lock"])
def test_transfer_reserves_aliased_directory_ownership(tmp_path, filename):
    """A sentinel alias and its actual lock cannot be replaced by a download."""
    manifest = tmp_path / "inventory.json"
    state = tmp_path / "pull.json"
    destination = tmp_path / "data"
    destination.mkdir()
    (destination / "datatrail-pull").symlink_to(destination / "owner")
    write_inventory(manifest, [filename])

    with pytest.raises(ValueError, match="control file"):
        with pull_manifest_module.transfer_session(manifest, destination, state):
            pytest.fail("A download could invalidate directory ownership")

    assert not state.exists()
