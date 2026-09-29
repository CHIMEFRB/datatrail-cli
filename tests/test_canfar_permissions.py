"""Native CANFAR permissions stay within the requested directory tree."""

import grp
import logging
import os
import stat
from types import SimpleNamespace

import pytest

from dtcli.src import functions


def _mode(path):
    return stat.S_IMODE(path.stat().st_mode)


def test_permissions_preserve_modes_and_update_nested_files(tmp_path):
    folder = tmp_path / "dataset"
    nested = folder / "nested"
    nested.mkdir(parents=True)
    ordinary = nested / "data.h5"
    executable = folder / "script"
    ordinary.write_text("data")
    executable.write_text("script")
    folder.chmod(0o750)
    nested.chmod(0o700)
    ordinary.chmod(0o640)
    executable.chmod(0o751)

    functions._apply_chime_frb_rw_permissions(str(folder), os.getgid())

    assert _mode(folder) == 0o770
    assert _mode(nested) == 0o720
    assert _mode(ordinary) == 0o660
    assert _mode(executable) == 0o771
    assert all(
        path.stat().st_gid == os.getgid()
        for path in (folder, nested, ordinary, executable)
    )


def test_permissions_do_not_follow_file_directory_or_root_symlinks(tmp_path):
    folder = tmp_path / "dataset"
    folder.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    external_file = outside / "private"
    external_file.write_text("private")
    outside.chmod(0o700)
    external_file.chmod(0o600)
    (folder / "file-link").symlink_to(external_file)
    (folder / "directory-link").symlink_to(outside, target_is_directory=True)
    (folder / "cycle").symlink_to(folder, target_is_directory=True)
    root_link = tmp_path / "root-link"
    root_link.symlink_to(outside, target_is_directory=True)

    functions._apply_chime_frb_rw_permissions(str(folder), os.getgid())
    functions._apply_chime_frb_rw_permissions(str(root_link), os.getgid())

    assert _mode(outside) == 0o700
    assert _mode(external_file) == 0o600


def test_permissions_reject_file_replaced_by_symlink(tmp_path, monkeypatch):
    folder = tmp_path / "dataset"
    folder.mkdir()
    victim = folder / "victim"
    victim.write_text("data")
    outside = tmp_path / "private"
    outside.write_text("private")
    outside.chmod(0o600)
    original_chmod = os.chmod

    def replace_before_chmod(path, mode, *args, **kwargs):
        if path == "victim":
            victim.unlink()
            victim.symlink_to(outside)
        return original_chmod(path, mode, *args, **kwargs)

    monkeypatch.setattr(functions.os, "chmod", replace_before_chmod)
    functions._apply_chime_frb_rw_permissions(str(folder), os.getgid())

    assert victim.is_symlink()
    assert _mode(outside) == 0o600


def test_chown_failure_does_not_skip_chmod(tmp_path, monkeypatch, caplog):
    folder = tmp_path / "dataset"
    folder.mkdir(mode=0o700)
    data = folder / "data"
    data.write_text("data")
    data.chmod(0o600)

    def deny_chown(*args, **kwargs):
        raise PermissionError("group change denied")

    monkeypatch.setattr(functions.os, "fchown", deny_chown)
    monkeypatch.setattr(functions.os, "chown", deny_chown)
    with caplog.at_level(logging.WARNING):
        functions._apply_chime_frb_rw_permissions(str(folder), os.getgid())

    assert _mode(folder) == 0o720
    assert _mode(data) == 0o620
    assert "group change denied" in caplog.text


def test_chmod_failure_does_not_stop_other_files(tmp_path, monkeypatch, caplog):
    folder = tmp_path / "dataset"
    folder.mkdir()
    denied = folder / "denied"
    allowed = folder / "allowed"
    for path in (denied, allowed):
        path.write_text("data")
        path.chmod(0o600)
    original_chmod = os.chmod

    def selective_chmod(path, mode, **kwargs):
        if path == "denied":
            raise PermissionError("mode change denied")
        original_chmod(path, mode, **kwargs)

    monkeypatch.setattr(functions.os, "chmod", selective_chmod)
    with caplog.at_level(logging.WARNING):
        functions._apply_chime_frb_rw_permissions(str(folder), os.getgid())

    assert _mode(denied) == 0o600
    assert _mode(allowed) == 0o620
    assert "mode change denied" in caplog.text


def test_get_files_resolves_group_once_and_preserves_transfer_result(
    tmp_path, monkeypatch
):
    lookups = []
    transfers = []
    failed = [{"source": "failed"}]

    def resolve_group(name):
        lookups.append(name)
        return SimpleNamespace(gr_gid=os.getgid())

    def transfer(**kwargs):
        transfers.append(kwargs)
        return failed

    monkeypatch.setattr(grp, "getgrnam", resolve_group)
    monkeypatch.setattr(functions, "procure", lambda: {"root_mounts": {}})
    monkeypatch.setattr(functions.cadcclient, "pget", transfer)

    result = functions.get_files(
        ["data/a/one.h5", "data/b/two.h5"], "canfar", str(tmp_path), 2, 0
    )

    assert lookups == ["chime-frb-rw"]
    assert result is failed
    assert len(transfers) == 1
    assert transfers[0]["destination"] == [
        str(tmp_path / "data/a/one.h5"),
        str(tmp_path / "data/b/two.h5"),
    ]
    assert all(_mode(tmp_path / p) & stat.S_IWGRP for p in ["data/a", "data/b"])


@pytest.mark.parametrize("error", [KeyError("missing group"), OSError("lookup failed")])
def test_missing_group_keeps_group_write_and_downloads(
    tmp_path, monkeypatch, caplog, error
):
    folder = tmp_path / "data"
    folder.mkdir(mode=0o700)
    transferred = []

    def missing_group(name):
        raise error

    monkeypatch.setattr(grp, "getgrnam", missing_group)
    monkeypatch.setattr(functions, "procure", lambda: {"root_mounts": {}})
    monkeypatch.setattr(
        functions.cadcclient, "pget", lambda **kwargs: transferred.append(kwargs) or []
    )
    with caplog.at_level(logging.WARNING):
        result = functions.get_files(["data/file.h5"], "canfar", str(tmp_path), 1, 0)

    assert result == []
    assert len(transferred) == 1
    assert _mode(folder) == 0o720
    assert "Could not resolve CANFAR group" in caplog.text


def test_permissions_do_not_require_read_access_to_owned_files(tmp_path):
    folder = tmp_path / "dataset"
    folder.mkdir()
    data = folder / "unreadable"
    data.write_text("data")
    data.chmod(0)
    try:
        functions._apply_chime_frb_rw_permissions(str(folder), os.getgid())
        assert _mode(data) == 0o020
    finally:
        data.chmod(0o600)


def test_missing_directory_is_best_effort(tmp_path, caplog):
    with caplog.at_level(logging.WARNING):
        functions._apply_chime_frb_rw_permissions(str(tmp_path / "missing"), os.getgid())
    assert "Could not update CANFAR permissions" in caplog.text
