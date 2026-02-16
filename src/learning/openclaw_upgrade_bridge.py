"""
OpenClaw -> Ralph upgrade request bridge.

Goal
- Make OpenClaw "self-improvement" output actionable by converting structured
  lines written into OpenClaw memory into `ganjamon-agent/data/upgrade_requests.json`.

Why
- OpenClaw cron jobs are LLM-driven; they often produce plans in memory but do not
  automatically feed the legacy Ralph pipeline.
- Ralph loops (Surgical + Evolutionary) are built around UpgradeSystem +
  `data/upgrade_requests.json`.

Contract (what OpenClaw should write)
- One or more single-line JSON objects prefixed with:
  `UPGRADE_REQUEST_JSON: {...}`

Example:
UPGRADE_REQUEST_JSON: {"title":"Fix Farcaster reply loop","description":"...","category":"fix_bug","priority":"high","reason":"...","affected_domains":["social"]}

This module is intentionally deterministic and does not call any LLMs.
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


UPGRADE_LINE_PREFIX = "UPGRADE_REQUEST_JSON:"
_UPGRADE_LINE_RE = re.compile(r"^UPGRADE_REQUEST_JSON:\s*(\{.*\})\s*$")


@dataclass
class BridgeConfig:
    project_root: Path
    memory_dir: Path
    ganjamon_data_dir: Path
    state_path: Path
    poll_seconds: int = 60


def _safe_read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _atomic_write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(tmp, path)


def _load_state(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(_safe_read_text(path))
    except Exception:
        return {"version": 1, "files": {}}


def _save_state(path: Path, state: Dict[str, Any]) -> None:
    _atomic_write_json(path, state)


def _iter_new_lines(path: Path, start_offset: int) -> Tuple[int, List[str]]:
    """
    Returns: (new_offset, lines)
    """
    # If file shrank/rotated, restart from beginning.
    try:
        size = path.stat().st_size
    except FileNotFoundError:
        return start_offset, []
    if start_offset < 0 or start_offset > size:
        start_offset = 0

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        f.seek(start_offset)
        text = f.read()
        new_offset = f.tell()
    # Keep line endings irrelevant: splitlines() drops trailing newline.
    return new_offset, text.splitlines()


def _parse_upgrade_lines(lines: Iterable[str]) -> List[Dict[str, Any]]:
    upgrades: List[Dict[str, Any]] = []
    for line in lines:
        m = _UPGRADE_LINE_RE.match(line.strip())
        if not m:
            continue
        raw = m.group(1)
        try:
            obj = json.loads(raw)
        except Exception:
            continue
        if isinstance(obj, dict):
            upgrades.append(obj)
    return upgrades


def _normalize_str(v: Any) -> str:
    return str(v).strip()


def _to_enum_value(raw: str, allowed: Iterable[str], default: str) -> str:
    key = raw.strip().lower()
    if key in allowed:
        return key
    return default


def _submit_upgrades_via_upgrade_system(
    upgrades: List[Dict[str, Any]], ganjamon_data_dir: Path
) -> List[Tuple[str, str]]:
    """
    Returns list of (request_id, title) that were submitted/deduped.
    """
    if not upgrades:
        return []

    # Import UpgradeSystem from the trading agent code (local file import, no network).
    import sys

    agent_src = ganjamon_data_dir.parent / "src"
    sys.path.insert(0, str(agent_src))
    try:
        from learning.upgrade_system import UpgradeSystem, UpgradeCategory, UpgradePriority  # type: ignore
    finally:
        try:
            sys.path.remove(str(agent_src))
        except Exception:
            pass

    system = UpgradeSystem(data_dir=str(ganjamon_data_dir))

    allowed_categories = {e.value for e in UpgradeCategory}
    allowed_priorities = {e.value for e in UpgradePriority}

    submitted: List[Tuple[str, str]] = []
    for u in upgrades:
        title = _normalize_str(u.get("title") or "")
        description = _normalize_str(u.get("description") or u.get("details") or "")
        reason = _normalize_str(u.get("reason") or "")
        if not title or not description:
            continue

        category_raw = _normalize_str(u.get("category") or "self_improvement")
        priority_raw = _normalize_str(u.get("priority") or "medium")
        category = UpgradeCategory(_to_enum_value(category_raw, allowed_categories, "self_improvement"))
        priority = UpgradePriority(_to_enum_value(priority_raw, allowed_priorities, "medium"))

        affected = u.get("affected_domains") or u.get("affectedDomains") or u.get("domains") or []
        if isinstance(affected, str):
            affected_domains = [affected]
        elif isinstance(affected, list):
            affected_domains = [str(x) for x in affected if str(x).strip()]
        else:
            affected_domains = []

        req_id = system.request_upgrade(
            title=title,
            description=description,
            category=category,
            priority=priority,
            reason=reason,
            suggested_approach=_normalize_str(u.get("suggested_approach") or u.get("approach") or "") or None,
            suggested_sources=u.get("suggested_sources") or u.get("sources") or None,
            affected_domains=affected_domains,
        )
        submitted.append((req_id, title))

    return submitted


def run_once(cfg: BridgeConfig, day: Optional[str] = None) -> Dict[str, Any]:
    """
    Process new UPGRADE_REQUEST_JSON lines from today's memory file, update upgrade_requests.json.
    Returns a short summary dict for logs.
    """
    now = datetime.now()
    day = day or f"{now:%Y-%m-%d}"
    mem_file = cfg.memory_dir / f"{day}.md"

    state = _load_state(cfg.state_path)
    files = state.setdefault("files", {})
    rec = files.setdefault(day, {"offset": 0, "lastRunAt": None})
    start_offset = int(rec.get("offset") or 0)

    new_offset, lines = _iter_new_lines(mem_file, start_offset)
    upgrades = _parse_upgrade_lines(lines)
    submitted = _submit_upgrades_via_upgrade_system(upgrades, cfg.ganjamon_data_dir)

    rec["offset"] = new_offset
    rec["lastRunAt"] = now.isoformat()
    _save_state(cfg.state_path, state)

    return {
        "day": day,
        "memory_file": str(mem_file),
        "scanned_lines": len(lines),
        "found_upgrades": len(upgrades),
        "submitted": len(submitted),
        "submitted_ids": [x[0] for x in submitted][-10:],
    }


def run_loop(cfg: BridgeConfig, shutdown_event) -> None:
    """
    Loop forever until shutdown_event is set.
    """
    while not shutdown_event.is_set():
        try:
            run_once(cfg)
        except Exception:
            # Never crash the supervisor.
            pass
        shutdown_event.wait(cfg.poll_seconds)


def default_config(project_root: Optional[Path] = None) -> BridgeConfig:
    root = project_root or Path(__file__).resolve().parents[2]
    return BridgeConfig(
        project_root=root,
        memory_dir=root / "openclaw-workspace" / "ganjamon" / "memory",
        ganjamon_data_dir=root / "agents" / "ganjamon" / "data",
        state_path=root / "data" / "openclaw_upgrade_bridge_state.json",
        poll_seconds=int(os.getenv("OPENCLAW_UPGRADE_BRIDGE_POLL_SECONDS", "60")),
    )

