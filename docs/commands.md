<div align="center">
    <img src="../images/Datatrail-logo.png" width="110", height="100">
</div>

<h1 align="center">Commands</h1>

The commands available to you are:

- [`clear`](clear.md): Remove a dataset's files at the local or CANFAR site.
- [`config`](cli.md#datatrail-config): Initialize, inspect, or edit the CLI
  configuration.
- [`doctor`](doctor.md): Check configuration, server health, certificate validity,
  and authentication to Minoc and Luskan.
- [`inventory`](inventory.md): Recursively discover datasets and write their
  file replica URIs to a resumable JSON manifest.
- [`list` / `ls`](list.md): Browse scopes and datasets, filter with `--match`,
  or discover children with `--expand` and `--recursive`.
- [`ps`](ps.md): Inspect a dataset's files and storage locations. JSON output
  includes common paths for each storage element.
- [`pull`](pull.md): Download a dataset's files.
- [`pull-manifest`](pull-manifest.md): Download Minoc files from an inventory
  manifest with resumable transfer state.
- [`scout`](scout.md): Compare registered and observed file counts and, after
  confirmation, register missing Minoc replicas.
- [`unregistered`](unregistered.md): Summarize registration failures or search
  for records of a specific event.
- [`verify`](verify.md): Compare registered Minoc files with Minoc and Luskan
  metadata, reporting missing files, size or checksum mismatches, and
  unavailable metadata.
- [`version`](cli.md#datatrail-version): Show CLI and server version information.

For practical examples, start with the [User Guide](user_guide.md) or the
[recursive discovery walkthrough](discovery.md). The
[Reference](cli.md) lists every command and its options.
