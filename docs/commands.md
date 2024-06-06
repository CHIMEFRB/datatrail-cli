<div align="center">
    <img src="../images/Datatrail-logo.png" width="110", height="100">
</div>

<h1 align="center">Commands</h1>

The commands available to you are:

- `clear`: This removes all files belonging to the 'scope' and 'dataset', only
  available for the local and canfar sites.
- `config`: Edit the `.datatrail/config.yaml` configuration file.
- `list`: This list either the 'scopes' available or all of the datasets
  belonging to the given dataset.
- `ps`: This provides detailed information for the given 'scope' and 'dataset' combination.
- `pull`: This allows you to download all files belonging to the 'scope' and
  'dataset' provided.
- `scout`: This command provides an overview of what the Datatrail database
  thinks is the current number of files for a given dataset at each storage
  element, compared to what is observed. If a discrepancy is found at Minoc,
  the user can choose to create the file replicas missing for Minoc.
- `version`: List the CLI and server version.

Detailed information on all of the CLI commands can be found on the
[Reference](cli) page.
