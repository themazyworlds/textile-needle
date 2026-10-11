# Needle 🪡

**The sharp, minimal developer SDK for Textile Yarns, Strands, and Desktop AI Agents.**

Needle provides the core primitives and interface contracts for building capability plugins (Yarns) and connecting client agents to the Textile desktop intelligence fabric.

## Installation

```bash
uv add textile-needle
```

## Quickstart

### 1. Authoring a Yarn

```python
from needle import Yarn, strand, CapabilityTier

class MyDesktopYarn(Yarn):
    name = "launcher"
    layer = 50

    @strand(tier=CapabilityTier.INTERACT)
    def open_window(self, app_name: str) -> str:
        """Launch and focus an application."""
        return f"Launched {app_name}"
```

### 2. Connecting an Agent via Twill MCP

```python
from needle import TwillClient

# Connect to Textile Twill stdio MCP server in one call:
toolset = await TwillClient.create_mcp_toolset()
```
