"""
Centralized path definitions for the Grok & Mon project.

All project-wide paths derive from PROJECT_ROOT. This module eliminates
hardcoded path strings scattered across the codebase and provides a single
place to update if directories are ever moved.

Usage:
    from src.core.paths import PROJECT_ROOT, AGENT_DIR, TRADING_DATA
"""

from pathlib import Path
import os

# The canonical project root — override with GROKMON_ROOT env var if needed.
# Default: two levels up from this file (src/core/paths.py → sol-cannabis/)
PROJECT_ROOT = Path(os.getenv("GROKMON_ROOT", str(Path(__file__).resolve().parents[2])))

# --- First-party agents (things we RUN as subprocesses) ---
AGENTS_DIR = PROJECT_ROOT / "agents"
AGENT_DIR = AGENTS_DIR / "ganjamon"           # Trading agent
TRADING_DATA = AGENT_DIR / "data"             # Trading agent data dir
FARCASTER_DIR = AGENTS_DIR / "farcaster"      # Farcaster posting agent

# --- Reference repos (things we READ from) ---
REFS_ROOT = PROJECT_ROOT / "cloned-repos"

# --- Core application ---
SRC_DIR = PROJECT_ROOT / "src"
DATA_DIR = PROJECT_ROOT / "data"
CONFIG_DIR = PROJECT_ROOT / "config"

# --- OpenClaw ---
OPENCLAW_WORKSPACE = PROJECT_ROOT / "openclaw-workspace"
OPENCLAW_CONFIG = OPENCLAW_WORKSPACE / "config" / "openclaw.json"
OPENCLAW_MEMORY = OPENCLAW_WORKSPACE / "ganjamon" / "memory"

# --- Frontend / deploy ---
PAGES_DEPLOY = PROJECT_ROOT / "pages-deploy"
CLOUDFLARE_DIR = PROJECT_ROOT / "cloudflare"

# --- Voice / streaming (Windows-only) ---
RASTA_VOICE_DIR = PROJECT_ROOT / "rasta-voice"

# --- Other project dirs ---
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
DOCS_DIR = PROJECT_ROOT / "docs"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
ASSETS_DIR = PROJECT_ROOT / "assets"
