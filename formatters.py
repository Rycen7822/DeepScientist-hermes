"""Formatting helpers for compact DeepScientist plugin outputs."""

from __future__ import annotations

from typing import Any

MAX_TEXT = 12000


def compact_text(text: str, *, limit: int = MAX_TEXT) -> str:
    value = str(text or "")
    if len(value) <= limit:
        return value
    omitted = len(value) - limit
    return value[:limit] + f"\n...[truncated {omitted} chars]"


def compact_payload(payload: dict[str, Any]) -> dict[str, Any]:
    result = dict(payload)
    for key in ("stdout", "stderr"):
        if key in result:
            result[key] = compact_text(str(result[key]))
    return result
