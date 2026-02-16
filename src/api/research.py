"""
Research / Pirate Intelligence API Router
==========================================

HAL API endpoints for the pirate intelligence system.
These endpoints allow OpenClaw skills to trigger research activities
and read intel digests without running the full daemon.

Endpoints:
    GET  /api/research/status       - Get pirate daemon status
    GET  /api/research/digest       - Get latest intel digest
    GET  /api/research/targets      - Get tracked agents/targets
    POST /api/research/scan/github  - Trigger a GitHub scan cycle
    POST /api/research/scan/onchain - Trigger an on-chain stalking cycle
    POST /api/research/scan/social  - Trigger a social intel cycle
    POST /api/research/briefing     - Generate a full intel briefing
"""

import json
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/research", tags=["research"])

PROJECT_ROOT = Path(__file__).parent.parent.parent
INTEL_DIR = PROJECT_ROOT / "data" / "intel"
DIGEST_DIR = INTEL_DIR / "digests"


@router.get("/status")
async def get_research_status():
    """Get pirate intelligence daemon status."""
    try:
        from src.research.pirate import get_pirate_daemon
        daemon = get_pirate_daemon()
        return daemon.get_status()
    except Exception as e:
        # Daemon may not be initialized — return state file info instead
        state_file = INTEL_DIR / "pirate_state.json"
        if state_file.exists():
            try:
                state = json.loads(state_file.read_text(encoding="utf-8"))
                state["running"] = False
                state["note"] = "Daemon not active — showing last saved state"
                return state
            except (json.JSONDecodeError, OSError):
                pass
        return {
            "running": False,
            "error": str(e),
            "note": "Pirate daemon not initialized",
        }


@router.get("/digest")
async def get_latest_digest(
    limit: int = Query(1, ge=1, le=10, description="Number of recent digests"),
):
    """Get the latest intel digest(s)."""
    DIGEST_DIR.mkdir(parents=True, exist_ok=True)

    digests = sorted(DIGEST_DIR.glob("*.json"), reverse=True)[:limit]
    if not digests:
        return {"digests": [], "note": "No digests generated yet"}

    results = []
    for digest_file in digests:
        try:
            data = json.loads(digest_file.read_text(encoding="utf-8"))
            results.append(data)
        except (json.JSONDecodeError, OSError) as e:
            results.append({"file": digest_file.name, "error": str(e)})

    return {"digests": results, "count": len(results)}


@router.get("/targets")
async def get_tracked_targets():
    """Get the list of tracked agents/repos/wallets."""
    targets_file = Path(__file__).parent.parent / "research" / "targets.yaml"

    if not targets_file.exists():
        return {"targets": {}, "note": "targets.yaml not found"}

    try:
        import yaml
        with open(targets_file, encoding="utf-8") as f:
            targets = yaml.safe_load(f) or {}
        return {
            "agents": len(targets.get("agents", [])),
            "repos": len(targets.get("repos", [])),
            "wallets": len(targets.get("wallets", [])),
            "targets": targets,
        }
    except ImportError:
        # PyYAML not installed — return raw text
        return {"raw": targets_file.read_text(encoding="utf-8"), "note": "PyYAML not available"}
    except Exception as e:
        return {"error": str(e)}


@router.get("/intel")
async def get_intel_files(
    category: Optional[str] = Query(
        None,
        description="Filter by category: github, onchain, social, code_analysis",
    ),
    limit: int = Query(10, ge=1, le=50),
):
    """List available intelligence files."""
    INTEL_DIR.mkdir(parents=True, exist_ok=True)

    results = []
    search_dirs = [INTEL_DIR]
    if category:
        cat_dir = INTEL_DIR / category
        if cat_dir.exists():
            search_dirs = [cat_dir]
        else:
            return {"files": [], "note": f"Category '{category}' directory not found"}

    for search_dir in search_dirs:
        for f in sorted(search_dir.rglob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:limit]:
            try:
                stat = f.stat()
                results.append({
                    "path": str(f.relative_to(INTEL_DIR)),
                    "size_bytes": stat.st_size,
                    "modified": stat.st_mtime,
                })
            except OSError:
                continue

    return {"files": results[:limit], "count": len(results)}


@router.post("/scan/github")
async def trigger_github_scan():
    """Trigger a GitHub repository scan cycle."""
    try:
        from src.research.pirate import get_pirate_daemon
        daemon = get_pirate_daemon()
        await daemon._do_github()
        return {"status": "completed", "action": "github_scan"}
    except Exception as e:
        logger.error(f"GitHub scan failed: {e}")
        raise HTTPException(status_code=500, detail=f"GitHub scan failed: {str(e)}")


@router.post("/scan/onchain")
async def trigger_onchain_scan():
    """Trigger an on-chain stalking cycle."""
    try:
        from src.research.pirate import get_pirate_daemon
        daemon = get_pirate_daemon()
        await daemon._do_onchain()
        return {"status": "completed", "action": "onchain_scan"}
    except Exception as e:
        logger.error(f"On-chain scan failed: {e}")
        raise HTTPException(status_code=500, detail=f"On-chain scan failed: {str(e)}")


@router.post("/scan/social")
async def trigger_social_scan():
    """Trigger a social intelligence gathering cycle."""
    try:
        from src.research.pirate import get_pirate_daemon
        daemon = get_pirate_daemon()
        await daemon._do_social()
        return {"status": "completed", "action": "social_scan"}
    except Exception as e:
        logger.error(f"Social scan failed: {e}")
        raise HTTPException(status_code=500, detail=f"Social scan failed: {str(e)}")


@router.post("/briefing")
async def trigger_briefing():
    """Generate a full intelligence briefing."""
    try:
        from src.research.pirate import get_pirate_daemon
        daemon = get_pirate_daemon()
        await daemon._do_briefing()
        return {"status": "completed", "action": "intel_briefing"}
    except Exception as e:
        logger.error(f"Briefing generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Briefing failed: {str(e)}")
