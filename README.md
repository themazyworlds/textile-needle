# Needle

Developer SDK and interface contracts for Textile capability yarns and agents.

Needle provides the base classes, decorators, event models, and execution primitives required to build capability packages (yarns) that run inside Textile's desktop intelligence runtime.

---

## Installation

```bash
uv add textile-needle
```

or via pip:

```bash
pip install textile-needle
```

---

## Core Primitives

- **`Yarn`**: Base class for capability packages. Manages layer declaration, configuration schemas, lifecycle hooks (`is_available`, `on_load`, `on_unload`), ambient event emission (`publish_event`), state storage (`set_slot`, `get_slot`), and blackboard notices (`stitch`).
- **`@strand`**: Decorator exposing functions as executable tool capabilities with parameter schemas, capability tiers (`OBSERVE`, `INTERACT`, `MUTATE`, `PRIVILEGED`), timeouts, and resource tags.
- **Events (`EventFrame`, `EventUrgency`)**: Standardized event envelopes with urgency tiers (`AMBIENT`, `NOTICE`, `ALERT`, `FLASH`) for cross-process synchronization.
- **Guardrails (`ScopedPath`, `SessionProcessGuard`, `AccessBoundaryError`)**: Confinement primitives for mathematical filesystem root anchors and POSIX session boundary validation.
- **Worker (`needle.worker`)**: Standard subprocess execution target executed in isolated virtual environments.

---

## Quickstart

### 1. Define a Capability Yarn

```python
from needle import CapabilityTier, EventUrgency, Yarn, strand


class SystemControlYarn(Yarn):
    name = "system_control"
    layer = 50

    def is_available(self) -> bool:
        return True

    @strand(tier=CapabilityTier.OBSERVE)
    def get_uptime(self) -> str:
        """Return system uptime information."""
        with open("/proc/uptime", "r", encoding="utf-8") as f:
            seconds = float(f.read().split()[0])
        return f"{seconds:.1f} seconds"

    @strand(tier=CapabilityTier.MUTATE)
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
requires-python = ">=3.14"
dependencies = [
    "textile-needle>=0.1.0",
]

[tool.textile]
tailor = "system"
layer = 50
resources = ["fs:/proc"]
```

---

## Capability Tiers

| Tier | Policy Gate | Sandboxing Profile | Typical Operations |
| :--- | :--- | :--- | :--- |
| `OBSERVE` | Open | Read-only bind mounts | Telemetry, process queries, status checks |
| `INTERACT` | Open | Workspace and network mounts | Desktop notifications, window focus, clipboard |
| `MUTATE` | 2FA Required | Isolated write mounts | Configuration updates, file modifications |
| `PRIVILEGED` | 2FA Required | Host execution boundary | Session exit, power state changes, system reboots |

---

## Layer Priority Reference

Higher layers override strands declared in lower layers:

| Layer Constant | Value | Scope |
| :--- | :--- | :--- |
| `LAYER_CORE_POSIX_THRESHOLD` | 0 | Core POSIX system utilities |
| `LAYER_DESKTOP_PROTOCOL_THRESHOLD` | 50 | Protocols (D-Bus, MPRIS, Wayland) |
| `LAYER_COMPOSITOR_DE_THRESHOLD` | 100 | Compositor / Desktop environment (Hyprland, GNOME) |
| `LAYER_SESSION_MANAGER_THRESHOLD` | 150 | Session managers (UWSM, systemd scopes) |
| `LAYER_USER_OVERRIDE_THRESHOLD` | 1000 | User local scripts and explicit overrides |

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
