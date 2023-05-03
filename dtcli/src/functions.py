import requests
from chime_frb_api import get_logger

from dtcli import SERVER
from dtcli.utilities import utilities

logger = get_logger()


def ps(scope: str, dataset: str, base_url: str = SERVER):
    """List detailed information about a dataset."""
    # TODO: This command should list the files and policies of a dataset.
    try:
        payload = {"scope": scope, "name": dataset}
        url = base_url + "/query/dataset/find"
        r = requests.post(url, json=payload)
        files_response = utilities.decode_response(r)

        url = base_url + f"/query/dataset/{scope}/{dataset}"
        r = requests.get(url)
        policy_response = utilities.decode_response(r)

        return files_response, policy_response

    except requests.exceptions.ConnectionError as e:
        logger.error(e)
        return "Datatrail Server at CHIME is not responding."
