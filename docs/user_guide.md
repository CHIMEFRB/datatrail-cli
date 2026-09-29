<div align="center">
    <img src="../images/Datatrail-logo.png" width="110", height="100">
</div>

<h1 align="center">User Guide</h1>

## Set up and check your connection

[Install the CLI](install.md), then [initialize its configuration](initialising.md).
Use [`doctor`](doctor.md) to check your configuration, Datatrail server health,
CANFAR certificate, and authentication to Minoc and Luskan before working with
files. The [`config` reference](cli.md#datatrail-config) covers inspecting and
editing configuration values.

## Find and inspect datasets

Start with [Recursive discovery](discovery.md) for a walkthrough of `--match`,
`--expand`, and `--recursive`, followed by a resumable inventory and download.

- [`list` / `ls`](list.md): Browse scopes and datasets. Use `--match` to narrow
  a search, `--expand` to see one level of children, and `--recursive` to follow
  descendants to terminal datasets.
- [`ps`](ps.md): Inspect a dataset's files and storage locations, including
  per-storage-element common paths in JSON output.
- [`inventory`](inventory.md): Save recursive discovery and file replica URIs
  in a JSON manifest that can be resumed after an interruption.

## Download and check files

For a large collection, use [`inventory`](inventory.md) to save the discovered
files, then pass that manifest to [`pull-manifest`](pull-manifest.md) to download
them with resumable progress.

- [`pull`](pull.md): Download the files in a dataset.
- [`pull-manifest`](pull-manifest.md): Download Minoc files from an inventory
  with saved transfer progress and bounded concurrency.
- [`verify`](verify.md): Compare registered Minoc files with Minoc and Luskan
  metadata to identify missing files, size or checksum mismatches, and
  unavailable metadata.
- [`clear`](clear.md): Remove a dataset's local or CANFAR files.

## Investigate registration problems

- [`scout`](scout.md): Compare registered and observed file counts and review
  discrepancies before confirming repairs.
- [`unregistered`](unregistered.md): Summarize registration failures or inspect
  records for a specific event, with optional scope and partial-name filters.

## Use results in scripts

`list`, `ps`, `doctor`, `verify`, and `unregistered search` support `--json`.
Their guides explain each output format. `inventory` writes a JSON manifest,
while `pull-manifest` saves a separate JSON transfer-state file. Consult the
relevant command's guide for exit status and error handling.

The [command overview](commands.md) links to every command, including
[`version`](cli.md#datatrail-version). The [CLI reference](cli.md) lists all
arguments and options.
