"""
needle.layers - Layer priority thresholds and constants.
Yarns use integer layers (e.g. 0 to 1000) where higher numbers deterministically
override lower layers for capability resolution.
"""

from __future__ import annotations

DEFAULT_LAYER: int = 50

__all__ = ["DEFAULT_LAYER"]
