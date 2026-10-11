"""
needle.yarn - Base class and lifecycle contract for Textile Yarns.
"""

import inspect
from collections.abc import Callable, Sequence
from typing import Any, cast

from needle.models import Strand, Weft
from needle.tiers import CapabilityTier


class Yarn:
    """Base class for all Textile capability plugins (Yarns)."""

    name: str = ""
    layer: int = 150
    description: str = ""
    resources: Sequence[str] = ()

    def __init__(
        self,
        name: str | None = None,
        layer: int = 150,
        description: str | None = None,
        resources: Sequence[str] | None = None,
    ) -> None:
        self.name: str = name or self.__class__.__name__.lower().removesuffix("yarn")
        self.layer: int = layer
        self.description: str = description or (self.__doc__.strip().splitlines()[0] if self.__doc__ else self.name)
        self.resources: Sequence[str] = list(resources or [])

    def is_available(self) -> bool:
        """Check whether the underlying system service, daemon, or tool is present."""
        return True

    def on_load(self) -> None:
        """Lifecycle hook invoked when this Yarn is loaded into the active runtime."""

    def on_unload(self) -> None:
        """Lifecycle hook invoked when this Yarn is unloaded."""

    def build_strand(
        self,
        name: str,
        description: str,
        handler: Callable[..., Any],
        *,
        tier: CapabilityTier = CapabilityTier.INTERACT,
        parameters: dict[str, Any] | None = None,
        required: list[str] | None = None,
        capability: str | None = None,
        resources: list[str] | None = None,
        timeout: float | None = 30.0,
        no_timeout: bool = False,
    ) -> Strand:
        """Helper to construct and return a Strand object explicitly."""
        return Strand(
            name=name,
            description=description,
            handler=handler,
            raw_handler=handler,
            tier=tier,
            parameters=parameters or {},
            required=required or [],
            capability=capability,
            resources=resources or list(self.resources),
            timeout=None if no_timeout else timeout,
            no_timeout=no_timeout,
        )

    def get_strands(self) -> list[Strand]:
        """Discover all strands exposed by this Yarn (from decorators or explicit declarations)."""
        strands: list[Strand] = []
        for _, method in inspect.getmembers(self, predicate=callable):
            if getattr(method, "_is_strand", False):
                s_name = getattr(method, "_strand_name", method.__name__)
                s_desc = getattr(method, "_strand_description", method.__doc__ or s_name)
                s_tier = getattr(method, "_strand_tier", CapabilityTier.INTERACT)
                s_cap = getattr(method, "_strand_capability", None)
                s_timeout = getattr(method, "_strand_timeout", 30.0)
                s_no_timeout = getattr(method, "_strand_no_timeout", False)
                s_res = getattr(method, "_strand_resources", list(self.resources))

                sig = inspect.signature(method)
                params: dict[str, Any] = {}
                req: list[str] = []

                type_map = {
                    str: "string",
                    int: "integer",
                    float: "number",
                    bool: "boolean",
                    list: "array",
                    dict: "object",
                }

                for p_name, p in sig.parameters.items():
                    if p_name in ("self", "cls"):
                        continue
                    p_type = "string"
                    if p.annotation is not inspect.Parameter.empty:
                        p_type = type_map.get(p.annotation, "string")
                    prop: dict[str, Any] = {"type": p_type}
                    if p.default is not inspect.Parameter.empty:
                        prop["default"] = p.default
                    else:
                        req.append(p_name)
                    params[p_name] = prop

                strands.append(
                    Strand(
                        name=s_name,
                        description=s_desc,
                        handler=method,
                        raw_handler=method,
                        tier=s_tier,
                        capability=s_cap,
                        parameters=params,
                        required=req,
                        resources=s_res,
                        timeout=s_timeout,
                        no_timeout=s_no_timeout,
                    )
                )
        return strands

    def get_wefts(self) -> list[Weft]:
        """Discover all real-time token streaming wefts defined on this Yarn."""
        wefts: list[Weft] = []
        for _, method in inspect.getmembers(self, predicate=callable):
            if getattr(method, "_is_weft", False):
                w_name = getattr(method, "_weft_name", method.__name__)
                w_pattern = cast(Any, method)._weft_pattern
                w_desc = getattr(method, "_weft_description", "")
                w_strip = getattr(method, "_weft_strip", True)
                w_priority = getattr(method, "_weft_priority", 100)

                wefts.append(
                    Weft(
                        name=w_name,
                        pattern=w_pattern,
                        handler=method,
                        description=w_desc,
                        strip=w_strip,
                        priority=w_priority,
                    )
                )
        return wefts
