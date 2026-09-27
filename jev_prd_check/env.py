"""Tiny .env loader -- no external dependency, since env vars set in the
user's own shell don't reach separate tool invocations anyway."""

from __future__ import annotations

import os
from pathlib import Path


GLOBAL_ENV_PATH = Path.home() / ".config" / "jev-prd-check" / ".env"

# plugin.json's userConfig keys -> the canonical env var names the rest of
# this package expects. Claude Code exports every userConfig option to hook
# processes as CLAUDE_PLUGIN_OPTION_<KEY> (key uppercased); MCP servers get
# their own env block via ${user_config.KEY} substitution instead (see
# .mcp.json), so this mapping only matters for the hook.
_PLUGIN_OPTION_ENV_MAP = {
    "TYPESAFE_API_KEY": "CLAUDE_PLUGIN_OPTION_TYPESAFE_API_KEY",
    "ADO_ORG_PROJECT": "CLAUDE_PLUGIN_OPTION_ADO_ORG_PROJECT",
    "ADO_PAT": "CLAUDE_PLUGIN_OPTION_ADO_PAT",
}


def load_plugin_options() -> None:
    for canonical, option_var in _PLUGIN_OPTION_ENV_MAP.items():
        value = os.environ.get(option_var)
        if value:
            os.environ.setdefault(canonical, value)


def load_dotenv(path: str | Path) -> None:
    path = Path(path)
    if not path.is_file():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def load_config(local_root: Path | None = None) -> None:
    """Resolve config in priority order: Claude Code plugin userConfig
    (CLAUDE_PLUGIN_OPTION_*, set when actually running as an installed
    plugin) > local_root/.env (dev convenience override) > the stable,
    install-method-independent GLOBAL_ENV_PATH. A plugin installed from a
    marketplace is re-cloned into a cache directory with no .env of its
    own, so GLOBAL_ENV_PATH (or userConfig) is what actually works there."""
    load_plugin_options()
    if local_root is not None:
        load_dotenv(local_root / ".env")
    load_dotenv(GLOBAL_ENV_PATH)
