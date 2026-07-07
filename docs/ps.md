# 🔍 Detailed dataset info using `ps`

<!-- termynal -->
```bash
$ datatrail ps --help
Usage: datatrail ps [OPTIONS] SCOPE DATASET

  Details of a dataset.

Options:
  -s, --show-files  Show file names.
  -v, --verbose     Verbosity: v=INFO, vv=DEBUG.
  -q, --quiet       Set log level to ERROR.
  --json            Output as JSON.
  --help            Show this message and exit.
```

The `ps` command is used to get information about a child dataset. It can
display the datasets replication and deletion policies, in addition to the
size and number of files in the dataset.

!!! example "Dataset policies and size at minoc"

    ```shell
    $> datatrail ps kko.event.baseband.raw 308892599
       Datatrail: 308892599 kko.event.baseband.raw at Minoc
    ┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┓
    ┃ Storage Element ┃ Number of Files ┃ Size of Files [GB] ┃
    ┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━┩
    │ minoc           │ 1024            │ 5.34               │
    └─────────────────┴─────────────────┴────────────────────┘
                       Datatrail: Policies for 308892599 kko.event.baseband.raw
    ┏━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
    ┃ Policy      ┃ Storage Element                    ┃ Priority ┃ Default ┃ Delete After [days] ┃
    ┡━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
    │ Replication │ chime                              │ low      │ True    │ -                   │
    ├─────────────┼────────────────────────────────────┼──────────┼─────────┼─────────────────────┤
    │ Deletion    │ minoc                              │ low      │ True    │ 36500               │
    │             │ arc                                │ high     │ True    │ 60                  │
    │             │ chime                              │ medium   │ True    │ 90                  │
    │             │ kko                                │ medium   │ True    │ 90                  │
    ├─────────────┼────────────────────────────────────┼──────────┼─────────┼─────────────────────┤
    │ Belongs to  │ B0531+21.commissioning.pulsar.temp │          │         │                     │
    └─────────────┴────────────────────────────────────┴──────────┴─────────┴─────────────────────┘
    ```

This command is also able to display a list of files for each storage element,
if the `--show-files` or `-s` flag is passed.

!!! example "Listing dataset's files"

    ```shell
    $> datatrail ps kko.event.baseband.raw 308892599 --show-files
    ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
    ┃ Datatrail: Files for 308892599 kko.event.baseband.raw           ┃
    ┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
    │ Storage Element: minoc                                          │
    │ Common Path: data/kko/baseband/raw/2023/08/07/astro_308892599/  │
    │ - baseband_308892599_129.h5                                     │
    │ - baseband_308892599_1013.h5                                    │
    │ - baseband_308892599_171.h5                                     │
    │ - baseband_308892599_250.h5                                     │
    │ - baseband_308892599_269.h5                                     │
    │ - baseband_308892599_284.h5                                     │
    │ - baseband_308892599_295.h5                                     │
    │ - baseband_308892599_306.h5                                     │
    │ - baseband_308892599_353.h5                                     │
    │ - baseband_308892599_926.h5                                     │
    │ - baseband_308892599_933.h5                                     │
    │ - baseband_308892599_201.h5                                     │
    │ - baseband_308892599_393.h5                                     │
    │ - baseband_308892599_429.h5                                     │
    │ - baseband_308892599_542.h5                                     │
    │ - baseband_308892599_565.h5                                     │
    │ - baseband_308892599_604.h5                                     │
    │ - baseband_308892599_615.h5                                     │
    │ - baseband_308892599_657.h5                                     │
    │ - baseband_308892599_672.h5                                     │
    │ - baseband_308892599_10.h5                                      │
    │ - baseband_308892599_110.h5                                     │
    │ - baseband_308892599_111.h5                                     │
    :
    ```

## 🤖 Machine-readable JSON output

The `--json` flag outputs structured JSON instead of formatted tables, making it easy to parse dataset information in scripts and pipelines:

```bash
$ datatrail ps kko.event.baseband.raw 308892599 --json
{
  "dataset": "308892599",
  "scope": "kko.event.baseband.raw",
  "files": {
    "contains_datasets": 0,
    "datasets_contained": [],
    "file_replica_locations": {
      "minoc": [
        "data/kko/baseband/raw/2023/08/07/astro_308892599/baseband_308892599_129.h5",
        "data/kko/baseband/raw/2023/08/07/astro_308892599/baseband_308892599_1013.h5",
        ...
      ]
    }
  },
  "policies": {
    "replication_policy": {
      "preferred_storage_elements": ["chime"],
      "priority": "low",
      "default": true
    },
    "deletion_policy": [
      {
        "storage_element": "minoc",
        "priority": "low",
        "default": true,
        "delete_after_days": 36500
      },
      ...
    ],
    "belongs_to": [
      {
        "scope": "kko.event.baseband.raw",
        "name": "B0531+21.commissioning.pulsar.temp"
      }
    ]
  }
}
```

### Usage in scripts

```python
import json
import subprocess

# Get dataset information
result = subprocess.run(
    ["datatrail", "ps", "kko.event.baseband.raw", "308892599", "--json"],
    capture_output=True,
    text=True,
)
data = json.loads(result.stdout)

# Access file locations
file_locations = data["files"]["file_replica_locations"]
minoc_files = file_locations.get("minoc", [])

# Access policies
replication_policy = data["policies"]["replication_policy"]
deletion_policy = data["policies"]["deletion_policy"]
belongs_to = data["policies"]["belongs_to"]
```
