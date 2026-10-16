# Needle

Developer SDK and interface contracts for Textile capability yarns and agents.

Needle provides the base classes, decorators, event models, and execution primitives required to build capability packages (yarns) that run inside Textile's desktop intelligence runtime.

---

## Installation

```bash
uv add needle
```

or via pip:

```bash
pip install needle
```

---

## Core Primitives

- **`Yarn`**: Base class for capability packages. Manages layer declaration, configuration schemas, lifecycle hooks (`is_available`, `on_load`, `on_unload`), ambient event emission (`publish_event`), state storage (`set_slot`, `get_slot`), and blackboard notices (`stitch`).
- **`@strand`**: Declarative tier decorators (`@strand.observe`, `@strand.interact`, `@strand.mutate`, `@strand.privileged`, `@strand.system_exec`) exposing functions as executable tool capabilities with parameter schemas, tier-aware timeouts, reasons, and fallbacks.
- **Events (`EventFrame`, `EventUrgency`)**: Standardized event envelopes with urgency tiers (`AMBIENT`, `NOTICE`, `ALERT`, `FLASH`) for cross-process synchronization.
- **Guardrails (`ScopedPath`, `SessionProcessGuard`, `AccessBoundaryError`)**: Confinement primitives for mathematical filesystem root anchors and POSIX session boundary validation.
- **Worker (`needle.worker`)**: Standard subprocess execution target executed in isolated virtual environments.

---

## Quickstart

### 1. Define a Capability Yarn

```python
from needle import EventUrgency, Yarn, strand


class SystemControlYarn(Yarn):
    name = "system_control"
    layer = 50

    def is_available(self) -> bool:
        return True

    @strand.observe
    def get_uptime(self) -> str:
        """Return system uptime information."""
        with open("/proc/uptime", "r", encoding="utf-8") as f:
            seconds = float(f.read().split()[0])
        return f"{seconds:.1f} seconds"

    @strand.mutate(reason="Broadcasting system alert notice")
    def trigger_alert(self, message: str) -> str:
        """Broadcast a system alert event."""
        self.publish_event(
            topic="system.alert",
            summary=message,
            urgency=EventUrgency.ALERT,
            data={"message": message},
        )
        return "Alert dispatched"
```

### 2. Configure `pyproject.toml`

Every capability yarn is distributed as a self-contained directory containing standard package metadata:

```toml
[project]
name = "textile-yarn-system-control"
version = "0.1.0"
description = "System control capabilities for Textile"
requires-python = ">=3.15"
dependencies = [
    "needle>=0.1.0",
]

[tool.textile]
tailor = "system"
layer = 50
resources = ["fs:/proc"]
```

---

## Capability Tiers

| Tier | Policy Gate | Default Timeout | Sandboxing Profile | Typical Operations |
| :--- | :--- | :--- | :--- | :--- |
| `OBSERVE` | Open | 10s | Read-only container mount | Telemetry, process queries, status checks |
| `INTERACT` | Open | 15s | Workspace and network mounts | Desktop notifications, window focus, clipboard |
| `MUTATE` | 2FA Required | 60s | Isolated write mounts | Configuration updates, file modifications |
| `PRIVILEGED` | 2FA Required | 300s | Host execution boundary | System reconfiguration, package updates |
| `SYSTEM_EXEC` | 2FA Required | 120s | Ephemeral sandbox | Command execution, terminal tools |

---

## Layer Priority

Yarns declare an integer `layer` (0 to 1000, default `50` / `DEFAULT_LAYER`). When multiple yarns provide conflicting strands or capabilities, higher layers deterministically override lower layers:

- `0`: Core POSIX / baseline system fabric
- `50`: Protocols & middleware (default priority)
- `100`: Desktop environment & compositor integration (Hyprland, Caelestia)
- `150`: Session managers & companions (UWSM)
- `1000`: Explicit user overrides & custom local scripts

---

## Guardrails

### ScopedPath

Enforces that file operations remain strictly relative to a declared anchor root, rejecting path traversals and symbolic escapes:

```python
from pathlib import Path
from needle.guardrails import AccessBoundaryError, ScopedPath

scoped = ScopedPath(root=Path.home())
safe_target = scoped.resolve("documents/notes.txt")  # OK
escaped = scoped.resolve("../../etc/shadow")  # Raises AccessBoundaryError
```

### SessionProcessGuard

Validates that target process IDs share the active POSIX desktop session:

```python
from needle.guardrails import AccessBoundaryError, SessionProcessGuard

target_pid = SessionProcessGuard.verify_pid_in_session(1234)
```
