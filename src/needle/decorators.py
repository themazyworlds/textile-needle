"""
needle.decorators - Declarative @strand and @weft decorators for Yarns.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

from needle.tiers import CapabilityTier, parse_capability_tier


@dataclass(slots=True)
class StrandOptions:
    """Configuration options for a Strand decorator."""

    name: str | None = None
    description: str | None = None
    capability: str | None = None
    tier: CapabilityTier | Literal["observe", "interact", "mutate", "privileged", "system_exec"] | None = None
    timeout: float | None = 30.0
    no_timeout: bool = False
    resources: list[str] | None = None


@dataclass(slots=True)
class WeftOptions:
    """Configuration options for a Weft decorator."""

    pattern: str | re.Pattern = ""
    name: str | None = None
    description: str | None = None
    strip: bool = True
    priority: int = 100


def strand(
    func: Callable[..., Any] | None = None,
    options: StrandOptions | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
    capability: str | None = None,
    tier: CapabilityTier | Literal["observe", "interact", "mutate", "privileged", "system_exec"] | None = None,
    timeout: float | None = 30.0,
    no_timeout: bool = False,
    resources: list[str] | None = None,
    **kwargs: Any,
) -> Any:
    """Decorator marking a Yarn method as an executable Desktop Strand tool.

    Example:
        @strand(tier=CapabilityTier.INTERACT)
        def my_tool(self, query: str) -> str:
            return "done"
    """
    if options is None:
        options = StrandOptions(
            name=name,
            description=description,
            capability=capability,
            tier=tier,
            timeout=timeout,
            no_timeout=no_timeout,
            resources=resources or kwargs.get("resources"),
        )

    if options.tier is None:
        raise ValueError(
            "Strand decorator must declare an explicit capability tier "
            "(e.g. @strand(tier=CapabilityTier.INTERACT) or @strand(tier='observe'))."
        )

    validated_tier = parse_capability_tier(options.tier, strand_name=options.name or "")

    def decorator(fn: Any) -> Any:
        fn_name = getattr(fn, "__name__", "")
        fn_doc = getattr(fn, "__doc__", "")

        fn._is_strand = True
        fn._strand_name = options.name or fn_name
        fn._strand_description = options.description or (fn_doc.strip().splitlines()[0] if fn_doc else "")
        fn._strand_capability = options.capability
        fn._strand_tier = validated_tier
        fn._strand_timeout = None if options.no_timeout else options.timeout
        fn._strand_no_timeout = options.no_timeout
        fn._strand_resources = list(options.resources or [])
        return fn

    return decorator(func) if func is not None else decorator


def weft(
    func: Callable[..., Any] | None = None,
    options: WeftOptions | None = None,
    *,
    pattern: str | re.Pattern = "",
    name: str | None = None,
    description: str | None = None,
    strip: bool = True,
    priority: int = 100,
    **_kwargs: Any,
) -> Any:
    """Decorator marking a Yarn method as a streaming token Weft attunement filter."""
    if options is None:
        options = WeftOptions(
            pattern=pattern,
            name=name,
            description=description,
            strip=strip,
            priority=priority,
        )

    compiled_pattern = re.compile(options.pattern) if isinstance(options.pattern, str) else options.pattern

    def decorator(fn: Any) -> Any:
        fn_name = getattr(fn, "__name__", "")
        fn_doc = getattr(fn, "__doc__", "")

        fn._is_weft = True
        fn._weft_name = options.name or fn_name
        fn._weft_pattern = compiled_pattern
        fn._weft_description = options.description or (fn_doc.strip().splitlines()[0] if fn_doc else "")
        fn._weft_strip = options.strip
        fn._weft_priority = options.priority
        return fn

    return decorator(func) if func is not None else decorator
