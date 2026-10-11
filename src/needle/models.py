"""
needle.models - Pydantic definitions for Strands, Wefts, and schema specifications.
"""

import re
from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

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


class Weft(BaseModel):
    """Represents a real-time streaming semantic token attunement filter."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    pattern: re.Pattern
    description: str = ""
    strip: bool = True
    priority: int = 100
    handler: Callable[..., Any] | None = None
    raw_handler: Callable[..., Any] | None = None
    args_schema: type[BaseModel] | None = None
    param_names: list[str] = Field(default_factory=list)

    def execute_match(self, match: re.Match[str]) -> Any:
        """Execute weft attunement handler with regex match extracted arguments coerced with Pydantic."""
        raw_kwargs: dict[str, Any] = {}
        if named := {k: v for k, v in match.groupdict().items() if v is not None}:
            raw_kwargs = named
        elif match.groups():
            raw_kwargs = dict(zip(self.param_names, match.groups(), strict=False))
        elif len(self.param_names) == 1:
            raw_kwargs = {self.param_names[0]: match[0]}

        if self.args_schema:
            try:
                validated = self.args_schema.model_validate(raw_kwargs)
                coerced = validated.model_dump()
            except ValidationError:
                coerced = raw_kwargs
        else:
            coerced = raw_kwargs

        return self.handler(**coerced) if self.handler else None
