#!/usr/bin/env python3
"""
ops_snapshot.py

Single-file, dependency-free operational snapshot for the Chromebook runtime.

Goal: quickly answer "are all systems up?" without relying on brittle shell quoting.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


def _http_get(url: str, timeout_s: float = 2.5) -> tuple[int, str]:
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            raw = resp.read()
            try:
                body = raw.decode("utf-8", errors="replace")
            except Exception:
                body = str(raw[:200])
            return int(getattr(resp, "status", 200)), body
    except urllib.error.HTTPError as e:
        try:
            body = (e.read() or b"").decode("utf-8", errors="replace")
        except Exception:
            body = ""
        return int(getattr(e, "code", 0) or 0), body
    except Exception as e:
        return 0, str(e)


def _http_head_ok(url: str, timeout_s: float = 2.0) -> tuple[bool, str]:
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            _ = resp.read(1)
            return int(getattr(resp, "status", 200)) == 200, f"HTTP {getattr(resp, 'status', 200)}"
    except Exception as e:
        return False, str(e)


def _run(cmd: list[str], timeout_s: float = 8.0) -> tuple[int, str]:
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True, timeout=timeout_s)
        return 0, out
    except subprocess.CalledProcessError as e:
        return int(e.returncode or 1), (e.output or "")
    except Exception as e:
        return 1, str(e)


def _fmt_ts(ts: float | int | None) -> str:
    if ts is None:
        return "-"
    try:
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(float(ts)))
    except Exception:
        return "-"


def _fmt_ms(ms: float | int | None) -> str:
    if ms is None:
        return "-"
    try:
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(float(ms) / 1000.0))
    except Exception:
        return "-"


def _print_json_preview(label: str, body: str, max_chars: int = 900) -> None:
    print(label)
    try:
        obj = json.loads(body)
        s = json.dumps(obj, indent=2, sort_keys=True)
        print(s[:max_chars] + ("..." if len(s) > max_chars else ""))
    except Exception:
        print(body[:max_chars] + ("..." if len(body) > max_chars else ""))


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    os.chdir(repo)

    print("== ops snapshot ==")
    print(f"time: {_fmt_ts(time.time())}")
    print(f"cwd: {repo}")
    print()

    # --- services ---
    print("== services (systemd --user) ==")
    for unit in ["grokmon.service", "ganja-mon-bot.service"]:
        rc, out = _run(["systemctl", "--user", "--no-pager", "--full", "status", unit], timeout_s=6.0)
        head = "\n".join(out.splitlines()[:35])
        print(f"[{unit}] rc={rc}")
        print(head)
        print()

    # --- endpoints ---
    print("== HAL endpoints ==")
    for url in [
        "http://127.0.0.1:8000/api/health",
        "http://127.0.0.1:8000/api/sensors",
        "http://127.0.0.1:8000/api/grow/stage",
        "http://127.0.0.1:8000/api/ai/latest",
        "http://127.0.0.1:8000/api/plant-progress",
    ]:
        code, body = _http_get(url, timeout_s=3.5)
        print(f"{url} -> {code}")
        if code and body:
            _print_json_preview("body:", body, max_chars=700)
        print()

    # --- OpenClaw ---
    print("== OpenClaw ==")
    ok, detail = _http_head_ok("http://127.0.0.1:18789/__openclaw__/canvas/", timeout_s=2.5)
    print(f"canvas: ok={ok} detail={detail}")
    print()

    # --- A2A/endpoint ---
    print("== A2A endpoint (8080) ==")
    code, body = _http_get("http://127.0.0.1:8080/admin/ping", timeout_s=2.5)
    print(f"/admin/ping -> {code}")
    if body:
        print(body[:500] + ("..." if len(body) > 500 else ""))
    print()

    # --- OpenClaw cron ---
    print("== OpenClaw cron store ==")
    cron_path = repo / "openclaw-workspace" / "cron" / "cron.json"
    if cron_path.exists():
        try:
            data = json.loads(cron_path.read_text(encoding="utf-8"))
            jobs = data.get("jobs") or []
            now_ms = int(time.time() * 1000)
            running = [
                (j.get("name") or j.get("id"))
                for j in jobs
                if isinstance((j.get("state") or {}).get("runningAtMs"), (int, float))
            ]
            due = [
                (j.get("name") or j.get("id"))
                for j in jobs
                if isinstance((j.get("state") or {}).get("nextRunAtMs"), (int, float))
                and now_ms >= int((j.get("state") or {}).get("nextRunAtMs"))
            ]
            print(f"jobs_total: {len(jobs)}")
            print(f"running_markers: {len(running)}")
            print(f"due_now: {len(due)}")

            key = {
                "Grow Decision Cycle",
                "Cross-Platform Social",
                "Research Cycle",
                "Self Improvement",
                "Reflection",
                "Daily NFT",
                "Auto-Review",
                "Reputation Publishing",
                "Alpha Distiller",
            }
            print("name\tenabled\tlastRun\tlastStatus\tnextRun\trunning")
            for j in jobs:
                name = j.get("name") or j.get("id")
                if name not in key:
                    continue
                st = j.get("state") or {}
                print(
                    "\t".join(
                        [
                            str(name),
                            "on" if j.get("enabled") else "off",
                            _fmt_ms(st.get("lastRunAtMs")),
                            str(st.get("lastStatus") or "-"),
                            _fmt_ms(st.get("nextRunAtMs")),
                            "yes"
                            if isinstance(st.get("runningAtMs"), (int, float))
                            else "no",
                        ]
                    )
                )
            if running:
                print(f"running_examples: {running[:6]}")
            if due:
                print(f"due_examples: {due[:6]}")
        except Exception as e:
            print(f"failed to parse {cron_path}: {e}")
    else:
        print(f"missing: {cron_path}")
    print()

    # --- memory (OpenClaw workspace + mirror) ---
    print("== memory ==")
    mem_dir = repo / "openclaw-workspace" / "ganjamon" / "memory"
    today = time.strftime("%Y-%m-%d", time.localtime())
    mem_file = mem_dir / f"{today}.md"
    print(f"openclaw_memory_dir: {mem_dir} exists={mem_dir.exists()}")
    if mem_file.exists():
        st = mem_file.stat()
        print(f"openclaw_memory_today: {mem_file} mtime={_fmt_ts(st.st_mtime)} size={st.st_size}")
        tail = mem_file.read_text(encoding="utf-8", errors="replace").splitlines()[-12:]
        print("tail:")
        for line in tail:
            print(line[:300])
    else:
        print(f"openclaw_memory_today: missing ({mem_file})")
    # episodic memory (HAL)
    epi = repo / "data" / "episodic_memory.json"
    if epi.exists():
        st = epi.stat()
        print(f"episodic_memory: {epi} mtime={_fmt_ts(st.st_mtime)} size={st.st_size}")
    else:
        print(f"episodic_memory: missing ({epi})")
    print()

    # --- self-improvement bridge ---
    print("== self-improvement bridge ==")
    upgrades = repo / "cloned-repos" / "ganjamon-agent" / "data" / "upgrade_requests.json"
    if upgrades.exists():
        st = upgrades.stat()
        print(f"upgrade_requests: {upgrades} mtime={_fmt_ts(st.st_mtime)} size={st.st_size}")
        try:
            o = json.loads(upgrades.read_text(encoding="utf-8"))
            if isinstance(o, list):
                print(f"upgrade_requests_count: {len(o)}")
        except Exception:
            pass
    else:
        print(f"upgrade_requests: missing ({upgrades})")
    print()

    # --- plant ops: last watering ---
    print("== plant ops: watering ==")
    water_state = repo / "data" / "gentle_watering_state.json"
    if water_state.exists():
        try:
            o = json.loads(water_state.read_text(encoding="utf-8"))
            print(f"last_water_ts: {o.get('last_water_ts')}")
            print(f"last_water_ml: {o.get('last_water_ml')}")
            print(f"last_stage: {o.get('last_stage')}")
        except Exception as e:
            print(f"failed to parse {water_state}: {e}")
    else:
        print(f"missing: {water_state}")
    print()

    # --- quick runtime load ---
    print("== machine ==")
    for cmd in (["uptime"], ["free", "-h"], ["df", "-h", "/"]):
        rc, out = _run(cmd, timeout_s=5.0)
        print("$", " ".join(cmd), f"(rc={rc})")
        print(out.strip())
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

