# Building a durable inventory

`datatrail inventory` recursively discovers terminal datasets and records each
file replica URI in a versioned JSON manifest. The manifest can later drive a
batch download without repeating the archive crawl.

Every run must be bounded in one of these ways:

```shell
$> datatrail inventory chime.event.baseband.raw
$> datatrail inventory --match classified,baseband
$> datatrail inventory gbo.acquisition.processed --parent complex_gains
```

A scope limits traversal to that scope. `--match` may search across scopes but
only opens matching larger datasets. `--parent` requires a scope and starts at
one known dataset. It cannot be combined with `--match`.

Use `--output` to choose the manifest path:

```shell
$> datatrail inventory chime.event.baseband.raw --match classified \
     --output baseband-inventory.json
```

The command writes the manifest atomically after discovery and after every
dataset query. A rerun with the same selection reuses `ready` and `empty`
entries, then retries `pending` and `failed` entries. A different selection is
refused so unrelated inventories cannot be mixed.

An inventory with any failed discovery branch or file query exits nonzero.
`--allow-incomplete` keeps the incomplete manifest but exits zero when a caller
wants to inspect or process the available subset.

## Manifest format

The first format is `datatrail.inventory/v1`:

```json
{
  "schema": "datatrail.inventory/v1",
  "selection": {
    "scope": "gbo.acquisition.processed",
    "match": [],
    "parent": "complex_gains"
  },
  "complete": true,
  "discovery_failures": [],
  "datasets": [
    {
      "scope": "gbo.acquisition.processed",
      "dataset": "20230525",
      "parent": "complex_gains",
      "path": ["complex_gains", "20230525"],
      "status": "ready",
      "replicas": [
        {
          "storage_element": "minoc",
          "uri": "cadc:CHIMEFRB/example/file.h5"
        }
      ]
    }
  ]
}
```

Replica rows contain only Datatrail information. Size and checksum fields may
be added in a later schema when they can be obtained without requiring a CADC
credential during inventory creation. A valid dataset with no replica URIs has
status `empty`; an unavailable or invalid file response has status `failed`
and an `error` field.
