"""Tests for the Datatrail functions for Workflow pipelines."""

from types import SimpleNamespace

import click
import pytest
import yaml

from dtcli import workflow


class FakeCommand:
    """A CLI command that records its arguments and returns an exit code."""

    def __init__(self, name, code=None, effect=None):
        self.name = name
        self.code = code
        self.effect = effect
        self.calls = []

    def main(self, args, standalone_mode):
        assert standalone_mode is False
        self.calls.append(args)
        if self.effect:
            self.effect()
        return self.code


@pytest.fixture
def config(tmp_path, monkeypatch):
    """A Datatrail configuration for canfar, with its root mount in tmp_path."""
    path = tmp_path / ".datatrail" / "config.yaml"
    root = str(tmp_path / "arc") + "/"
    monkeypatch.setattr(workflow, "CONFIG", path)

    def write(site="canfar"):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump({"site": site, "root_mounts": {site: root}}))

    monkeypatch.setattr(
        workflow, "init", SimpleNamespace(callback=lambda site: write(site))
    )
    monkeypatch.setattr(workflow, "procure", lambda: yaml.safe_load(path.read_text()))
    return SimpleNamespace(path=path, root=root, write=write)


def test_pull_dataset_returns_workflow_outcome(config, monkeypatch):
    config.write()
    pull = FakeCommand("pull")
    monkeypatch.setattr(workflow, "pull", pull)
    monkeypatch.setattr(
        workflow,
        "find_missing_dataset_files",
        lambda scope, dataset, root, verbose: {"missing": [], "existing": ["a", "b"]},
    )

    results, products, plots = workflow.pull_dataset(
        "chime.event.baseband.raw", 123, cores=4, site="canfar"
    )

    assert pull.calls == [
        ["chime.event.baseband.raw", "123", "--force", "--cores", "4", "-v"]
    ]
    assert results == {
        "scope": "chime.event.baseband.raw",
        "dataset": "123",
        "files": 2,
        "directory": config.root,
    }
    assert products == [] and plots == []


def test_pull_dataset_creates_the_configuration(config, monkeypatch):
    monkeypatch.setattr(workflow, "pull", FakeCommand("pull"))
    monkeypatch.setattr(
        workflow,
        "find_missing_dataset_files",
        lambda *args: {"missing": [], "existing": ["a"]},
    )
    workflow.pull_dataset("scope", "1", site="canfar")
    assert yaml.safe_load(config.path.read_text())["site"] == "canfar"


def test_pull_dataset_needs_a_site_without_configuration(config):
    with pytest.raises(RuntimeError, match="give a site"):
        workflow.pull_dataset("scope", "1")


def test_pull_dataset_refuses_another_sites_configuration(config):
    config.write("chime")
    with pytest.raises(RuntimeError, match="is for chime, not canfar"):
        workflow.pull_dataset("scope", "1", site="canfar")


@pytest.mark.parametrize(
    "code, files, message",
    [
        # ctx.exit(1) comes back as a return value
        (1, {"missing": [], "existing": ["a"]}, "exited with 1"),
        # pull reports these only on the console and exits 0
        (None, {"error": "Scope does not exist"}, "Could not check"),
        (None, {"missing": ["a"], "existing": ["b"]}, "1 of scope 1's files"),
        (None, {"missing": [], "existing": []}, "has no files"),
    ],
)
def test_pull_dataset_raises_when_it_failed(config, monkeypatch, code, files, message):
    config.write()
    monkeypatch.setattr(workflow, "pull", FakeCommand("pull", code=code))
    monkeypatch.setattr(workflow, "find_missing_dataset_files", lambda *args: files)
    with pytest.raises(RuntimeError, match=message):
        workflow.pull_dataset("scope", "1", site="canfar")


def test_pull_dataset_passes_on_click_errors(config, monkeypatch):
    config.write()

    def abort():
        raise click.Abort()

    monkeypatch.setattr(workflow, "pull", FakeCommand("pull", effect=abort))
    with pytest.raises(click.Abort):
        workflow.pull_dataset("scope", "1", site="canfar")


def _dataset_dir(config):
    path = config.path.parent.parent / "arc" / "data" / "chime" / "astro_1"
    path.mkdir(parents=True)
    (path / "baseband_1_0.h5").write_text("")
    return path


def test_clear_dataset_clears_and_checks(config, monkeypatch):
    config.write()
    path = _dataset_dir(config)

    def delete():
        for file in path.iterdir():
            file.unlink()
        path.rmdir()

    clear = FakeCommand("clear", effect=delete)
    monkeypatch.setattr(workflow, "clear", clear)
    monkeypatch.setattr(
        workflow, "find_dataset_common_path", lambda *args: "data/chime/astro_1/"
    )

    results, products, plots = workflow.clear_dataset("scope", 1, site="canfar")

    assert clear.calls == [["scope", "1", "--force", "-v"]]
    assert results == {
        "scope": "scope",
        "dataset": "1",
        "path": config.root + "data/chime/astro_1/",
        "cleared": True,
    }
    assert products == [] and plots == []


def test_clear_dataset_without_a_local_copy(config, monkeypatch):
    config.write()
    clear = FakeCommand("clear")
    monkeypatch.setattr(workflow, "clear", clear)
    monkeypatch.setattr(
        workflow, "find_dataset_common_path", lambda *args: "data/chime/astro_2/"
    )
    results, _, _ = workflow.clear_dataset("scope", "2", site="canfar")
    assert results["cleared"] is False
    assert clear.calls == []


def test_clear_dataset_raises_when_files_remain(config, monkeypatch):
    config.write()
    _dataset_dir(config)
    monkeypatch.setattr(workflow, "clear", FakeCommand("clear"))
    monkeypatch.setattr(
        workflow, "find_dataset_common_path", lambda *args: "data/chime/astro_1/"
    )
    with pytest.raises(RuntimeError, match="still there"):
        workflow.clear_dataset("scope", "1", site="canfar")


@pytest.mark.parametrize(
    "common", [None, "The Datatrail Central Server at CHIME at is not reachable!!!"]
)
def test_clear_dataset_raises_when_it_cant_find_the_dataset(config, monkeypatch, common):
    config.write()
    monkeypatch.setattr(workflow, "find_dataset_common_path", lambda *args: common)
    with pytest.raises(RuntimeError, match="Could not find where"):
        workflow.clear_dataset("scope", "1", site="canfar")
