# Registration and early access to an event

Datatrail registration records a dataset and its files. Replication copies the
registered files to another storage element such as Minoc, where they become
accessible from CANFAR. A successful registration request does not mean that a
transfer has finished.

## Check an event first

Use the ordinary CLI to inspect the event before requesting more work:

```bash
datatrail unregistered search EVENT_ID
datatrail ps SCOPE EVENT_ID
```

Replace `EVENT_ID` with the event number and `SCOPE` with the event's actual
scope, for example `chime.event.baseband.raw`. A recorded
registration failure can identify a missing classification, missing parent
dataset, or another problem that submitting the same request will not fix.

The normal date-based registration schedule leaves time for human
classification. An authorized on-site operator can submit one event earlier
with the `datatrail-admin` tools. This uses the site's existing service
configuration and data mounts; installing `datatrail-cli` on CANFAR alone does
not grant that access.

## On-site operator workflow

The administrator command and its preview/status options are documented in the
[manual registration runbook](https://github.com/CHIMEFRB/datatrail/blob/main/docs/services/manual-registration.md).
Use a released administrator image containing those options, and run
`datatrail-admin registration single-dataset --help` to check the installed
version's interface.

Confirm that data capture has finished and the source files are fully written.
Inside the authorized site's configured registration environment:

```bash
datatrail-admin registration single-dataset chime baseband --name EVENT_ID --dry-run
datatrail-admin registration single-dataset chime baseband --name EVENT_ID
datatrail-admin registration status chime baseband --name EVENT_ID
```

The preview identifies the source files and intended registration without
submitting work. Review it before confirming the second command. An accepted
request enters the registration queue; classification, registration, and
policy-driven replication can still fail or remain pending afterward.

For a dataset outside the usual classification rules, an operator may select an
existing parent dataset with approved policies using the administrator
workflow. Review the parent and its retention/replication policies explicitly.
The command does not create new policies or guarantee a transfer deadline.

Do not delete local completion markers or repeatedly resubmit a request to
speed up replication. Inspect its status and failure reason first. Once the
recorded Minoc replicas are available, use the normal [`pull`](pull.md) or
[`pull-manifest`](pull-manifest.md) workflow on CANFAR.

## Registration service alerts

`datatrail doctor` checks the CLI configuration and service readiness when you
run it. Continuous registration monitoring belongs to the site's deployed
monitoring service. Operators should configure the expected workers, alert
routing, and failure/recovery tests described in the
[registration monitoring runbook](https://github.com/CHIMEFRB/datatrail/blob/main/docs/services/registration_monitoring.md).

A missing or stale worker and a running worker that stops making progress are
different failures. An alert should identify the affected site and worker and
provide its restart/escalation instructions. Alert delivery must be tested in
the deployed environment before relying on it.
