"""
needle.models - Pydantic definitions for Strands and schema specifications.
"""

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from needle.tiers import CapabilityTier


class Strand(BaseModel):
    """Represents a single callable tool/strand exposed by a Yarn."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    description: str = ""
    parameters: dict[str, Any] = Field(default_factory=dict)
    required: list[str] = Field(default_factory=list)
    handler: Callable[..., Any] | None = None
    raw_handler: Callable[..., Any] | None = None
    capability: str | None = None
    args_schema: type[BaseModel] | None = None
    tier: CapabilityTier = CapabilityTier.INTERACT
    resources: list[str] = Field(default_factory=list)
    timeout: float | None = 30.0
    no_timeout: bool = False

    def to_mcp_definition(self) -> dict[str, Any]:
        """Convert strand schema into Model Context Protocol format."""
        tier_str = str(self.tier.value).upper() if hasattr(self.tier, "value") else str(self.tier).upper()
        desc = f"[Capability Tier: {tier_str}] {self.description}".strip()
        schema = (
            self.args_schema.model_json_schema()
            if self.args_schema
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
