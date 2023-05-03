"""Utility functions."""

from requests.models import Response


def decode_response(response: Response):
    """Decode response."""
    if response.status_code in [200, 201]:
        return response.json()
    else:
        return response.text
