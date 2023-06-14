# Datatrail CLI

!!! example "Installation"

    The Datatrail CLI can be installed from PYPI using pip:

    ``` shell
    pip install datatrail-cli
    ```

    It can also be installed from source using git and poetry:

    ``` shell
    git clone ssh+git://git@github.com/chimefrb/datatrail-cli
    cd datatrail-cli

    # If you don't have Poetry:
    pip install poetry

    poetry install --without docs
    ```

## A CLI to interact with files registered in Datatrail

In order to fully utilise this CLI, you must have an account with
[CANFAR](https://www.canfar.net) and access to the either of the following
groups: `chime-frb-ro` or `chime-frb-rw`.

## Initialising the CLI

This CLI make use of a configuration file, normally placed in the '.datatrail'
directory in `$HOME`. To create a configuration file, use the command
`datatrail config init --site {SITE}`, where `{SITE}` is 'local', 'chime', or
one of the outrigger sites. See below for a guide for each of the sites.

=== "Local"

    ``` shell
    # Create Datatrail config file
    datatrail config init --site local
    
    # Ensure valid CADC Certificate exists
    cadc-get-cert -u [username]
    ```

=== "CANFAR"

    The Configuration steps at CANFAR are similar to the local configuration.
    One notable exception is that after installation, the `datatrail` command
    may not be in the PATH. It is installed to `~/.local/bin`, in which case
    you may need to add it to your PATH or prepend it to the follwing commands.
    
    ``` shell
    # Create Datatrail config file
    datatrail config init --site canfar
    
    # Ensure valid CADC Certificate exists
    cadc-get-cert -u [username]
    ```

=== "CHIME"

    ``` shell
    # Create Datatrail config file
    datatrail config init --site chime
    
    # Ensure valid CADC Certificate exists
    cadc-get-cert -u [username]
    ```

=== "KKO"

    ``` shell
    # Create Datatrail config file
    datatrail config init --site kko
    
    # Ensure valid CADC Certificate exists
    cadc-get-cert -u [username]
    ```

=== "GBO"

    ``` shell
    # Create Datatrail config file
    datatrail config init --site gbo
    
    # Ensure valid CADC Certificate exists
    cadc-get-cert -u [username]
    ```

=== "HCO"

    ``` shell
    # Create Datatrail config file
    datatrail config init --site hco
    
    # Ensure valid CADC Certificate exists
    cadc-get-cert -u [username]
    ```

## Commands

The commands available to you are:

- `list`: This list either the 'scopes' available or all of the datasets
    belonging to the given dataset.
- `ps`: This provides detailed information for the given 'scope' and 'dataset'
    combination.
- `pull`: This allows you to download all files belonging to the 'scope' and
'dataset' provided.
- `clear`: This removes all files belonging to the 'scope' and 'dataset', only
available for the local and canfar sites.
- `config`: Edit the `.datatrail/config.yaml` configuration file.
- `version`: List the CLI and server version.

Detailed information on all of the CLI commands can be found on the
[Reference](cli) page.
