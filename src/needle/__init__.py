"""
needle - The Sharp, Minimal Developer SDK for Textile Yarns and Agents.
"""

lazy from needle.decorators import StrandDecorator, strand
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
lazy from needle.layers import DEFAULT_LAYER
lazy from needle.manifest import export_yarn_manifest
lazy from needle.models import Strand
lazy from needle.settings import SettingsObject, load_package_settings, resolve_yarn_settings
lazy from needle.tiers import DEFAULT_TIER_TIMEOUTS, CapabilityTier, parse_capability_tier
lazy from needle.yarn import Yarn

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_LAYER",
    "DEFAULT_TIER_TIMEOUTS",
    "AccessBoundaryError",
    "CapabilityTier",
    "EventFrame",
    "EventOptions",
    "EventUrgency",
    "NeedleError",
    "ScopedPath",
    "SessionProcessGuard",
    "SettingsObject",
    "Strand",
    "StrandCollisionError",
    "StrandDecorator",
    "StrandError",
    "StrandNotFoundError",
    "StrandOperationalError",
    "Yarn",
    "YarnNotFoundError",
    "export_yarn_manifest",
    "load_package_settings",
    "parse_capability_tier",
    "resolve_yarn_settings",
    "strand",
]
