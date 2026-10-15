"""
needle - The Sharp, Minimal Developer SDK for Textile Yarns and Agents.
"""

lazy from needle.decorators import StrandOptions, strand
lazy from needle.errors import (
    NeedleError,
    StrandCollisionError,
    StrandError,
    StrandNotFoundError,
    StrandOperationalError,
    YarnNotFoundError,
)
lazy from needle.events import EventFrame, EventOptions, EventUrgency
lazy from needle.guardrails import AccessBoundaryError, ScopedPath, SessionProcessGuard
lazy from needle.layers import (
    LAYER_COMPOSITOR_DE_THRESHOLD,
    LAYER_CORE_POSIX_THRESHOLD,
    LAYER_DESKTOP_PROTOCOL_THRESHOLD,
    LAYER_SESSION_MANAGER_THRESHOLD,
    LAYER_USER_OVERRIDE_THRESHOLD,
    LayerInfo,
    LayerTier,
    get_layer_info,
)
lazy from needle.manifest import export_yarn_manifest
lazy from needle.models import Strand
lazy from needle.settings import SettingsObject, load_package_settings, resolve_yarn_settings
lazy from needle.tiers import CapabilityTier, parse_capability_tier
lazy from needle.yarn import Yarn

__version__ = "0.1.0"

__all__ = [
    "LAYER_COMPOSITOR_DE_THRESHOLD",
    "LAYER_CORE_POSIX_THRESHOLD",
    "LAYER_DESKTOP_PROTOCOL_THRESHOLD",
    "LAYER_SESSION_MANAGER_THRESHOLD",
    "LAYER_USER_OVERRIDE_THRESHOLD",
    "AccessBoundaryError",
    "CapabilityTier",
    "EventFrame",
    "EventOptions",
    "EventUrgency",
    "LayerInfo",
    "LayerTier",
    "NeedleError",
    "ScopedPath",
    "SessionProcessGuard",
    "SettingsObject",
    "Strand",
    "StrandCollisionError",
    "StrandError",
    "StrandNotFoundError",
    "StrandOperationalError",
    "StrandOptions",
    "Yarn",
    "YarnNotFoundError",
    "export_yarn_manifest",
    "get_layer_info",
    "load_package_settings",
    "parse_capability_tier",
    "resolve_yarn_settings",
    "strand",
]
