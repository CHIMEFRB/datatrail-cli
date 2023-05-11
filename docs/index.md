# Datatrail CLI

!!! example "Installation"

    The Datatrail CLI can be installed using pip:

    ``` shell
    pip install datatrail-cli
    ```

    It can also be installed from source using git and poetry:

    ``` shell
    git clone ssh+git://git@github.com/chimefrb/datatrail-cli

    # If you don't have Poetry:
    pip install poetry

    poetry install --without docs
    ```

## A CLI to interact with files registered in Datatrail

In order to fully utilise this CLI, you must have an account with [CANFAR](https://www.canfar.net) and access to the either of the following groups: `chime-frb-ro` or `chime-frb-rw`.

## Initialising the CLI

This CLI make use of a configuration file, normally placed in the '.datatrail' directory in `$HOME`. To create a configuration file, use the command `datatrail config init --site {SITE}`, where `{SITE}` is 'local', 'chime', or one of the outrigger sites.

## Commands

The commands available to you are:

- `list`: This list either the 'scopes' available or all of the datasets belonging to the given dataset.
- `ps`: This provides detailed information for the given 'scope' and 'dataset' combination.
- `pull`: This allows you to download all files belonging to the 'scope' and 'dataset' provided.

Detailed information on all of the CLI commands can be found on the [Reference](cli) page.
