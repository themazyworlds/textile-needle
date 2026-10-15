"""
needle.tiers - Execution privilege and capability tier definitions.
"""

from enum import StrEnum
from typing import Any


class CapabilityTier(StrEnum):
    """Execution risk & privilege tiers for Textile Strands."""

    OBSERVE = "observe"  # Read-only telemetry, state inspection, queries, logs
    INTERACT = "interact"  # Desktop GUI interactions, window focus, visual notifications
    MUTATE = "mutate"  # File modifications, killing user processes, local workspace changes
    PRIVILEGED = "privileged"  # System configuration, package installs, D-Bus system calls, Polkit
    SYSTEM_EXEC = "system_exec"  # Arbitrary shell command execution (auto-isolated)


def parse_capability_tier(raw_tier: Any, strand_name: str = "") -> CapabilityTier:
    """Parse and validate a capability tier value, failing closed on invalid tiers."""
    if isinstance(raw_tier, CapabilityTier):
        return raw_tier
    if isinstance(raw_tier, str):
        try:
            return CapabilityTier(raw_tier.strip().lower())
        except ValueError:
            pass
    raise ValueError(
        f"Strand '{strand_name or 'unknown'}' must declare a valid CapabilityTier "
        f"(e.g. CapabilityTier.OBSERVE, CapabilityTier.INTERACT, CapabilityTier.MUTATE, "
        f"CapabilityTier.PRIVILEGED, or CapabilityTier.SYSTEM_EXEC)."
    )
