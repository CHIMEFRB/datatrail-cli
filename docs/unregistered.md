# 🚧 Inspecting failures with `unregistered`

<!-- termynal -->

```bash
❯ datatrail unregistered --help
Usage: datatrail unregistered [OPTIONS] COMMAND [ARGS]...

  Commands related to unregistered datasets.

Options:
  --help  Show this message and exit.

Commands:
  search   Check whether an event is an unregistered dataset.
  summary  Summarise the reasons for unregistered datasets.
```

## Overview

When Datatrail cannot register a dataset, the attempt is recorded in the
unregistered datasets bucket along with the reason it failed. The
`unregistered` commands let you inspect that bucket, either as a whole with
`summary`, or for a single event with `search`.

This is usually the first place to look when an event you expect to find with
[`scout`](scout.md) or [`ps`](ps.md) is missing entirely from Datatrail.

## `search`

```bash
❯ datatrail unregistered search --help
Usage: datatrail unregistered search [OPTIONS] EVENT

  Check whether an event is an unregistered dataset.

Options:
  -s, --scope TEXT  Only search within this scope.
  -p, --partial     Match events containing EVENT.
  -v, --verbose     Verbosity: v=INFO, vv=DEBUG.
  -q, --quiet       Only errors shown in logs.
  --json            Output as JSON.
  --help            Show this message and exit.
```

`search` answers the question "why is this event not in Datatrail?". Each
record found is shown as a separate block, most recently recorded first,
detailing the scope and site the registration was attempted for, the parent
dataset it was to be attached to, and the reason the attempt failed.

An event can have more than one record, e.g. one per site, or one per failed
attempt.

=== "All scopes"

    ```bash
    ❯ datatrail unregistered search 1172713191
                       ⚠ 1172713191 is an unregistered dataset ⚠
                                    4 records found.
    Event           1172713191
    Scope           hco.event.baseband.raw
    Site            hco
    Parent dataset  CHAMPS_Localization.J0408
    Recorded        2026-08-08 19:15 UTC
    Reason          Could not attach datasets: 1172713191 and
                    CHAMPS_Localization.J0408. ERROR: dataset
                    CHAMPS_Localization.J0408, hco.event.baseband.raw not found..

    Event           1172713191
    Scope           gbo.event.baseband.raw
    Site            gbo
    Parent dataset  CHAMPS_Localization.J0408
    Recorded        2026-08-08 19:09 UTC
    Reason          Could not attach datasets: 1172713191 and
                    CHAMPS_Localization.J0408. ERROR: dataset
                    CHAMPS_Localization.J0408, gbo.event.baseband.raw not found..

    Event           1172713191
    Scope           kko.event.baseband.raw
    Site            kko
    Parent dataset  CHAMPS_Localization.J0408
    Recorded        2026-08-08 18:54 UTC
    Reason          Could not attach datasets: 1172713191 and
                    CHAMPS_Localization.J0408. ERROR: dataset
                    CHAMPS_Localization.J0408, kko.event.baseband.raw not found..

    Event           1172713191
    Scope           chime.event.intensity.raw
    Site            chime
    Parent dataset  CHAMPS_Localization.J0408
    Recorded        2026-08-08 14:28 UTC
    Reason          Could not attach datasets: 1172713191 and
                    CHAMPS_Localization.J0408. ERROR: dataset
                    CHAMPS_Localization.J0408, chime.event.intensity.raw not
                    found..
    ```

=== "Filtering by scope"

    ```bash
    ❯ datatrail unregistered search 1172713191 --scope kko.event.baseband.raw
                       ⚠ 1172713191 is an unregistered dataset ⚠
                                    1 record found.
    Event           1172713191
    Scope           kko.event.baseband.raw
    Site            kko
    Parent dataset  CHAMPS_Localization.J0408
    Recorded        2026-08-08 18:54 UTC
    Reason          Could not attach datasets: 1172713191 and
                    CHAMPS_Localization.J0408. ERROR: dataset
                    CHAMPS_Localization.J0408, kko.event.baseband.raw not found..
    ```

=== "No records found"

    ```bash
    ❯ datatrail unregistered search 382085503
    382085503 is not an unregistered dataset.
    Use --partial to search for events containing this name.
    ```

### Partial matches

By default the event name has to match exactly. With `--partial`, any event
name _containing_ the given string is returned, which is useful when you only
know part of the name, or when you want to check a whole family of events such
as a set of commissioning datasets.

