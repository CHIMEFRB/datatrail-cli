"""Tests for output ownership across processes and path aliases."""

import subprocess
import sys
from pathlib import Path

import pytest

from dtcli.locking import output_lock


def test_other_process_is_refused_and_exit_releases_lock(tmp_path: Path) -> None:
    """A killed owner cannot leave an output permanently locked."""
    output = tmp_path / "inventory.json"
    code = (
        "import sys; from pathlib import Path; "
        "from dtcli.locking import output_lock\n"
        "with output_lock(Path(sys.argv[1])):\n"
        "    print('locked', flush=True)\n"
        "    sys.stdin.read(1)\n"
    )
    with subprocess.Popen(
        [sys.executable, "-c", code, str(output)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    ) as owner:
        try:
            assert owner.stdout is not None
            assert owner.stdout.readline().strip() == "locked"
            with pytest.raises(OSError, match="already in use"):
                with output_lock(output):
                    pytest.fail("A second writer acquired the output")
        finally:
            owner.kill()
            owner.wait(timeout=10)

    with output_lock(output):
        output.write_text("recovered", encoding="utf-8")
    assert output.read_text(encoding="utf-8") == "recovered"
    assert (tmp_path / ".inventory.json.lock").exists()


def test_aliases_share_ownership_and_interruptions_release_it(tmp_path: Path) -> None:
    """A symlink cannot bypass ownership, and exceptions release it."""
    output = tmp_path / "inventory.json"
    output.write_text("original", encoding="utf-8")
    alias = tmp_path / "alias.json"
    try:
        alias.symlink_to(output)
    except OSError:
        pytest.skip("This platform does not permit creating symlinks")

    with pytest.raises(KeyboardInterrupt):
        with output_lock(output):
            with pytest.raises(OSError, match="already in use"):
                with output_lock(alias):
                    pytest.fail("An alias bypassed the lock")
            raise KeyboardInterrupt

    with output_lock(alias):
        assert output.read_text(encoding="utf-8") == "original"
