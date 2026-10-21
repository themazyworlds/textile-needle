"""
needle.models - Lightweight data models for Strands and schema specifications.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from needle.tiers import CapabilityTier


@dataclass(slots=True)
class Strand:
    """Represents a single callable tool/strand exposed by a Yarn."""

    name: str
    description: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    required: list[str] = field(default_factory=list)
    handler: Callable[..., Any] | None = None
    raw_handler: Callable[..., Any] | None = None
    capability: str | None = None
    args_schema: Any = None
    tier: CapabilityTier = CapabilityTier.INTERACT
    resources: list[str] = field(default_factory=list)
    timeout: float | None = 30.0
    no_timeout: bool = False
    reason: str | None = None
    fallback: Any = None

    def to_mcp_definition(self) -> dict[str, Any]:
        """Convert strand schema into Model Context Protocol format."""
        tier_str = str(self.tier.value).upper() if hasattr(self.tier, "value") else str(self.tier).upper()
        desc = f"[Capability Tier: {tier_str}] {self.description}".strip()
        schema = (
            self.args_schema.model_json_schema()
            if hasattr(self.args_schema, "model_json_schema")
            else {
                "type": "object",
                "properties": self.parameters,
                "required": self.required,
                "additionalProperties": False,
            }
        )
        return {
            "name": self.name,
            "description": desc,
            "input_schema": schema,
            "inputSchema": schema,
        }


__all__ = ["Strand"]
