from __future__ import annotations

from dataclasses import dataclass


class AdapterError(RuntimeError):
    pass


@dataclass
class FetchResult:
    products: list[dict]
    pages: int


def float_or_none(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
