from pathlib import Path
from typing import Any

import orjson
import pytest

from needle import DEFAULT_LAYER, CapabilityTier, Yarn, parse_capability_tier, strand


class SampleYarn(Yarn):
    """Sample testing Yarn."""

    def __init__(self) -> None:
        super().__init__(name="sample", layer=42)

    @strand.interact(description="Launch an application")
    def launch(self, app_name: str, wait: bool = False) -> str:
        """Launch app documentation."""
        return f"launched {app_name} (wait={wait})"

    @strand.privileged(reason="System reconfiguration required", fallback=False, no_timeout=True)
    def sys_task(self) -> str:
        return "priv_done"

    @strand.observe
    def get_metrics(self) -> str:
        return "metrics"

    @strand.mutate(reason="Writing configuration files")
    def save_config(self, key: str, val: str) -> str:
        return f"{key}={val}"

    @strand.system_exec()
    def run_cmd(self, cmd: str) -> str:
        return f"ran {cmd}"


class DefaultLayerYarn(Yarn):
    """Yarn using default layer."""


def test_capability_tier_parsing() -> None:
    assert parse_capability_tier("observe") == CapabilityTier.OBSERVE
    assert parse_capability_tier(CapabilityTier.PRIVILEGED) == CapabilityTier.PRIVILEGED


def test_yarn_default_layer() -> None:
    yarn = DefaultLayerYarn()
    assert yarn.layer == DEFAULT_LAYER
    assert yarn.layer == 50


def test_direct_strand_call_raises_type_error() -> None:
    import pytest

    with pytest.raises(TypeError, match="Direct @strand is not supported"):
        strand(lambda: None)  # type: ignore[operator]


def test_yarn_reflection_and_strands() -> None:
    yarn = SampleYarn()
    assert yarn.name == "sample"
    assert yarn.layer == 42
    assert yarn.is_available() is True

    strands = yarn.get_strands()
    assert len(strands) == 5

    launch_strand = next(s for s in strands if s.name == "launch")
    assert launch_strand.tier == CapabilityTier.INTERACT
    assert launch_strand.description == "Launch an application"
    assert launch_strand.timeout == 15.0
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

    # Verify privileged strand with reason, fallback, no_timeout
    sys_strand = next(s for s in strands if s.name == "sys_task")
    assert sys_strand.tier == CapabilityTier.PRIVILEGED
    assert sys_strand.no_timeout is True
    assert sys_strand.timeout is None
    assert sys_strand.reason == "System reconfiguration required"
    assert sys_strand.fallback is False

    # Verify observe tier default timeout 10.0s
    obs_strand = next(s for s in strands if s.name == "get_metrics")
    assert obs_strand.tier == CapabilityTier.OBSERVE
    assert obs_strand.timeout == 10.0

    # Verify mutate tier default timeout 60.0s and reason
    mut_strand = next(s for s in strands if s.name == "save_config")
    assert mut_strand.tier == CapabilityTier.MUTATE
    assert mut_strand.timeout == 60.0
    assert mut_strand.reason == "Writing configuration files"

    # Verify system_exec tier default timeout 120.0s
    exec_strand = next(s for s in strands if s.name == "run_cmd")
    assert exec_strand.tier == CapabilityTier.SYSTEM_EXEC
    assert exec_strand.timeout == 120.0


def test_yarn_manifest() -> None:
    yarn = SampleYarn()
    manifest = yarn.export_manifest()
    assert manifest["name"] == "sample"
    assert manifest["class_name"] == "SampleYarn"
    assert manifest["layer"] == 42
    assert len(manifest["strands"]) == 5
    launch_data = next(s for s in manifest["strands"] if s["name"] == "launch")
    assert launch_data["tier"] == "interact"
    assert launch_data["timeout"] == 15.0
    assert "app_name" in launch_data["parameters"]
    assert "wait" in launch_data["parameters"]

    sys_data = next(s for s in manifest["strands"] if s["name"] == "sys_task")
    assert sys_data["reason"] == "System reconfiguration required"
    assert sys_data["fallback"] is False


def test_yarn_settings_and_execution() -> None:
    yarn = SampleYarn()
    yarn.set_user_settings({"custom_key": "custom_val"})
    assert yarn.settings["custom_key"] == "custom_val"
    assert yarn.settings.custom_key == "custom_val"

    exec_res = yarn.execute_sync("launch", {"app_name": "term", "wait": True})
    assert exec_res == "launched term (wait=True)"


class DictReturnYarn(Yarn):
    """Yarn returning structured dictionary and list results."""

    @strand.observe
    def get_data(self) -> dict[str, Any]:
        return {"status": "ok", "count": 10}


def test_yarn_dict_result_serialization() -> None:
    yarn = DictReturnYarn()
    res = yarn.execute_sync("get_data", {})
    assert orjson.loads(res) == {"status": "ok", "count": 10}


def test_manifest_probe_and_main(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    from needle.manifest import PROBE_PREFIX, main, probe_file

    yarn_file = tmp_path / "probed_yarn.py"
    yarn_file.write_text(
        "from needle import Yarn, strand\n"
        "class ProbedTestYarn(Yarn):\n"
        "    @strand.observe\n"
        "    def hello(self) -> str:\n"
        "        return 'world'\n",
        encoding="utf-8",
    )

    manifests = probe_file(yarn_file)
    assert len(manifests) == 1
    assert manifests[0]["name"] == "probedtest"
    assert manifests[0]["class_name"] == "ProbedTestYarn"

    monkeypatch.setattr("sys.argv", ["needle.manifest", str(yarn_file)])
    main()
    captured = capsys.readouterr().out
    assert PROBE_PREFIX in captured
    json_part = captured.split(PROBE_PREFIX, 1)[1].strip()
    parsed = orjson.loads(json_part)
    assert parsed["name"] == "probedtest"
