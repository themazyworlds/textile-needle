"""
needle.client - Lightweight connection helpers for connecting client agents to Textile Twill MCP.
"""

import os
from pathlib import Path
from typing import Any


class TwillClient:
    """Helper client to spawn or connect to the Textile Twill stdio MCP server."""

    @staticmethod
    def get_server_parameters(
        textile_dir: str | Path | None = None,
        env: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Return parameters dict suitable for MCPServerStdio or standard MCP client transports.

        Includes full desktop session environment by default (preserving Wayland, Hyprland, D-Bus).
        """
        target_dir = Path(textile_dir).resolve() if textile_dir else Path.home() / "Projects" / "textile"
        cmd_args = ["run"]
        if target_dir.is_dir():
            cmd_args.extend(["--directory", str(target_dir)])
        cmd_args.extend(["textile", "twill"])

        merged_env = dict(os.environ)
        if env:
            merged_env.update(env)

        return {
            "command": "uv",
            "args": cmd_args,
            "cwd": str(target_dir) if target_dir.is_dir() else None,
            "env": merged_env,
        }

