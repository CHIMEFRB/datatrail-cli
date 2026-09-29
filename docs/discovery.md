# Discover datasets recursively

Use `datatrail list` (or its alias `datatrail ls`) when you know part of a
dataset name but not where it sits in the hierarchy. Choose how far to explore:

- `--match`: Select larger datasets using comma-separated, case-insensitive
  terms. Every term must appear in the combined scope and dataset name.
- `--expand`: Open each selected larger dataset one level and list its children.
- `--recursive`: Follow descendants to terminal datasets and record the path
  to each result.

## Start with a bounded search

For example, find gain datasets within one scope:

```shell
datatrail ls gbo.acquisition.processed --match gains
```

To inspect one level of children, add `--expand`:

```shell
datatrail ls gbo.acquisition.processed --match gains --expand
```

To continue through nested datasets, use `--recursive` instead:

```shell
datatrail ls gbo.acquisition.processed --match gains --recursive
```

You can omit the scope to search across scopes, but `--expand` and `--recursive`
then require `--match` to bound the search. Matching selects the starting larger
datasets; descendants are followed even if their own names do not contain the
search terms.

The recursive walk visits each dataset once, so shared descendants are not
repeated and cycles cannot loop forever. It retains the first path found in
sorted order. A dataset with an answered empty child list is terminal.

## Save discovery results for a script

```shell
datatrail ls gbo.acquisition.processed --match gains --recursive --json > datasets.json
```

The JSON map contains `results` and `failed`. Each recursive result records its
`scope`, `dataset`, `parent`, and `path`. See the [list guide](list.md) for output
examples and ordinary scope or child-dataset queries. A top-level failure can
return an `error` object instead of a map and exits `1`, so check the process
status before reading the result fields.

!!! warning "Check for incomplete discovery"

    An unanswered branch is retained as a partial row and recorded in `failed`.
    A partial map with rows still exits `0`; no rows plus unanswered queries exits
    `1`. Scripts that require complete results must also check that `failed` is
    empty.

## Turn discovery into a resumable download

`list --recursive` maps datasets. Use [`inventory`](inventory.md) when you also
need their file replica URIs saved in a durable manifest:

```shell
datatrail inventory gbo.acquisition.processed --match gains --output gains-inventory.json
datatrail pull-manifest gains-inventory.json --directory ./gains --cores 4
```

An inventory can resume unfinished queries. [`pull-manifest`](pull-manifest.md)
tracks completed transfers in a separate state file so a later run can continue
without repeating completed downloads. Read both guides for incomplete results,
state-file ownership, and transfer behavior.
