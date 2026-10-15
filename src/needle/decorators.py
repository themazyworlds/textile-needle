"""
needle.decorators - Declarative @strand decorator for Yarns.
"""

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
    isolated: bool = True,
    **_kwargs: Any,
) -> Any:
    """Decorator marking a Yarn method as an executable capability Strand."""
    if options is None:
        options = StrandOptions(
            name=name,
            description=description,
            capability=capability,
            tier=tier,
            timeout=timeout,
            no_timeout=no_timeout,
            resources=resources,
        )

    def decorator(fn: Any) -> Any:
        fn_name = getattr(fn, "__name__", "")
        fn_doc = getattr(fn, "__doc__", "")

        resolved_tier_val = options.tier or CapabilityTier.INTERACT
        validated_tier = parse_capability_tier(resolved_tier_val, strand_name=fn_name)

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


__all__ = ["StrandOptions", "strand"]
