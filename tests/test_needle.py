"""
Tests for needle SDK - verifies Yarn base class, decorators, schema generation, and MCP serialization.
"""

from needle import CapabilityTier, Yarn, parse_capability_tier, strand


class SampleYarn(Yarn):
    """Sample testing Yarn."""

    def __init__(self) -> None:
        super().__init__(name="sample", layer=42)

    @strand(tier=CapabilityTier.INTERACT, description="Launch an application")
    def launch(self, app_name: str, wait: bool = False) -> str:
        """Launch app documentation."""
        return f"launched {app_name} (wait={wait})"

    @strand(tier=CapabilityTier.PRIVILEGED, no_timeout=True)
    def sys_task(self) -> str:
        return "priv_done"


def test_capability_tier_parsing() -> None:
    assert parse_capability_tier("observe") == CapabilityTier.OBSERVE
    assert parse_capability_tier(CapabilityTier.PRIVILEGED) == CapabilityTier.PRIVILEGED


def test_yarn_reflection_and_strands() -> None:
    yarn = SampleYarn()
    assert yarn.name == "sample"
    assert yarn.layer == 42
    assert yarn.is_available() is True

    strands = yarn.get_strands()
    assert len(strands) == 2

    launch_strand = next(s for s in strands if s.name == "launch")
    assert launch_strand.tier == CapabilityTier.INTERACT
    assert launch_strand.description == "Launch an application"
    assert "app_name" in launch_strand.parameters
    assert launch_strand.parameters["app_name"]["type"] == "string"
    assert "app_name" in launch_strand.required
    assert "wait" in launch_strand.parameters
    assert launch_strand.parameters["wait"]["default"] is False

    # Execute handler directly
    assert launch_strand.handler is not None
    res = launch_strand.handler(app_name="firefox", wait=True)
    assert res == "launched firefox (wait=True)"

    # Verify MCP serialization
    mcp_def = launch_strand.to_mcp_definition()
    assert mcp_def["name"] == "launch"
    assert "[Capability Tier: INTERACT]" in mcp_def["description"]
    assert "properties" in mcp_def["input_schema"]

    # Verify no_timeout on privileged task
    sys_strand = next(s for s in strands if s.name == "sys_task")
    assert sys_strand.no_timeout is True
    assert sys_strand.timeout is None


def test_yarn_manifest() -> None:
    yarn = SampleYarn()
    manifest = yarn.export_manifest()
    assert manifest["name"] == "sample"
    assert manifest["class_name"] == "SampleYarn"
    assert manifest["layer"] == 42
    assert len(manifest["strands"]) == 2
    launch_data = next(s for s in manifest["strands"] if s["name"] == "launch")
    assert launch_data["tier"] == "interact"
    assert "app_name" in launch_data["parameters"]
    assert "wait" in launch_data["parameters"]


def test_yarn_settings_and_execution() -> None:
    yarn = SampleYarn()
    yarn.set_user_settings({"custom_key": "custom_val"})
    assert yarn.settings["custom_key"] == "custom_val"
    assert yarn.settings.custom_key == "custom_val"

    exec_res = yarn.execute_sync("launch", {"app_name": "term", "wait": True})
    assert exec_res == "launched term (wait=True)"
