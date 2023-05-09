"""Utility functions."""

from typing import Any, Dict, List, Union

from requests.models import Response


def decode_response(response: Response) -> Union[Dict, str]:
    """Decode response.

    Args:
        response (Response): Request response.

    Returns:
        Union[Dict, str]: JSON response or text.
    """
    if response.status_code in [200, 201]:
        return response.json()
    else:
        return response.text


def split(data: List[Any], count: int) -> List[List[Any]]:
    """Split a list into batches.

    Args:
        data (List[Any]): List to split.
        count (int): Number of batches to split into.

    Returns:
        List[List[Any]]: List of batches.
    """
    batch_size = len(data) // count
    remainder = len(data) % count
    batches: List[Any] = []
    idx = 0
    for i in range(count):
        if i < remainder:
            batch = data[idx : idx + batch_size + 1]  # noqa: E203
            idx += batch_size + 1
        else:
            batch = data[idx : idx + batch_size]  # noqa: E203
            idx += batch_size
        if len(batch) > 0:
            batches.append(batch)
    return batches
