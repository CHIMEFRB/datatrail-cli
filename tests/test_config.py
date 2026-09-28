"""Tests for shared configuration loading and validation."""

from pathlib import Path

import pytest
import yaml

from dtcli import config


@pytest.fixture
def configuration():
    """Provide valid CLI settings."""
    return {
        "server": "https://example.invalid/datatrail",
        "vospace_certfile": "/tmp/certificate.pem",
        "site": "local",
        "root_mounts": {"local": "./"},
    }


def test_procure_configuration_and_keys(tmp_path: Path, configuration):
    """Load complete mappings and individual values without discarding false values."""
    configuration.update({"enabled": False, "": "empty-key-value"})
    filename = tmp_path / "config.yaml"
    filename.write_text(yaml.safe_dump(configuration))

    assert config.procure(filename) == configuration
    assert config.procure(filename, "server") == configuration["server"]
    assert config.procure(filename, "enabled") is False
    assert config.procure(filename, "") == "empty-key-value"
    assert config.procure(filename, "missing") is None


@pytest.mark.parametrize(
    "contents", ["", "null", "- private-value", "private-value", "1"]
)
def test_procure_rejects_nonmapping_yaml(tmp_path: Path, caplog, contents):
    """Reject empty, scalar, and sequence documents without logging their contents."""
    filename = tmp_path / "private-filename.yaml"
    filename.write_text(contents)

    assert config.procure(filename) is None
    assert "Configuration must be a mapping." in caplog.text
    assert "private" not in caplog.text


def test_procure_malformed_yaml_is_private(tmp_path: Path, caplog):
    """Do not expose parser exceptions, paths, or secret YAML values in diagnostics."""
    filename = tmp_path / "private-filename.yaml"
    filename.write_text("secret: [private-value")

    assert config.procure(filename) is None
    assert "Configuration could not be loaded." in caplog.text
    assert "private" not in caplog.text
    assert "secret" not in caplog.text
    assert all(record.exc_info is None for record in caplog.records)


@pytest.mark.parametrize(
    "error",
    [
        FileNotFoundError("private-value"),
        PermissionError("private-value"),
        UnicodeDecodeError("utf-8", b"\xff", 0, 1, "private-value"),
    ],
)
def test_procure_expected_read_failures(monkeypatch, tmp_path: Path, caplog, error):
    """Return None for missing, unreadable, and undecodable configuration files."""

    def fail_open(*args, **kwargs):
        """Simulate a failed configuration read."""
        raise error

    monkeypatch.setattr(config, "open", fail_open, raising=False)

    assert config.procure(tmp_path / "private-filename.yaml") is None
    assert "Configuration could not be loaded." in caplog.text
    assert "private" not in caplog.text
    assert all(record.exc_info is None for record in caplog.records)


@pytest.mark.parametrize("contents", [None, "secret: [private-value", "- private-value"])
def test_procure_quiet_failures(tmp_path: Path, caplog, contents):
    """Keep loading failures silent when requested by machine-readable commands."""
    filename = tmp_path / "private-filename.yaml"
    if contents is not None:
        filename.write_text(contents)

    assert config.procure(filename, quiet=True) is None
    assert not caplog.records


def test_procure_does_not_hide_unexpected_errors(monkeypatch, tmp_path: Path):
    """Leave programming errors visible instead of treating them as missing settings."""

    def fail_load(*args, **kwargs):
        """Simulate an unexpected loader failure."""
        raise RuntimeError("unexpected failure")

    filename = tmp_path / "config.yaml"
    filename.write_text("site: local")
    monkeypatch.setattr(config.yaml, "safe_load", fail_load)

    with pytest.raises(RuntimeError, match="unexpected failure"):
        config.procure(filename)


@pytest.mark.parametrize("scheme", ["http", "https"])
def test_validate_configuration(configuration, scheme):
    """Accept complete configurations with supported server protocols."""
    configuration["server"] = f"{scheme}://example.invalid/datatrail"

    assert config.validate(configuration) is True


@pytest.mark.parametrize("configuration", [None, [], "site: local", 1])
def test_validate_requires_mapping(configuration):
    """Reject configuration values that are not mappings."""
    assert config.validate(configuration) is False


@pytest.mark.parametrize("key", ["server", "vospace_certfile", "site", "root_mounts"])
def test_validate_requires_settings(configuration, key):
    """Require every setting used by CLI readiness checks."""
    del configuration[key]

    assert config.validate(configuration) is False


@pytest.mark.parametrize("key", ["server", "vospace_certfile", "site"])
@pytest.mark.parametrize("value", [None, 1, "", " \t"])
def test_validate_requires_nonblank_strings(configuration, key, value):
    """Reject unusable server, certificate, and site values."""
    configuration[key] = value

    assert config.validate(configuration) is False


@pytest.mark.parametrize(
    "server",
    ["ftp://example.invalid", "https:///datatrail", "example.invalid", "http://["],
)
def test_validate_rejects_invalid_server(configuration, server):
    """Reject unsupported or malformed server URLs without raising parser errors."""
    configuration["server"] = server

    assert config.validate(configuration) is False


@pytest.mark.parametrize(
    "mounts",
    [None, [], {}, {"other": "/"}, {"local": 1}, {"local": ""}, {"local": " \t"}],
)
def test_validate_requires_mount_for_site(configuration, mounts):
    """Require a nonblank string root mount for the configured site."""
    configuration["root_mounts"] = mounts

    assert config.validate(configuration) is False
