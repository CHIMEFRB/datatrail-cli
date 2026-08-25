"""Tests for reliable downloads."""

from pathlib import Path
from types import SimpleNamespace

import pytest
from click.testing import CliRunner
from tenacity import wait_none

from dtcli import pull as pull_module
from dtcli.utilities import cadcclient


class FakeStorage:
    """Serve test files without a network connection."""

    def __init__(self, contents):
        self.contents = contents
        self.calls = []
        self.destinations = []

    def cadcinfo(self, uri):
        return SimpleNamespace(size=len(self.contents[uri]))

    def cadcget(self, uri, destination):
        self.calls.append(uri)
        self.destinations.append(destination)
        Path(destination).write_bytes(self.contents[uri])


def disable_retry_wait(monkeypatch):
    """Keep failed download tests fast."""
    monkeypatch.setattr(cadcclient, "wait_exponential", lambda **kwargs: wait_none())


def test_get_publishes_complete_file_atomically(monkeypatch, tmp_path):
    """The final path changes only after a complete download."""
    destination = tmp_path / "file.dat"
    destination.write_bytes(b"old")

    class AtomicStorage(FakeStorage):
        def cadcget(self, uri, temporary):
            temporary_path = Path(temporary)
            assert temporary_path.parent == destination.parent
            assert temporary_path != destination
            assert destination.read_bytes() == b"old"
            super().cadcget(uri, temporary)

    uri = "cadc:CHIMEFRB/data/file.dat"
    storage = AtomicStorage({uri: b"complete"})
    monkeypatch.setattr(cadcclient, "_connect", lambda **kwargs: (None, storage, None))

    failures = cadcclient.get(["data/file.dat"], [str(destination)])

    assert failures == []
    assert destination.read_bytes() == b"complete"
    assert storage.destinations[0].endswith(".part")
    assert list(tmp_path.glob(".*.part")) == []


def test_get_removes_incomplete_file_and_continues(monkeypatch, tmp_path):
    """A size mismatch does not stop later files."""
    disable_retry_wait(monkeypatch)
    bad_uri = "cadc:CHIMEFRB/data/bad.dat"
    good_uri = "cadc:CHIMEFRB/data/good.dat"
    storage = FakeStorage({bad_uri: b"bad", good_uri: b"good"})

    def cadcinfo(uri):
        size = 10 if uri == bad_uri else 4
        return SimpleNamespace(size=size)

    storage.cadcinfo = cadcinfo
    monkeypatch.setattr(cadcclient, "_connect", lambda **kwargs: (None, storage, None))
    bad_destination = tmp_path / "bad.dat"
    good_destination = tmp_path / "good.dat"

    failures = cadcclient.get(
        ["data/bad.dat", "data/good.dat"],
        [str(bad_destination), str(good_destination)],
    )

    assert len(failures) == 1
    assert failures[0]["source"] == "data/bad.dat"
    assert "size mismatch" in failures[0]["error"]
    assert not bad_destination.exists()
    assert good_destination.read_bytes() == b"good"
    assert storage.calls.count(bad_uri) == 3
    assert list(tmp_path.glob(".*.part")) == []


def test_get_cleans_up_after_interruption(monkeypatch, tmp_path):
    """An interrupted transfer leaves no visible or temporary file."""
    uri = "cadc:CHIMEFRB/data/file.dat"
    destination = tmp_path / "file.dat"

    class InterruptedStorage(FakeStorage):
        def cadcget(self, uri, temporary):
            Path(temporary).write_bytes(b"partial")
            raise KeyboardInterrupt

    storage = InterruptedStorage({uri: b"complete"})
    monkeypatch.setattr(cadcclient, "_connect", lambda **kwargs: (None, storage, None))

    with pytest.raises(KeyboardInterrupt):
        cadcclient.get(["data/file.dat"], [str(destination)])

    assert not destination.exists()
    assert list(tmp_path.glob(".*.part")) == []


def test_get_works_without_remote_size(monkeypatch, tmp_path):
    """A file can be downloaded when Minoc has no size metadata."""
    uri = "cadc:CHIMEFRB/data/file.dat"
    destination = tmp_path / "file.dat"
    storage = FakeStorage({uri: b"complete"})
    storage.cadcinfo = lambda uri: SimpleNamespace(size=None)
    monkeypatch.setattr(cadcclient, "_connect", lambda **kwargs: (None, storage, None))

    failures = cadcclient.get(["data/file.dat"], [str(destination)])

    assert failures == []
    assert destination.read_bytes() == b"complete"


def test_pget_returns_worker_failures(monkeypatch, tmp_path):
    """Parallel workers return failures to the caller."""
    destination = str(tmp_path / "file.dat")

    def send_failure(connection, source, destinations, *args):
        connection.send(
            [
                {
                    "source": source[0],
                    "destination": destinations[0],
                    "error": "size mismatch",
                }
            ]
        )
        connection.close()

    monkeypatch.setattr(cadcclient, "_send_get_results", send_failure)

    failures = cadcclient.pget(["data/file.dat"], [destination], processors=1)

    assert len(failures) == 1
    assert failures[0]["source"] == "data/file.dat"
    assert "size mismatch" in failures[0]["error"]


def configure_pull(monkeypatch, tmp_path, get_files):
    """Configure pull without external services."""
    destination = str(tmp_path / "data" / "file.dat")
    config = {"site": "local", "root_mounts": {"local": str(tmp_path)}}
    monkeypatch.setattr(pull_module, "procure", lambda: config)
    monkeypatch.setattr(pull_module, "validate_scope", lambda scope: True)
    monkeypatch.setattr(pull_module, "check_canfar_status", lambda console: (True, True))
    monkeypatch.setattr(
        pull_module,
        "find_missing_dataset_files",
        lambda *args, **kwargs: {"missing": ["data/file.dat"], "existing": []},
    )
    monkeypatch.setattr(pull_module.cadcclient, "size", lambda path: 1.0)
    monkeypatch.setattr(pull_module, "get_files", get_files)
    return destination


def test_pull_exits_nonzero_for_reported_failure(monkeypatch, tmp_path):
    """A worker failure makes the command fail."""
    destination = str(tmp_path / "data" / "file.dat")
    failure = {
        "source": "data/file.dat",
        "destination": destination,
        "error": "connection lost",
    }
    configure_pull(monkeypatch, tmp_path, lambda *args, **kwargs: [failure])

    result = CliRunner().invoke(
        pull_module.pull,
        ["scope", "dataset", "--directory", str(tmp_path), "--force"],
    )

    assert result.exit_code == 1
    assert "connection lost" in result.output


def test_pull_exits_nonzero_when_file_is_still_missing(monkeypatch, tmp_path):
    """A silent partial pull makes the command fail."""
    configure_pull(monkeypatch, tmp_path, lambda *args, **kwargs: [])

    result = CliRunner().invoke(
        pull_module.pull,
        ["scope", "dataset", "--directory", str(tmp_path), "--force"],
    )

    assert result.exit_code == 1
    assert "File not downloaded" in result.output


def test_pull_interruption_exits_nonzero(monkeypatch, tmp_path):
    """An interrupted pull is not reported as successful."""

    def interrupt(*args, **kwargs):
        raise KeyboardInterrupt

    configure_pull(monkeypatch, tmp_path, interrupt)

    result = CliRunner().invoke(
        pull_module.pull,
        ["scope", "dataset", "--directory", str(tmp_path), "--force"],
    )

    assert result.exit_code != 0
