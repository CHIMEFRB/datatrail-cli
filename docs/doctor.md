# Check readiness with `doctor`

Use `doctor` when a command cannot connect, authentication fails, or you want to
check your setup before downloading data:

```bash
datatrail doctor
```

The command reads your existing CLI configuration and certificate, then checks
Datatrail, Minoc, and Luskan. See [initial setup](initialising.md) if you have not
configured the CLI or obtained a CADC certificate.

## Understand the checks

The text report prints one line per check, labeled `OK` or `FAILED`:

| Check | What must pass |
| --- | --- |
| `config` | The configuration loads and contains a server URL, certificate path, site, and root mount for that site. |
| `server` | The configured Datatrail server returns a valid, healthy `/health/check` report, including database and API status. |
| `certificate` | The configured certificate is readable PEM and its validity period includes the current time. |
| `minoc` | Minoc's capabilities endpoint responds successfully and confirms authentication with the certificate. |
| `luskan` | Luskan's capabilities endpoint responds successfully and confirms authentication with the certificate. |

If configuration fails, the remaining readiness checks are skipped. If the
certificate fails, the Minoc and Luskan checks are skipped. Skipped checks appear
as `FAILED` with a message explaining why they were not checked; they do not
independently establish that a service is down.

A successful report confirms these readiness checks at that moment. It does not
prove permission to read every dataset, verify file contents, or continuously
monitor registration workers. The command does not change configuration, renew
certificates, or download datasets.

## Use the result in a script

```bash
datatrail doctor --json > doctor.json
```

`--json` replaces the text report with a JSON object on standard output. It has a
top-level `ok` boolean and a `checks` object containing `config`, `server`,
`certificate`, `minoc`, and `luskan`. Each check contains its own `ok` boolean and
`message`. The report is still written when a check fails.

| Exit status | Meaning |
| --- | --- |
| `0` | Every readiness check passed. |
| `1` | At least one readiness check failed or was skipped. |

Address the first relevant failure: review [configuration and certificate setup](initialising.md)
for local problems, or share the failed check and message with the service operator.
Run `doctor` again after addressing the cause. For dataset metadata checks, use
[`verify`](verify.md).
