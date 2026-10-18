"""
needle.yarn - Base class and lifecycle contract for Textile Yarns.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import contextlib
import inspect
import sys
import tomllib
from collections.abc import Callable, Sequence
from functools import cached_property
from importlib import resources
from typing import TYPE_CHECKING, Any

import orjson

from needle.layers import DEFAULT_LAYER
from needle.models import Strand
from needle.settings import SettingsObject, resolve_yarn_settings
from needle.tiers import DEFAULT_TIER_TIMEOUTS, CapabilityTier, parse_capability_tier

if TYPE_CHECKING:
    from pydantic import BaseModel


class Yarn:
    """Base class for all Textile capability plugins (Yarns)."""

    name: str = ""
    layer: int = DEFAULT_LAYER
    description: str = ""
    tailor: str = "textile"
    version: str = "1.0.0"
    resources: Sequence[str] = ()
    dependencies: Sequence[str] = ()
    settings_schema: type[BaseModel] | None = None
    _elastic: Any = None
    _tapestry: Any = None

    def __init__(
        self,
        name: str | None = None,
        layer: int | None = None,
        description: str | None = None,
        tailor: str | None = None,
        version: str | None = None,
        resources: Sequence[str] | None = None,
        dependencies: Sequence[str] | None = None,
    ) -> None:
        cfg = self._read_pyproject()
        proj = cfg.get("project", {})
        tool = cfg.get("tool", {}).get("textile", {})

        # Declarative attribute resolution: Constructor Arg -> pyproject.toml -> Class Default
        proj_name = str(proj["name"]).removeprefix("textile-yarn-").removeprefix("yarn-") if "name" in proj else ""
        self.name = name or self.name or proj_name or self.__class__.__name__.lower().removesuffix("yarn")

        doc = inspect.getdoc(self.__class__)
        class_desc = doc.splitlines()[0].strip() if doc else self.name
        proj_desc = str(proj["description"]).splitlines()[0].strip() if "description" in proj else ""
        self.description = description or self.description or proj_desc or class_desc

        self.version = version or str(proj.get("version", self.version))
        self.layer = layer if layer is not None else int(tool.get("layer", self.layer))

        first_author = proj.get("authors", [{}])[0] if proj.get("authors") else {}
        author_name = first_author.get("name", "textile") if isinstance(first_author, dict) else str(first_author)
        self.tailor = tailor or str(tool.get("tailor", author_name if author_name else self.tailor))

        self.resources = list(resources if resources is not None else tool.get("resources", self.resources))
        self.dependencies = list(
            dependencies if dependencies is not None else proj.get("dependencies", self.dependencies)
        )

        settings_table = tool.get("settings", {}) if isinstance(tool.get("settings"), dict) else {}
        self._settings_info = dict(settings_table)
        self._default_settings = {
            k: v.get("default", v) if isinstance(v, dict) else v for k, v in settings_table.items()
        }
        self._user_settings: dict[str, Any] = {}
        self._settings: Any = None
        self._slots: dict[str, Any] = {}

    @classmethod
    def _read_pyproject(cls) -> dict[str, Any]:
        """Official PyPA resource loading via importlib.resources."""
        with contextlib.suppress(TypeError, ValueError, AttributeError, ModuleNotFoundError, OSError):
            target = resources.files(cls.__module__).joinpath("pyproject.toml")
            if target.is_file():
                with target.open("rb") as f:
                    return tomllib.load(f)
        return {}

    def get_settings_schema(self) -> type[BaseModel] | None:
        """Return explicit Pydantic settings schema for this yarn."""
        return self.settings_schema

    def set_user_settings(self, settings: dict[str, Any]) -> None:
        """Inject user configuration overrides for this yarn."""
        self._user_settings = dict(settings)
        self._settings = None

    @property
    def settings(self) -> Any:
        """Returns validated settings based on pyproject.toml defaults and user overrides."""
        if self._settings is not None:
            return self._settings

        self._settings = resolve_yarn_settings(
            user_config=getattr(self, "_user_settings", {}),
            default_config=self._default_settings,
            schema=self.get_settings_schema(),
            package_anchor=self.__class__.__module__,
        )
        return self._settings

    def reload_settings(self) -> Any:
        """Clear cached settings and reload."""
        self._settings = None
        return self.settings

    @property
    def elastic(self) -> Any:
        """Universal cross-process event and sensory bus."""
        inst = getattr(self, "_elastic", None)
        if inst is not None:
            return inst
        if "textile.core.telemetry.elastic" in sys.modules:
            return getattr(sys.modules["textile.core.telemetry.elastic"], "elastic", None)
        return None

    @property
    def tapestry(self) -> Any:
        """Universal live state & sensory blackboard."""
        inst = getattr(self, "_tapestry", None)
        if inst is not None:
            return inst
        if "textile.core.telemetry.blackboard" in sys.modules:
            return getattr(sys.modules["textile.core.telemetry.blackboard"], "sensory_tapestry", None)
        return None

    def publish_event(
        self,
        topic: str,
        options: Any = None,
        **kwargs: Any,
    ) -> None:
        """Publish a real-time event to Elastic."""
        if self.elastic is not None:
            summary = (
                getattr(options, "summary", "") or kwargs.get("summary") or f"Event '{topic}' from yarn '{self.name}'"
            )
            urgency = getattr(options, "urgency", None) or kwargs.get("urgency", "notice")
            data = getattr(options, "data", None) if options is not None else kwargs.get("data")
            payload = data if isinstance(data, dict) else (kwargs if kwargs else {"payload": data})
            retained_slot = getattr(options, "retained_slot", None) or kwargs.get("retained_slot")
            retained_value = getattr(options, "retained_value", None) or kwargs.get("retained_value")
            self.elastic.broadcast(
                topic=topic,
                source=self.name,
                summary=summary,
                urgency=urgency,
                data=payload,
                retained_slot=retained_slot,
                retained_value=retained_value,
            )

    def stitch(self, level: str, message: str, data: dict[str, Any] | None = None) -> Any:
        """Stitch a structured notice/alert into the Tapestry sensory blackboard."""
        if self.tapestry is not None:
            return self.tapestry.stitch(level=level, source=self.name, message=message, data=data)
        return None

    def set_slot(self, key: str, value: Any) -> None:
        """Set a retained domain state slot."""
        if self.elastic is not None:
            self.elastic.occupy_seat(key, value, source=self.name)
        self._slots[key] = value

    def get_slot(self, key: str, default: Any = None) -> Any:
        """Get a retained domain state slot."""
        if self.elastic is not None:
            return self.elastic.get_slot(key, default)
        return self._slots.get(key, default)

    def get_dependencies(self) -> list[str]:
        """Return system dependencies declared for this yarn."""
        return list(getattr(self, "dependencies", []))

    def is_available(self) -> bool:
        """Check whether runtime dependencies and environment are met."""
        return True

    def on_load(self) -> None:
        """Lifecycle hook invoked when this Yarn is loaded into the active runtime."""

    def on_unload(self) -> None:
        """Lifecycle hook invoked when this Yarn is unloaded."""

    @cached_property
    def strands(self) -> list[Strand]:
        """Automatically discovers all @strand decorated methods on the class once."""
        return self.get_strands()

    def build_strand(
        self,
        name: str,
        description: str,
        handler: Callable[..., Any],
        *,
        tier: CapabilityTier | str = CapabilityTier.INTERACT,
        parameters: dict[str, Any] | None = None,
        required: list[str] | None = None,
        capability: str | None = None,
        resources: list[str] | None = None,
        timeout: float | None = None,
        no_timeout: bool = False,
        args_schema: type[BaseModel] | None = None,
        reason: str | None = None,
        fallback: Any = None,
    ) -> Strand:
        """Helper to construct and return a Strand object explicitly."""
        validated_tier = parse_capability_tier(tier, strand_name=name)
        params = dict(parameters) if parameters else {}
        req = list(required) if required else []
        if args_schema is not None and not params:
            json_schema = args_schema.model_json_schema()
            params = dict(json_schema.get("properties", {}))
            req = list(json_schema.get("required", []))

        resolved_timeout = None if no_timeout else (timeout if timeout is not None else DEFAULT_TIER_TIMEOUTS.get(validated_tier, 15.0))

        return Strand(
            name=name,
            description=description,
            handler=handler,
            raw_handler=handler,
            tier=validated_tier,
            parameters=params,
            required=req,
            capability=capability,
            args_schema=args_schema,
            resources=resources or list(self.resources),
            timeout=resolved_timeout,
            no_timeout=no_timeout,
            reason=reason,
            fallback=fallback,
        )

    def get_strands(self) -> list[Strand]:
        """Discover all strands exposed by this Yarn (from decorators or explicit declarations)."""
        discovered: list[Strand] = []
        for m_name in dir(self.__class__):
            if m_name.startswith("__"):
                continue
            class_attr = getattr(self.__class__, m_name, None)
            if isinstance(class_attr, (property, cached_property)):
                continue
            method = getattr(self, m_name, None)
            if not callable(method) or not getattr(method, "_is_strand", False):
                continue
            s_name = getattr(method, "_strand_name", method.__name__)
            s_desc = getattr(method, "_strand_description", method.__doc__ or s_name)
            s_tier = getattr(method, "_strand_tier", CapabilityTier.INTERACT)
            s_cap = getattr(method, "_strand_capability", None)
            s_no_timeout = getattr(method, "_strand_no_timeout", False)
            s_timeout = getattr(method, "_strand_timeout", None if s_no_timeout else DEFAULT_TIER_TIMEOUTS.get(s_tier, 15.0))
            s_res = getattr(method, "_strand_resources", list(self.resources))
            s_reason = getattr(method, "_strand_reason", None)
            s_fallback = getattr(method, "_strand_fallback", None)

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
                if p_name in {"self", "cls"}:
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

            discovered.append(
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
                    reason=s_reason,
                    fallback=s_fallback,
                )
            )
        return discovered

    def execute_sync(self, strand_name: str, args: dict[str, Any]) -> str:
        """Execute strand synchronously by matching name in discovered strands."""
        strand = next((s for s in self.get_strands() if s.name == strand_name and s.handler is not None), None)
        if not strand or not strand.handler:
            return f"Error: Strand '{strand_name}' not implemented in yarn '{self.name}'."

        sig = inspect.signature(strand.handler)
        params = list(sig.parameters.values())
        if (
            len(params) == 1
            and params[0].annotation is not inspect.Parameter.empty
            and not inspect.isclass(params[0].annotation)
            and "dict" in str(params[0].annotation)
        ):
            res = strand.handler(args)
        else:
            try:
                bound = sig.bind_partial(**args)
                bound.apply_defaults()
                res = strand.handler(*bound.args, **bound.kwargs)
            except TypeError:
                res = strand.handler(args)

        if inspect.isawaitable(res):
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    res = pool.submit(asyncio.run, res).result()
            else:
                res = asyncio.run(res)

        if isinstance(res, str):
            return res
        if isinstance(res, (dict, list)):
            return orjson.dumps(res).decode()
        return str(res)

    def export_manifest(self) -> dict[str, Any]:
        """Export standardized yarn schema manifest and its capability strands."""
        from needle.manifest import export_yarn_manifest

        return export_yarn_manifest(self)


__all__ = ["SettingsObject", "Yarn"]
