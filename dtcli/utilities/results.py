"""Shared command result helpers."""

from typing import Any, Dict


def failure(message: object, code: str, retryable: bool) -> Dict[str, Any]:
    """Return a stable error result without changing the legacy message."""
    return {
        "error": str(message),
        "error_code": code,
        "retryable": bool(retryable),
    }
