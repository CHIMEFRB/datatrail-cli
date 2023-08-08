# ⚙️ Initialising the CLI

The Datatrail CLI makes use of a configuration file, placed in the '.datatrail'
directory in `$HOME`. To create a configuration file, use the command
`datatrail config init --site {SITE}`, where `{SITE}` is 'local', 'chime', or
one of the outrigger sites. See below for a guide for each of the sites.

=== "Local"

    To create a configuration file for Datatrail CLI, use the command: 

    ``` shell
    # Create Datatrail config file
    $> datatrail config init --site local
    Datatrail config file /Users/tarikzegmott/.datatrail/config.yaml created.
    ```
    
    You will now have a configuration file in `$HOME/.datatrail/config.yaml`.
    You can view the contents of the file using:

    ```shell
    $> datatrail config ls
    Filename: /Users/tarikzegmott/.datatrail/config.yaml
    {
        'root_mounts': {
            'canfar': '/arc/projects/chime_frb/',
            'chime': '/',
            'gbo': '/',
            'hco': '/',
            'kko': '/',
            'local': './'
        },
        'server': 'https://frb.chimenet.ca/datatrail',
        'site': 'local',
        'vospace_certfile': '/Users/tarikzegmott/.ssl/cadcproxy.pem'
    }
    ```

    The information you see here is basic values that the CLI will use to
    perform its operations. Particularly important, is the `vospace_certfile`
    which lists the location of your CADC Certificate. If you do not have a
    CADC Certificate, you should obtain one now.

    ```shell
    # Ensure valid CADC Certificate exists
    $> cadc-get-cert -u [username]
    tzegmott@ws.cadc-ccda.hia-iha.nrc-cnrc.gc.ca
    Password:
    
    DONE. 10 day certificate saved in /Users/tarikzegmott/.ssl/cadcproxy.pem
    ```
    
    !!! warning "CADC Certificate"
        The CADC certificate is required for the Datatrail CLI to function. Note
        that CADC certificates are valid for 10 days by default, up to a maximum
        of 30 days. You must refresh the certificate periodically.

    If you do not keep your CADC certificate in the default location, you must
    update the configuration file to pointt to the correct location.

    ```shell
    # Updating CADC Certificate location
    $> datatrail config set vospace_certificate /non/standard/location/cadcproxy.pem
    Attempting to set vospace_certificate to /non/standard/location/cadcproxy.pem
    Set vospace_certificate to /non/standard/location/cadcproxy.pem
    ```

=== "CANFAR"

    !!! note

        The Configuration steps at CANFAR are similar to the local configuration.
        One notable exception is that after installation, the `datatrail` command
        may not be in the PATH. It is installed to `~/.local/bin`, in which case
        you may need to add it to your PATH or prepend it to the follwing commands.
    
    To create a configuration file for Datatrail CLI, use the command: 

    ``` shell
    # Create Datatrail config file
    $> datatrail config init --site canfar
    Datatrail config file /arc/home/tzegmott/.datatrail/config.yaml created.
    ```
    
    You will now have a configuration file in `$HOME/.datatrail/config.yaml`.
    You can view the contents of the file using:

    ```shell
    $> datatrail config ls
    Filename: /arc/home/tzegmott/.datatrail/config.yaml
    {
        'root_mounts': {
            'canfar': '/arc/projects/chime_frb/',
            'chime': '/',
            'gbo': '/',
            'hco': '/',
            'kko': '/',
            'local': './'
        },
        'server': 'https://frb.chimenet.ca/datatrail',
        'site': 'canfar',
        'vospace_certfile': '/arc/home/tzegmott/.ssl/cadcproxy.pem'
    }
    ```

    The information you see here is basic values that the CLI will use to
    perform its operations. Particularly important, is the `vospace_certfile`
    which lists the location of your CADC Certificate. If you do not have a
    CADC Certificate, you should obtain one now.

    ```shell
    # Ensure valid CADC Certificate exists
    $> cadc-get-cert -u [username]
    tzegmott@ws.cadc-ccda.hia-iha.nrc-cnrc.gc.ca
    Password:
    
    DONE. 10 day certificate saved in /arc/home/tzegmott/.ssl/cadcproxy.pem
    ```
    
    !!! warning "CADC Certificate"
        The CADC certificate is required for the Datatrail CLI to function. Note
        that CADC certificates are valid for 10 days by default, up to a maximum
        of 30 days. You must refresh the certificate periodically.

    If you do not keep your CADC certificate in the default location, you must
    update the configuration file to pointt to the correct location.

    ```shell
    # Updating CADC Certificate location
    $> datatrail config set vospace_certificate /non/standard/location/cadcproxy.pem
    Attempting to set vospace_certificate to /non/standard/location/cadcproxy.pem
    Set vospace_certificate to /non/standard/location/cadcproxy.pem
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
