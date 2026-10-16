"""
needle.decorators - Declarative tier decorators for Yarns.
"""

from collections.abc import Callable
from typing import Any

from needle.tiers import DEFAULT_TIER_TIMEOUTS, CapabilityTier

_DEFAULT_TIMEOUT: object = object()


class StrandDecorator:
    """Namespace providing declarative capability tier decorators.

    Only tier-specific decorators are supported:
    - @strand.observe(...) or @strand.observe
    - @strand.interact(...) or @strand.interact
    - @strand.mutate(...) or @strand.mutate
    - @strand.privileged(...) or @strand.privileged
    - @strand.system_exec(...) or @strand.system_exec
    """

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        raise TypeError(
            "Direct @strand is not supported. Use explicit tier decorators: "
            "@strand.observe, @strand.interact, @strand.mutate, @strand.privileged, or @strand.system_exec."
        )

    def _decorate(
        self,
        func: Callable[..., Any] | None,
        *,
        name: str | None,
        description: str | None,
        capability: str | None,
        tier: CapabilityTier,
        timeout: float | None | object,
        no_timeout: bool,
        resources: list[str] | None,
        reason: str | None,
        fallback: Any,
    ) -> Any:
        def decorator(fn: Any) -> Any:
            fn_name = getattr(fn, "__name__", "")
            fn_doc = getattr(fn, "__doc__", "")

            if no_timeout:
                resolved_timeout = None
            elif timeout is not _DEFAULT_TIMEOUT and timeout is not None:
                resolved_timeout = timeout  # type: ignore[assignment]
            else:
                resolved_timeout = DEFAULT_TIER_TIMEOUTS.get(tier, 15.0)

            fn._is_strand = True
            fn._strand_name = name or fn_name
            fn._strand_description = description or (fn_doc.strip().splitlines()[0] if fn_doc else "")
            fn._strand_capability = capability
            fn._strand_tier = tier
            fn._strand_timeout = resolved_timeout
            fn._strand_no_timeout = no_timeout
            fn._strand_resources = list(resources or [])
            fn._strand_reason = reason
            fn._strand_fallback = fallback
            return fn

        return decorator(func) if func is not None else decorator

    def observe(
        self,
        func: Callable[..., Any] | None = None,
        *,
        name: str | None = None,
        description: str | None = None,
        capability: str | None = None,
        timeout: float | None | object = _DEFAULT_TIMEOUT,
        no_timeout: bool = False,
        resources: list[str] | None = None,
        reason: str | None = None,
        fallback: Any = None,
        **_kwargs: Any,
    ) -> Any:
        """Mark method as an OBSERVE tier strand (read-only telemetry, default timeout 10s)."""
        return self._decorate(
            func=func,
            name=name,
            description=description,
            capability=capability,
            tier=CapabilityTier.OBSERVE,
            timeout=timeout,
            no_timeout=no_timeout,
            resources=resources,
            reason=reason,
            fallback=fallback,
        )

    def interact(
        self,
        func: Callable[..., Any] | None = None,
        *,
        name: str | None = None,
        description: str | None = None,
        capability: str | None = None,
        timeout: float | None | object = _DEFAULT_TIMEOUT,
        no_timeout: bool = False,
        resources: list[str] | None = None,
        reason: str | None = None,
        fallback: Any = None,
        **_kwargs: Any,
    ) -> Any:
        """Mark method as an INTERACT tier strand (UI/IPC actions, default timeout 15s)."""
        return self._decorate(
            func=func,
            name=name,
            description=description,
            capability=capability,
            tier=CapabilityTier.INTERACT,
            timeout=timeout,
            no_timeout=no_timeout,
            resources=resources,
            reason=reason,
            fallback=fallback,
        )

    def mutate(
        self,
        func: Callable[..., Any] | None = None,
        *,
        name: str | None = None,
        description: str | None = None,
        capability: str | None = None,
        timeout: float | None | object = _DEFAULT_TIMEOUT,
        no_timeout: bool = False,
        resources: list[str] | None = None,
        reason: str | None = None,
        fallback: Any = None,
        **_kwargs: Any,
    ) -> Any:
        """Mark method as a MUTATE tier strand (state/file modification, default timeout 60s)."""
        return self._decorate(
            func=func,
            name=name,
            description=description,
            capability=capability,
            tier=CapabilityTier.MUTATE,
            timeout=timeout,
            no_timeout=no_timeout,
            resources=resources,
            reason=reason,
            fallback=fallback,
        )

    def privileged(
        self,
        func: Callable[..., Any] | None = None,
        *,
        name: str | None = None,
        description: str | None = None,
        capability: str | None = None,
        timeout: float | None | object = _DEFAULT_TIMEOUT,
        no_timeout: bool = False,
        resources: list[str] | None = None,
        reason: str | None = None,
        fallback: Any = None,
        **_kwargs: Any,
    ) -> Any:
        """Mark method as a PRIVILEGED tier strand (system admin, packages, default timeout 300s)."""
        return self._decorate(
            func=func,
            name=name,
            description=description,
            capability=capability,
            tier=CapabilityTier.PRIVILEGED,
            timeout=timeout,
            no_timeout=no_timeout,
            resources=resources,
            reason=reason,
            fallback=fallback,
        )

    def system_exec(
        self,
        func: Callable[..., Any] | None = None,
        *,
        name: str | None = None,
        description: str | None = None,
        capability: str | None = None,
        timeout: float | None | object = _DEFAULT_TIMEOUT,
        no_timeout: bool = False,
        resources: list[str] | None = None,
        reason: str | None = None,
        fallback: Any = None,
        **_kwargs: Any,
    ) -> Any:
        """Mark method as a SYSTEM_EXEC tier strand (command execution, default timeout 120s)."""
        return self._decorate(
            func=func,
            name=name,
            description=description,
            capability=capability,
            tier=CapabilityTier.SYSTEM_EXEC,
            timeout=timeout,
            no_timeout=no_timeout,
            resources=resources,
            reason=reason,
            fallback=fallback,
        )


strand = StrandDecorator()

__all__ = ["StrandDecorator", "strand"]
