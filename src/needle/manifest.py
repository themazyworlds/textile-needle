"""
needle.manifest - Yarn schema inspection and standalone manifest exporter.
"""

from __future__ import annotations

import importlib.util
import inspect
import json
import sys
from pathlib import Path
from typing import Any

from needle.yarn import Yarn

PROBE_PREFIX = "__TEXTILE_PROBE_JSON__:"
LOAD_EXCEPTIONS = (ImportError, SyntaxError, AttributeError, TypeError, ValueError, OSError, RuntimeError)


def export_yarn_manifest(yarn: Any) -> dict[str, Any]:
    """Export standardized yarn schema manifest and its capability strands."""
    strands_data: list[dict[str, Any]] = []
    for s in yarn.get_strands():
        tier_obj = getattr(s, "tier", "interact")
        tier_val = getattr(tier_obj, "value", str(tier_obj))
        s_no_timeout = bool(getattr(s, "no_timeout", False))
        s_timeout = None if s_no_timeout else getattr(s, "timeout", None)
        strands_data.append(
            {
                "name": s.name,
                "description": s.description,
                "tier": str(tier_val),
                "parameters": s.parameters,
                "required": s.required,
                "timeout": s_timeout,
                "no_timeout": s_no_timeout,
                "capability": s.capability,
            }
        )

    doc_desc = (yarn.__class__.__doc__ or "").strip().splitlines()[0] if yarn.__class__.__doc__ else yarn.name
    return {
        "class_name": yarn.__class__.__name__,
        "name": yarn.name,
        "description": yarn.description or doc_desc,
        "layer": yarn.layer,
        "tailor": yarn.tailor,
        "version": yarn.version,
        "resources": list(yarn.resources),
        "strands": strands_data,
    }


def probe_file(target_path: Path | str) -> list[dict[str, Any]]:
    """Inspect and extract Yarn manifests from a Python file path."""
    p = Path(target_path).resolve()
    if not p.exists() or not p.is_file():
        return []

    if str(p.parent) not in sys.path:
        sys.path.insert(0, str(p.parent))

    mod_name = f"probed_yarn_{p.stem}"
    spec = importlib.util.spec_from_file_location(mod_name, str(p))
    if not spec or not spec.loader:
        return []

    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    try:
        spec.loader.exec_module(mod)
    except LOAD_EXCEPTIONS:
        return []

    manifests: list[dict[str, Any]] = []
    for name, attr in inspect.getmembers(mod, inspect.isclass):
        if attr is Yarn or not issubclass(attr, Yarn) or getattr(attr, "__module__", "") != mod_name:
            continue
        try:
            inst = attr()
            manifest = inst.export_manifest() if hasattr(inst, "export_manifest") else export_yarn_manifest(inst)
            manifests.append(manifest)
        except LOAD_EXCEPTIONS:
            continue

    return manifests


def main() -> None:
    """CLI entrypoint for standalone manifest discovery (python -m needle.manifest <path>)."""
    if len(sys.argv) < 2:
        sys.exit(0)

    target_file = Path(sys.argv[1]).resolve()
    manifests = probe_file(target_file)
    for m in manifests:
        sys.stdout.write(f"{PROBE_PREFIX}{json.dumps(m)}\n")


if __name__ == "__main__":
    main()