```bash
❯ datatrail unregistered search 11728169 --partial
                    ⚠ 11728169 is an unregistered dataset ⚠
                                2 records found.
Event           1172816953
Scope           chime.event.intensity.raw
Site            chime
Parent dataset  CHAMPS_Localization.J0408
Recorded        2026-08-09 11:14 UTC
Reason          Could not attach datasets: 1172816953 and
                CHAMPS_Localization.J0408. ERROR: dataset
                CHAMPS_Localization.J0408, chime.event.intensity.raw not
                found..

Event           1172816944
Scope           chime.event.intensity.raw
Site            chime
Parent dataset  CHAMPS_Localization.J0408
Recorded        2026-08-09 10:16 UTC
Reason          Could not attach datasets: 1172816944 and
                CHAMPS_Localization.J0408. ERROR: dataset
                CHAMPS_Localization.J0408, chime.event.intensity.raw not
                found..
```

!!! note "Result limit"

    A maximum of 100 records are returned. If you hit that limit with
    `--partial`, narrow the search with a longer event name or a `--scope`.

### Machine readable output

`--json` prints the full records, including fields not shown in the table,
which is handy for scripting or for piping into `jq`.

```bash
❯ datatrail unregistered search 1172713191 --scope kko.event.baseband.raw --json
{
  "event": "1172713191",
  "scope": "kko.event.baseband.raw",
  "partial": false,
  "unregistered": [
    {
      "dataset_name": "1172713191",
      "dataset_scope": "kko.event.baseband.raw",
      "storage_name": "kko",
      "storage_element_captured_at": "kko",
      "attach_to_dataset": "CHAMPS_Localization.J0408",
      "reason": "Could not attach datasets: 1172713191 and CHAMPS_Localization.J0408. ERROR: dataset CHAMPS_Localization.J0408, kko.event.baseband.raw not found..",
      "associated_event": {},
      "locked": false
    }
  ]
}
```

!!! tip "Errors in JSON mode"

    With `--json`, a failed query is reported as `{"error": "..."}` on stdout
    and the command exits with status `1`, so failures can be detected in a
    pipeline.

## `summary`

```bash
❯ datatrail unregistered summary --help
Usage: datatrail unregistered summary [OPTIONS]

  Summarise the reasons for unregistered datasets.

Options:
  -v, --verbose  Verbosity: v=INFO, vv=DEBUG.
  -q, --quiet    Only errors shown in logs.
  --help         Show this message and exit.
```

`summary` groups every record in the bucket by the reason it failed, giving an
overview of what is currently going wrong. Reasons are grouped into categories,
e.g. `ATTACH_MISSING` for datasets whose parent dataset does not exist, or
`POSTGRES` for database errors.

```bash
❯ datatrail unregistered summary
                 Summary of reasons — 886 unregistered datasets
┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━┓
┃ Category         ┃ Detail                                    ┃ Count ┃     % ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━┩
│ POSTGRES         │ (psycopg2.errors.UniqueViolation)         │   627 │ 70.8% │
│                  │ duplicate key value violates unique       │       │       │
│                  │ constraint "name_se_captured_at_pair"     │       │       │
│                  │ DETAIL: Key                               │       │       │
├──────────────────┼───────────────────────────────────────────┼───────┼───────┤
│ STATUS           │ (no reason recorded)                      │   110 │ 12.4% │
│                  │ event-missing-verification                │    85 │  9.6% │
│                  │ pending-tsar-classification               │    23 │  2.6% │
├──────────────────┼───────────────────────────────────────────┼───────┼───────┤
│ ATTACH_MISSING   │ CHAMPS_Localization.J0408 →               │    18 │  2.0% │
│                  │ chime.event.intensity.raw                 │       │       │
│                  │ outrigger.commissioning.B0834 →           │    12 │  1.4% │
│                  │ chime.event.baseband.raw                  │       │       │
├──────────────────┼───────────────────────────────────────────┼───────┼───────┤
│ CREATE_DUPLICATE │ <ID> → chime.event.baseband.raw           │     3 │  0.3% │
└──────────────────┴───────────────────────────────────────────┴───────┴───────┘
```

For `ATTACH_MISSING` and `CREATE_DUPLICATE`, the detail column reads as
`dataset → scope`. In the `CREATE_DUPLICATE` case the digits of the dataset
name are replaced with `<ID>`, so that the same failure for many events is
counted as a single row.
