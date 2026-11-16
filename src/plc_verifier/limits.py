"""Byte budgets for distinct representations (not interchangeable)."""

import json

from .language import VerificationError

TRACE_BYTES = 16 * 1024 * 1024
RESULT_BYTES = 32 * 1024 * 1024
HTTP_REQUEST_BYTES = RESULT_BYTES + 1024 * 1024
FORMAT_BYTES = {
    "json": RESULT_BYTES,
    "html": 128 * 1024 * 1024,
    "csv": 64 * 1024 * 1024,
    "xml": 8 * 1024 * 1024,
}


def compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def bounded(text: str, limit: int, label: str) -> str:
    if len(text.encode("utf-8")) > limit:
        raise VerificationError(f"{label} exceeds {limit} UTF-8 bytes; nothing truncated")
    return text
