# 🕵️ Investigating a dataset with scout

<!-- termynal -->
```bash
❯ datatrail scout --help
Usage: datatrail scout [OPTIONS] DATASET [SCOPES]...

  Scout a dataset.

Options:
  -v, --verbose  Verbosity: v=INFO, vv=DEBUG.
  -q, --quiet    Set log level to ERROR.
  --help         Show this message and exit.
```

## Overview

The purpose of this function is the give users easy visibility into the
current situation for a given dataset across all of Datatrail's storage
elements. The number of datasets that information is given for depends on the
number of scopes that the given dataset name has registered. However, this
can be filtered by providing a list of scopes to the command.

## Usage

Below is an example of the output for the dataset named `382085503`, both
filtered to only show information for the `chime.event.baseband.raw` scope
and unfiltered.

!!! note
    The output below does not show the correct colouring. The rows of the table
    are colour-coded to indicate if it is observed or expected. Observed
    values are displayed in blue and expected values are in yellow.

=== "Filtering by scope"

    ```bash
    ❯ datatrail scout 382085503 chime.event.baseband.raw
                              Scout Results for 382085503
    ┏━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━┳━━━━━┳━━━━━┳━━━━━━━┓
    ┃ Scope                    ┃ chime ┃ baseband_buffer ┃ kko ┃ gbo ┃ hco ┃ minoc ┃
    ┡━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━╇━━━━━╇━━━━━╇━━━━━━━┩
    │ chime.event.baseband.raw │ 824   │ 0               │ 0   │ -1  │ -1  │ 824   │ # (1)!
    │ chime.event.baseband.raw │ 824   │ 0               │ 0   │ 0   │ 0   │ 824   │ # (2)!
    └──────────────────────────┴───────┴─────────────────┴─────┴─────┴─────┴───────┘
    Legend: Observed, Expected
    NOTE: In the case where more files are expected at a site other than minoc, that
    this may be due to the file type filtering when querying each site. This is a
    known limitation of the current implementation.
    ```
    
    1. The Observed number of files.
    2. The Expected number of files.

=== "Unfiltered"

    ```bash
    ❯ datatrail scout 382085503
                               Scout Results for 382085503
    ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━┳━━━━━━┳━━━━━┳━━━━━━━┓
    ┃ Scope                     ┃ chime ┃ baseband_buffer ┃ kko ┃ gbo  ┃ hco ┃ minoc ┃
    ┡━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━╇━━━━━━╇━━━━━╇━━━━━━━┩
    │ chime.event.baseband.raw  │ 824   │ 0               │ 0   │ -1   │ -1  │ 824   │
    │ chime.event.baseband.raw  │ 824   │ 0               │ 0   │ 0    │ 0   │ 824   │
    ├───────────────────────────┼───────┼─────────────────┼─────┼──────┼─────┼───────┤
    │ chime.event.intensity.raw │ 162   │ 0               │ 0   │ -1   │ -1  │ 164   │
    │ chime.event.intensity.raw │ 164   │ 0               │ 0   │ 0    │ 0   │ 164   │
    ├───────────────────────────┼───────┼─────────────────┼─────┼──────┼─────┼───────┤
    │ gbo.event.baseband.raw    │ 0     │ 0               │ 0   │ -1   │ -1  │ 1024  │
    │ gbo.event.baseband.raw    │ 0     │ 0               │ 0   │ 1024 │ 0   │ 1024  │
    └───────────────────────────┴───────┴─────────────────┴─────┴──────┴─────┴───────┘
    Legend: Observed, Expected
    NOTE: In the case where more files are expected at a site other than minoc, that this may
    be due to the file type filtering when querying each site. This is a known limitation of
    the current implementation.
    ```

!!! failure "Negative files"
    If the server encounters an error it is represented as a negative number.
    Which can occur when communicating with the mini-servers running at each
    storage element.

### Healing at Minoc
In some cases, the number of files expected at minoc may be less than the number
that actually exist there. This can occur when API requests drop, leading to an
inconsistent state in the database. When this is seen by `scout`, the command
offers to remedy the situation by adding the missing replicas.

```bash
❯ datatrail scout 383577603 chime.event.baseband.raw
                          Scout Results for 383577603
┏━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━┳━━━━━┳━━━━━┳━━━━━━━┓
┃ Scope                    ┃ chime ┃ baseband_buffer ┃ kko ┃ gbo ┃ hco ┃ minoc ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━╇━━━━━╇━━━━━╇━━━━━━━┩
│ chime.event.baseband.raw │ 702   │ 0               │ 0   │ -1  │ -1  │ 702   │
│ chime.event.baseband.raw │ 702   │ 0               │ 0   │ 0   │ 0   │ 699   │
└──────────────────────────┴───────┴─────────────────┴─────┴─────┴─────┴───────┘
Legend: Observed, Expected
NOTE: In the case where more files are expected at a site other than minoc, that this may
be due to the file type filtering when querying each site. This is a known limitation of
the current implementation.

Scopes with minoc discrepancy:
 - chime.event.baseband.raw

Would you like to attempt to heal this discrepancy? [y/n]: y
chime.event.baseband.raw - Healing successful.
```
