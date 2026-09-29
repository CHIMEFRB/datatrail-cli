"""Tests for optional pull size estimates."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from cadcutils import exceptions
from click.testing import CliRunner
from requests.exceptions import ConnectionError, ConnectTimeout, ReadTimeout, SSLError

from dtcli import pull as pull_module


@pytest.fixture
def pull_environment(monkeypatch, tmp_path):
    """Configure a downloadable file without external services."""
    destination = tmp_path / "data" / "file.dat"
    config = {"site": "local", "root_mounts": {"local": str(tmp_path)}}
    status = Mock(return_value=(True, True))
    size = Mock(return_value=1.25)

    def download(*args, **kwargs):
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(b"complete")
        return []

    get_files = Mock(side_effect=download)
    monkeypatch.setattr(pull_module, "procure", lambda: config)
    monkeypatch.setattr(pull_module, "validate_scope", lambda scope: True)
    monkeypatch.setattr(pull_module, "check_canfar_status", status)
    monkeypatch.setattr(
        pull_module,
        "find_missing_dataset_files",
        lambda *args, **kwargs: {"missing": ["data/file.dat"], "existing": []},
    )
    monkeypatch.setattr(pull_module.cadcclient, "size", size)
    monkeypatch.setattr(pull_module, "get_files", get_files)
    return SimpleNamespace(
        args=["scope", "dataset", "--directory", str(tmp_path)],
        destination=destination,
        status=status,
        size=size,
        get_files=get_files,
    )


@pytest.mark.parametrize(
    "error",
    [
        exceptions.HttpException("service retries exhausted"),
        exceptions.InternalServerException("500 Internal Server Error"),
        exceptions.UnexpectedException("503 Service Unavailable"),
        exceptions.TransferException("Read timeout"),
        ConnectionError("connection lost"),
        ConnectTimeout("connect timeout"),
        ReadTimeout("read timeout"),
    ],
    ids=lambda error: type(error).__name__,
)
def test_pull_force_continues_after_size_query_failure(pull_environment, error):
    """A failed optional query after a healthy probe cannot block a forced pull."""
    env = pull_environment
    env.size.side_effect = error

    result = CliRunner().invoke(pull_module.pull, env.args + ["--force"])

    assert result.exit_code == 0, result.exception
    assert "Unable to query Luskan" in result.output
    assert "No valid CADC certificate" not in result.output
    assert "Download 1 files?" not in result.output
    env.size.assert_called_once_with("/data/file.dat")
    env.get_files.assert_called_once()
    assert env.destination.read_bytes() == b"complete"


@pytest.mark.parametrize("luskan_up", [True, False])
@pytest.mark.parametrize("answer, download", [("y", True), ("n", False)])
def test_pull_confirms_when_size_is_unknown(
    pull_environment, luskan_up, answer, download
):
    """Unknown size still requires and respects the user's download decision."""
    env = pull_environment
    env.status.return_value = (True, luskan_up)
    env.size.side_effect = exceptions.UnexpectedException("503 Service Unavailable")

    result = CliRunner().invoke(pull_module.pull, env.args, input=answer + "\n")

    assert result.exit_code == 0, result.exception
    assert "Unable to query Luskan" in result.output
    assert "Download 1 files?" in result.output
    assert env.size.call_count == int(luskan_up)
    assert env.get_files.call_count == int(download)
    assert env.destination.exists() == download


def test_pull_force_skips_size_query_when_luskan_is_down(pull_environment):
    """A failed health probe skips the query and allows a forced download."""
    env = pull_environment
    env.status.return_value = (True, False)

    result = CliRunner().invoke(pull_module.pull, env.args + ["--force"])

    assert result.exit_code == 0, result.exception
    assert "Unable to query Luskan" in result.output
    assert "Download 1 files?" not in result.output
    env.size.assert_not_called()
    env.get_files.assert_called_once()


@pytest.mark.parametrize("size, force", [(1.25, False), (0.0, False), (0.0, True)])
def test_pull_preserves_known_size_behavior(pull_environment, size, force):
    """Known sizes retain their display and zero-size confirmation behavior."""
    env = pull_environment
    env.size.return_value = size
    args = env.args + (["--force"] if force else [])

    result = CliRunner().invoke(pull_module.pull, args, input="y\n")

    assert result.exit_code == 0, result.exception
    assert f"Size to download: {size:.2f} GB" in result.output
    assert "Unable to query Luskan" not in result.output
    assert env.get_files.call_count == int(force or size > 0)
    assert ("Download 1 files?" in result.output) == (not force and size > 0)


def test_pull_preserves_certificate_guidance(pull_environment):
    """A Requests certificate error still stops before prompting or downloading."""
    env = pull_environment
    env.size.side_effect = SSLError("invalid certificate")

    result = CliRunner().invoke(pull_module.pull, env.args + ["--force"])

    assert "No valid CADC certificate found" in result.output
    assert "cadc-get-cert" in result.output
    assert "Unable to query Luskan" not in result.output
    env.get_files.assert_not_called()


@pytest.mark.parametrize(
    "error",
    [
        exceptions.SslException("invalid certificate"),
        exceptions.UnauthorizedException("authentication required"),
        exceptions.ForbiddenException("permission denied"),
        exceptions.BadRequestException("invalid query"),
        exceptions.NotFoundException("resource missing"),
        ValueError("invalid query result"),
        TypeError("invalid call"),
        OSError("local filesystem error"),
        MemoryError("out of memory"),
    ],
    ids=lambda error: type(error).__name__,
)
def test_pull_does_not_hide_other_size_errors(pull_environment, error):
    """Authentication, certificate, and unexpected local errors remain fatal."""
    env = pull_environment
    env.size.side_effect = error

    result = CliRunner().invoke(pull_module.pull, env.args + ["--force"])

    assert result.exit_code != 0
    assert result.exception is error
    assert "Unable to query Luskan" not in result.output
    env.get_files.assert_not_called()
