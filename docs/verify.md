# Compare registered Minoc files with `verify`

Use `verify` to check whether the Minoc files recorded by Datatrail have consistent
metadata in Minoc and the Luskan inventory. Datatrail supplies the file list;
`verify` compares the sizes and MD5 checksums reported by the two CADC services.

```bash
datatrail verify chime.event.baseband.raw EVENT_ID
```

Replace the scope and `EVENT_ID` with your dataset's actual identifiers. The CLI
needs its normal configuration and a valid CADC certificate with service access.
Use [`doctor`](doctor.md) to troubleshoot configuration or authentication first.

## Read the results

The report starts with the scope, dataset, and `registered` count: the number of
unique Minoc file URIs returned by Datatrail. It then shows these result counts
and lists the URIs with problems:

| Result | Meaning |
| --- | --- |
| `present` | Both services returned complete, matching size and checksum metadata. |
| `missing` | A successful metadata lookup did not return the registered URI from Minoc, Luskan, or both. |
| `size-mismatch` | Both sizes are available, but their byte counts differ. |
| `checksum-mismatch` | Both MD5 values are available, but they differ. |
| `unavailable` | A service request failed, a response was invalid, or required metadata was incomplete. The comparison could not be completed. |

One file can have more than one problem, so problem counts need not add up to
`registered`. An unavailable lookup is not reported as proof that a file is
missing.

!!! note "An empty check can succeed"

    If Datatrail returns no registered Minoc files, the command reports
    `registered: 0` and succeeds. This does not establish that the dataset has
    been replicated. Inspect its recorded locations with [`ps`](ps.md).

This command reads metadata; it does not download files, recompute checksums from
their contents, or repair registrations. It checks only the registered Minoc
URIs supplied by Datatrail, so it does not discover unregistered files or verify
other storage elements. Matching service metadata is not a fresh integrity check
of the stored bytes.

## Save a detailed report

```bash
datatrail verify chime.event.baseband.raw EVENT_ID --json > verification.json
```

`--json` writes a JSON object on standard output, including on verification
failure. It contains `scope`, `dataset`, `registered`, `ok`, `summary`, and
`results`. The category keys use underscores (`size_mismatch` and
`checksum_mismatch`). Detailed results identify the URI, affected services, or
the differing Minoc and Luskan values as appropriate.

| Exit status | Meaning |
| --- | --- |
| `0` | No missing files, mismatches, or unavailable metadata were reported; this includes an empty registered file list. |
| `1` | Missing files or metadata mismatches were found, with no unavailable results. |
| `2` | At least one result was unavailable, even if other files also had mismatches. |

For unavailable results, check service readiness and retry after the underlying
problem is resolved. For missing files or mismatches, retain the detailed report
and investigate the dataset with [`ps`](ps.md) and [`scout`](scout.md) before
requesting corrective work.
