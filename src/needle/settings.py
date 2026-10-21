"""
needle.settings - Standalone dynamic settings object and configuration helpers.
"""

from __future__ import annotations

import contextlib
import sys
from pathlib import Path
from typing import Any
lazy import tomllib


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
    """Read [tool.textile.settings] directly from module directory or package resources."""
    if not anchor:
        return {}

    with contextlib.suppress(Exception):
        mod = sys.modules.get(anchor)
        if mod and hasattr(mod, "__file__") and mod.__file__:
            p = Path(mod.__file__).resolve().parent / "pyproject.toml"
            if p.is_file():
                with p.open("rb") as f:
                    data = tomllib.load(f)
                    settings_table = data.get("tool", {}).get("textile", {}).get("settings", {})
                    if isinstance(settings_table, dict):
                        return {k: v.get("default", v) if isinstance(v, dict) else v for k, v in settings_table.items()}

    with contextlib.suppress(TypeError, ValueError, AttributeError, ModuleNotFoundError, OSError):
        from importlib import resources

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
    schema: Any = None,
    package_anchor: str | None = None,
) -> Any:
    """Resolve merged settings into a schema instance or dot-accessible SettingsObject dictionary.

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
        if hasattr(schema, "model_validate"):
            with contextlib.suppress(Exception):
                return schema.model_validate(merged_config)
            with contextlib.suppress(Exception):
                return schema()
        elif callable(schema):
            with contextlib.suppress(Exception):
                return schema(**merged_config)

    return SettingsObject(merged_config)


__all__ = ["SettingsObject", "load_package_settings", "resolve_yarn_settings"]
