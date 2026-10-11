"""
needle.yarn - Base class and lifecycle contract for Textile Yarns.
"""

import asyncio
import concurrent.futures
import contextlib
import inspect
import sys
import tomllib
from collections.abc import Callable, Sequence
from functools import cached_property
from pathlib import Path
from typing import Any, cast

from pydantic import BaseModel, ValidationError

from needle.models import Strand, Weft
from needle.tiers import CapabilityTier


class SettingsObject(dict[str, Any]):
    """Dynamic settings object supporting dot-attribute access and dict indexing."""

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"Settings has no attribute {name!r}") from None

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value

    def __delattr__(self, name: str) -> None:
        try:
            del self[name]
        except KeyError:
            raise AttributeError(f"Settings has no attribute {name!r}") from None


class Yarn:
    """Base class for all Textile capability plugins (Yarns)."""

    name: str = ""
    layer: int = 150
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
        **kwargs: Any,
    ) -> None:
        if name:
            self.name = name
        elif not self.name:
            self.name = self.__class__.__name__.lower().removesuffix("yarn")

        if description:
            self.description = description.splitlines()[0].strip()
        elif not self.description:
            doc = inspect.getdoc(self.__class__)
            self.description = doc.splitlines()[0].strip() if doc else self.name

        if layer is not None:
            self.layer = layer
        if tailor is not None:
            self.tailor = tailor
        elif "tailor" in kwargs and kwargs["tailor"] is not None:
            self.tailor = str(kwargs["tailor"])
        if version is not None:
            self.version = version
        elif "version" in kwargs and kwargs["version"] is not None:
            self.version = str(kwargs["version"])
        if resources is not None:
            self.resources = list(resources)
        elif "resources" in kwargs and kwargs["resources"] is not None:
            self.resources = list(kwargs["resources"])
        if dependencies is not None:
            self.dependencies = list(dependencies)
        elif "dependencies" in kwargs and kwargs["dependencies"] is not None:
            self.dependencies = list(kwargs["dependencies"])

        self._default_settings: dict[str, Any] = {}
        self._settings_info: dict[str, Any] = {}
        self._settings: Any = None
        self._slots: dict[str, Any] = {}

        self._populate_pyproject_metadata(name=name, description=description, layer=layer, kwargs=kwargs)

    def _populate_pyproject_metadata(
        self,
        name: str | None,
        description: str | None,
        layer: int | None,
        kwargs: dict[str, Any],
    ) -> None:
        with contextlib.suppress(Exception):
            mod = sys.modules.get(self.__class__.__module__)
            mod_file = getattr(mod, "__file__", None)
            if not mod_file:
                try:
                    mod_file = inspect.getfile(self.__class__)
                except (TypeError, OSError):
                    mod_file = None
            if not mod_file:
                return
            pyproj = Path(mod_file).parent / "pyproject.toml"
            if not pyproj.exists():
                return
            with pyproj.open("rb") as f:
                data = tomllib.load(f)

            project = data.get("project", {})
            if not name and "name" in project and (not self.name or self.name == self.__class__.__name__.lower()):
                raw_name = str(project["name"])
                self.name = raw_name.removeprefix("textile-yarn-").removeprefix("yarn-")
            if not description and "description" in project:
                self.description = str(project["description"]).splitlines()[0].strip()
            if "version" not in kwargs and "version" in project:
                self.version = str(project["version"])
            if "authors" in project and project["authors"] and "tailor" not in kwargs:
                first_author = project["authors"][0]
                self.tailor = str(first_author.get("name", "textile") if isinstance(first_author, dict) else first_author)
            if "dependencies" not in kwargs and not self.dependencies and "dependencies" in project:
                self.dependencies = list(project["dependencies"])

            tool_textile = data.get("tool", {}).get("textile", {})
            if layer is None and "layer" in tool_textile:
                self.layer = int(tool_textile["layer"])
            if "tailor" in tool_textile and "tailor" not in kwargs:
                self.tailor = str(tool_textile["tailor"])
            if "resources" not in kwargs and not self.resources and "resources" in tool_textile:
                self.resources = list(tool_textile["resources"])
            if "settings" in tool_textile and isinstance(tool_textile["settings"], dict):
                self._settings_info = dict(tool_textile["settings"])
                for key, val in tool_textile["settings"].items():
                    if isinstance(val, dict) and "default" in val:
                        self._default_settings[key] = val["default"]
                    else:
                        self._default_settings[key] = val

    def get_settings_schema(self) -> type[BaseModel] | None:
        """Return explicit Pydantic settings schema for this yarn."""
        return self.settings_schema

    @property
    def settings(self) -> Any:
        """Returns validated settings based on pyproject.toml defaults and user overrides."""
        if self._settings is not None:
            return self._settings

        user_config: dict[str, Any] = {}
        if "textile.core.definitions.settings" in sys.modules:
            getter = getattr(sys.modules["textile.core.definitions.settings"], "get_user_yarn_settings", None)
            if callable(getter):
                res = getter(self.name)
                if isinstance(res, dict):
                    user_config = res

        merged_config = dict(self._default_settings)
        merged_config.update(user_config)

        schema = self.get_settings_schema()
        if schema is not None and isinstance(schema, type) and issubclass(schema, BaseModel):
            try:
                self._settings = schema.model_validate(merged_config)
            except ValidationError:
                try:
                    self._settings = schema()
                except (ValidationError, TypeError, ValueError):
                    self._settings = SettingsObject(merged_config)
        else:
            self._settings = SettingsObject(merged_config)

        return self._settings

    def reload_settings(self) -> Any:
        """Clear cached settings and reload."""
        self._settings = None
        return self.settings

    @property
    def elastic(self) -> Any:
        """Universal cross-process event and sensory bus."""
        if hasattr(self, "_elastic") and self._elastic is not None:
            return self._elastic
        if "textile.core.telemetry.elastic" in sys.modules:
            mod = sys.modules["textile.core.telemetry.elastic"]
            inst = getattr(mod, "elastic", None)
            if inst is not None and not inspect.ismodule(inst):
                return inst
        if "textile.core.telemetry" in sys.modules:
            inst = getattr(sys.modules["textile.core.telemetry"], "elastic", None)
            if inst is not None and not inspect.ismodule(inst):
                return inst
        return None

    @property
    def tapestry(self) -> Any:
        """Universal live state & sensory blackboard."""
        if hasattr(self, "_tapestry") and self._tapestry is not None:
            return self._tapestry
        if "textile.core.telemetry.blackboard" in sys.modules:
            mod = sys.modules["textile.core.telemetry.blackboard"]
            inst = getattr(mod, "sensory_tapestry", None)
            if inst is not None and not inspect.ismodule(inst):
                return inst
        if "textile.core.telemetry" in sys.modules:
            inst = getattr(sys.modules["textile.core.telemetry"], "sensory_tapestry", None)
            if inst is not None and not inspect.ismodule(inst):
                return inst
        return None

    def publish_event(
        self,
        topic: str,
        options: Any = None,
        **kwargs: Any,
    ) -> None:
        """Publish a real-time event to Elastic."""
        if self.elastic is not None:
            summary = getattr(options, "summary", "") or kwargs.get("summary") or f"Event '{topic}' from yarn '{self.name}'"
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

    @cached_property
    def wefts(self) -> list[Weft]:
        """Automatically discovers all @weft decorated methods on the class once."""
        return self.get_wefts()

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
        timeout: float | None = 30.0,
        no_timeout: bool = False,
        **kwargs: Any,
    ) -> Strand:
        """Helper to construct and return a Strand object explicitly."""
        if "textile.core.execution.reflector" in sys.modules:
            reflector = sys.modules["textile.core.execution.reflector"]
            build_fn = getattr(reflector, "build_dynamic_strand", None)
            if callable(build_fn):
                return cast(
                    Strand,
                    build_fn(
                        self,
                        name,
                        description,
                        handler,
                        tier=tier,
                        parameters=parameters,
                        required=required,
                        capability=capability,
                        resources=resources,
                        timeout=timeout,
                        no_timeout=no_timeout,
                        **kwargs,
                    ),
                )

        from needle.tiers import parse_capability_tier

        validated_tier = parse_capability_tier(tier, strand_name=name)
        return Strand(
            name=name,
            description=description,
            handler=handler,
            raw_handler=handler,
            tier=validated_tier,
            parameters=parameters or {},
            required=required or [],
            capability=capability,
            resources=resources or list(self.resources),
            timeout=None if no_timeout else timeout,
            no_timeout=no_timeout,
        )

    def get_strands(self) -> list[Strand]:
        """Discover all strands exposed by this Yarn (from decorators or explicit declarations)."""
        if "textile.core.execution.reflector" in sys.modules:
            reflector = sys.modules["textile.core.execution.reflector"]
            reflect_fn = getattr(reflector, "reflect_strands", None)
            if callable(reflect_fn):
                return cast(list[Strand], reflect_fn(self))

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
                )
            )
        return discovered

    def get_wefts(self) -> list[Weft]:
        """Discover all real-time token streaming wefts defined on this Yarn."""
        if "textile.core.execution.reflector" in sys.modules:
            reflector = sys.modules["textile.core.execution.reflector"]
            reflect_fn = getattr(reflector, "reflect_wefts", None)
            if callable(reflect_fn):
                return cast(list[Weft], reflect_fn(self))

        discovered: list[Weft] = []
        for m_name in dir(self.__class__):
            if m_name.startswith("__"):
                continue
            class_attr = getattr(self.__class__, m_name, None)
            if isinstance(class_attr, (property, cached_property)):
                continue
            method = getattr(self, m_name, None)
            if not callable(method) or not getattr(method, "_is_weft", False):
                continue
            w_name = getattr(method, "_weft_name", method.__name__)
            w_pattern = cast(Any, method)._weft_pattern
            w_desc = getattr(method, "_weft_description", "")
            w_strip = getattr(method, "_weft_strip", True)
            w_priority = getattr(method, "_weft_priority", 100)

            discovered.append(
                Weft(
                    name=w_name,
                    pattern=w_pattern,
                    handler=method,
                    description=w_desc,
                    strip=w_strip,
                    priority=w_priority,
                )
            )
        return discovered

    def execute_sync(self, strand_name: str, args: dict[str, Any]) -> str:
        """Execute strand synchronously by matching name in discovered strands."""
        strand = next((s for s in self.get_strands() if s.name == strand_name and s.handler is not None), None)
        if not strand or not strand.handler:
            return f"Error: Strand '{strand_name}' not implemented in yarn '{self.name}'."

        res = strand.handler(args)
        if inspect.isawaitable(res):
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    return str(pool.submit(asyncio.run, res).result())
            return str(asyncio.run(res))
        return str(res)
