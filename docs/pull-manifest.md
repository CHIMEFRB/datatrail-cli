# Pulling an inventory

`datatrail pull-manifest` downloads the Minoc files in an inventory and writes
durable transfer state beside it:

```shell
$> datatrail pull-manifest baseband-inventory.json --directory ./baseband
```

The default state path is `<inventory-name>.pull.json`. Use `--state` to put it
elsewhere. Each completed batch is written atomically, so rerunning the same
command skips completed files whose recorded size still matches and retries
pending or failed files.

Transfers are limited by `--cores`, which defaults to one. A larger value runs
only that many files at once:

```shell
$> datatrail pull-manifest baseband-inventory.json --directory ./baseband \
     --cores 4 --force
```

Each file is downloaded to a temporary sibling, checked against Minoc's size
when available, and moved into place only after it completes. An interrupted or
truncated download does not replace the destination.

The command exits nonzero when any file fails, the inventory is incomplete, or
a ready dataset has no Minoc replica. Available files are still downloaded and
checkpointed, so the next run can continue after the service recovers.

## Transfer state

The transfer state uses schema `datatrail.pull/v1`:

```json
{
  "schema": "datatrail.pull/v1",
  "inventory": "/data/baseband-inventory.json",
  "directory": "/data/baseband",
  "inventory_complete": true,
  "unavailable_datasets": [],
  "complete": true,
  "files": [
    {
      "uri": "cadc:CHIMEFRB/example/file.h5",
      "path": "example/file.h5",
      "status": "complete",
      "bytes": 4096
    }
  ]
}
```

Keep the state file with its inventory. A state file cannot be reused with a
different inventory path or destination directory.
