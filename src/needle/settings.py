"""
needle.settings - Standalone settings object, schema resolution, and configuration helpers.
"""

from __future__ import annotations

import contextlib
import tomllib
from importlib import resources
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pydantic import BaseModel


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


def load_package_settings(anchor: str | None = None) -> dict[str, Any]:
    """Read [tool.textile.settings] directly from package resources."""
    if not anchor:
        return {}
    with contextlib.suppress(TypeError, ValueError, AttributeError, ModuleNotFoundError, OSError):
        target = resources.files(anchor).joinpath("pyproject.toml")
        if target.is_file():
            with target.open("rb") as f:
                data = tomllib.load(f)
                settings_table = data.get("tool", {}).get("textile", {}).get("settings", {})
                if isinstance(settings_table, dict):
                    return {k: v.get("default", v) if isinstance(v, dict) else v for k, v in settings_table.items()}
    return {}


def resolve_yarn_settings(
    user_config: dict[str, Any],
    default_config: dict[str, Any] | None = None,
    schema: type[BaseModel] | None = None,
    package_anchor: str | None = None,
) -> Any:
    """Resolve and validate merged settings using Pydantic or fallback to SettingsObject.

    Default settings are resolved from package resources if package_anchor is provided,
    merged with any explicit default_config, and overridden by user_config.
    """
    merged_config: dict[str, Any] = {}
    if package_anchor is not None:
        merged_config.update(load_package_settings(package_anchor))
    if default_config:
        merged_config.update(default_config)
    merged_config.update(user_config)

    if schema is not None and isinstance(schema, type):
        from pydantic import BaseModel as _PydanticBase
        from pydantic import ValidationError

        if issubclass(schema, _PydanticBase):
            try:
                return schema.model_validate(merged_config)
            except ValidationError:
                try:
                    return schema()
                except ValidationError, TypeError, ValueError:
                    return SettingsObject(merged_config)
        return SettingsObject(merged_config)

    return SettingsObject(merged_config)


__all__ = ["SettingsObject", "load_package_settings", "resolve_yarn_settings"]
