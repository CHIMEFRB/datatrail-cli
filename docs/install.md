# 🛠️ Installation

There are two ways to install the Datatrail CLI:

=== "PYPI"

    ### Install from PYPI

    The Datatrail CLI can be installed from PYPI using pip:

    !!! example "pip"
    
        ```shell
        pip install datatrail-cli
        ```

=== "GitHub"

    ### Clone the repository

    The Datatrail CLI can be installed from source using git to download from
    GitHub and pip to install:

    !!! example "git+pip"
    
        ```shell
        git clone https://github.com/CHIMEFRB/datatrail-cli
        cd datatrail-cli
        pip install .
        ```

    It can also be installed from source using git and poetry:

    !!! example "git+poetry"

        ``` shell
        git clone ssh+git://git@github.com/chimefrb/datatrail-cli
        cd datatrail-cli
        poetry install --without docs
        ```
