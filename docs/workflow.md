# 🔁 In Workflow pipelines

`dtcli.workflow` has `pull` and `clear` as Python functions for Workflow pipeline
steps. A function runs in the step's own session, so what the command prints is in
the step's logs. Each one checks what the command did and raises if it failed, so
the step fails too: `datatrail pull` reports some failures (no CADC certificate,
minoc down, no files found) only on the console.

They return `(results, products, plots)`, as Workflow expects of a function.

## `pull_dataset`

Downloads a dataset, then checks that all its files are here.

```yaml
work:
  function: dtcli.workflow.pull_dataset
  parameters:
    scope: chime.event.baseband.raw
    dataset: "123456789"
    cores: 4
    site: canfar
```

- `cores`: parallel fetch processes (default 1).
- `site`: where it runs. If there's no Datatrail configuration, one is created
  for this site (as `datatrail config init --site <site>`); if there is one for
  another site, the step fails.
- `verbose`: 1 for INFO (default), 2 for DEBUG.

Results: `scope`, `dataset`, `files` (how many are here) and `directory`.

## `clear_dataset`

Deletes a dataset's local copy, then checks that it's gone. A dataset with no local
copy is left as it is, and the step succeeds, so it can clean up after a pull that
failed.

```yaml
work:
  function: dtcli.workflow.clear_dataset
  parameters:
    scope: chime.event.baseband.raw
    dataset: "123456789"
    site: canfar
```

- `clear_parents`: also delete empty parent directories (default false).
- `site` and `verbose` as for `pull_dataset`.

Results: `scope`, `dataset`, `path` and `cleared` (false if there was nothing to
clear).
