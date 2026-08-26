# 🗒️ Finding scopes and datasets with `list`

<!-- termynal -->
```bash
$ datatrail ls --help
Usage: datatrail list [OPTIONS] [SCOPE] [DATASETS]

  List scopes & datasets

Options:
  -v, --verbose  Verbosity: v=INFO, vv=DEBUG.
  -q, --quiet    Only errors shown in logs.
  --write        Write the events to file.
  --json         Output as JSON.
  --match TEXT   Comma-separated, case-insensitive terms a larger dataset must
                 all contain.
  --expand       Open each matched larger dataset one level and list its
                 children.
  --help         Show this message and exit.

```

Datasets in Datatrail are identified by the unique combination of a 'scope' and
a 'dataset name'. A scope gives an indication of site that the data was captured
at and the type of data product that the dataset contains. For example, the
scope 'kko.scheduled.baseband.raw' contains datasets captured at the KKO
outrigger and that are manually triggered baseband dumps.

Within Datatrail, there are two types of datasets:

- **Larger datasets** - are datasets that contain other datasets, but no files.
- **Datasets** - are datasets that are attached to files.

!!! note "Scopes"

    A list of all scopes in the Datatrail database can be obtained by the
    following command:

    ```shell
    $> datatrail ls
            Datatrail: Scopes
    ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
    ┃ Scopes                        ┃
    ┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
    │ chime.event.baseband.raw      │
    │ chime.event.intensity.raw     │
    │ kko.acquisition.processed     │
    │ kko.calibration.trackingbeam  │
    │ kko.event.baseband.beamformed │
    │ kko.event.baseband.processed  │
    │ kko.event.baseband.raw        │
    │ kko.scheduled.baseband.raw    │
    └───────────────────────────────┘
    ```

!!! note "Larger datasets with a scope"

    A list of all larger datasets for a given scope in the Datatrail database
    can be obtained by the following command:

    ```shell
    $> datatrail ls kko.scheduled.baseband.raw
               Datatrail: Larger Datasets
               kko.scheduled.baseband.raw
    ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
    ┃               Larger datasets                ┃
    ┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
    │                20230804095251                │
    │        scheduled.commissioning.steady        │
    └──────────────────────────────────────────────┘
    (END)

    ```

!!! note "Datasets within a larger dataset"

    A list of all datasets within a larger dataset in the Datatrail database
    can be obtained by the following command:

    ```shell
    Datatrail: Child Datasets scheduled.commissioning.steady kko.scheduled.baseband.raw
    ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
    ┃                                Datasets                                 ┃
    ┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
    │    20230616150511  20230604135840  20230604134842    20230604131847     │
    │    20230604130848  20230604125850  20230604124851    20230604123853     │
    │    20230604120858  20230603081533  20230603080535    20230603075536     │
    │    20230603072541  20230603071543  20230603070544    20230603065546     │
    │    20230603062551  20230601082325  20230601081326    20230601080328     │
    │    20230601073333  20230601072335  20230601071336    20230601070338     │
    │    20230601063343  20230531124438  20230531123440    20230524142031     │
    │    20230524135029  20230524134028  20230524133027    20230524132026     │
    │    20230524125024  20230524124023  20230524123022    20230523124023     │
    │    20230522074031  20230522073030  20230522072029    20230522071028     │
    │    20230522064025  20230522063024  20230522062023    20230522061022     │
    │    20230521074031  20230521073030  20230521072029    20230521071028     │
    │    20230521064025  20230521063024  20230521062023    20230521061023     │
    │    20230519094030  20230519093029  20230519092028    20230519091027     │
    │    20230519084025  20230519083024  20230519082023    20230519081022     │
    │    20230518030521  20230518024523  20230518024022    20230518023522     │
    :
    ```

!!! abstract "More information"

    Please see the CLI reference page for more information on the `list` command:
    [datatrail list](../cli/#datatrail-list)

## Finding datasets with `--match` and `--expand`

Navigating the hierarchy one name at a time gets slow when you do not know
where a dataset lives. `--match` filters the larger datasets of a scope, or
of **every** scope when no scope is given, by one or more comma-separated,
case-insensitive terms, which must all appear in the combined
`scope dataset` text:

```shell
$> datatrail ls chime.acquisition.processed --match gains
      Datatrail: Dataset Map
+-----------------------------+---------------+
| Scope                       | Dataset       |
+-----------------------------+---------------+
| chime.acquisition.processed | complex_gains |
+-----------------------------+---------------+
```

A hit may be a container whose children are the datasets you actually want.
`--expand` opens each matched larger dataset one level and lists the children
it finds, recording the parent; a match whose children cannot be listed keeps
its own row:

```shell
$> datatrail ls --match gain --expand
                    Datatrail: Dataset Map
+-----------------------------+---------------+---------------+
| Scope                       | Dataset       | Parent        |
+-----------------------------+---------------+---------------+
| chime.acquisition.processed | complex_gains |               |
+-----------------------------+---------------+---------------+
| gbo.acquisition.processed   | 20230716      | complex_gains |
| gbo.acquisition.processed   | 20230715      | complex_gains |
| ...                         | ...           | ...           |
+-----------------------------+---------------+---------------+
```

Rows reached through a parent resolve directly with
`datatrail ps <scope> <dataset>`; a row kept for a matched dataset whose
children could not be listed (or that has none) may still be a container.

!!! warning "Incomplete maps"

    If Datatrail does not answer for a scope or dataset during the walk, the
    map is reported as **incomplete** and the unanswered queries are listed,
    rather than silently showing them as empty. With `--json`, those queries
    appear in the `failed` list. A partial map still exits 0; a map with **no**
    rows and unanswered queries exits 1, since nothing was determined.

With `--json`, the map is emitted as structured rows for scripting; `parent`
is `null` for rows that were not reached through `--expand`:

```bash
$ datatrail ls --match gain --expand --json
{
  "results": [
    {
      "scope": "gbo.acquisition.processed",
      "dataset": "20230525",
      "parent": "complex_gains"
    },
    ...
  ],
  "failed": []
}
```

## 🤖 Machine-readable JSON output

The `--json` flag outputs structured JSON instead of formatted tables, making it easy to parse the output in scripts and pipelines:

```bash
# Get all scopes as JSON
$ datatrail ls --json
{
  "scopes": [
    "chime.event.baseband.raw",
    "chime.event.intensity.raw",
    "kko.acquisition.processed",
    ...
  ]
}

# Get larger datasets as JSON
$ datatrail ls kko.scheduled.baseband.raw --json
{
  "scope": "kko.scheduled.baseband.raw",
  "larger_datasets": [
    "20230804095251",
    "scheduled.commissioning.steady"
  ]
}

# Get child datasets as JSON
$ datatrail ls kko.scheduled.baseband.raw scheduled.commissioning.steady --json
{
  "datasets": [
    "20230616150511",
    "20230604135840",
    "20230604134842",
    ...
  ]
}
```

### Usage in scripts

```python
import json
import subprocess

# Get all scopes
result = subprocess.run(["datatrail", "ls", "--json"], capture_output=True, text=True)
data = json.loads(result.stdout)
scopes = data["scopes"]

# Get datasets for a scope
result = subprocess.run(
    ["datatrail", "ls", "chime.event.baseband.raw", "--json"],
    capture_output=True,
    text=True,
)
data = json.loads(result.stdout)
larger_datasets = data["larger_datasets"]
```
