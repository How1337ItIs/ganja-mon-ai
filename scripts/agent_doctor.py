#!/usr/bin/env python3
"""Agent Doctor — Lightweight health monitor for the GanjaMon unified agent.

Runs hourly via cron. Zero Claude Code cost. Checks the OpenClaw-first
runtime (HAL + OpenClaw gateway + trading agent), imports, API health,
data freshness, memory, and errors. Outputs a structured report to
data/health_report.json.

Usage:
    python scripts/agent_doctor.py          # Run all checks
    python scripts/agent_doctor.py --json   # Output JSON to stdout too
"""

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
AGENT_DIR = PROJECT_ROOT / "cloned-repos" / "ganjamon-agent"
REPORT_PATH = DATA_DIR / "health_report.json"

# Thresholds
MEMORY_WARN_MB = 1200       # Warn at 80% of 1500M limit
MEMORY_CRIT_MB = 1400       # Critical at 93%
STALE_MINUTES = 30          # Data older than this is stale
DISK_WARN_PCT = 85          # Disk usage warning


def run(cmd: str, timeout: int = 10) -> tuple[int, str]:
    """Run a shell command and return (returncode, stdout+stderr)."""
    try:
        r = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return r.returncode, (r.stdout + r.stderr).strip()
    except subprocess.TimeoutExpired:
        return -1, "TIMEOUT"
    except Exception as e:
        return -1, str(e)


def check_subprocesses() -> list[dict]:
    """Check if the unified OpenClaw-first stack is alive."""
    bugs = []

    # Also check by run.py subprocess pattern
    _, run_py_out = run("ps aux | grep 'run.py all' | grep -v grep")
    if not run_py_out:
        bugs.append({
            "severity": "CRITICAL",
            "name": "grokmon_not_running",
            "detail": "Main process (run.py all) not found",
        })
        return bugs

    # Check service status
    rc, status = run("systemctl --user is-active grokmon")
    if "active" not in status:
        bugs.append({
            "severity": "CRITICAL",
            "name": "service_inactive",
            "detail": f"grokmon.service status: {status}",
        })

    # Port probes (cheaper than full process matching).
    rc, ports = run("(ss -ltnp 2>/dev/null || netstat -ltnp 2>/dev/null || true)", timeout=5)
    if ":8000" not in ports:
        bugs.append({
            "severity": "HIGH",
            "name": "hal_port_missing",
            "detail": "HAL API server not listening on :8000",
        })
    if ":18789" not in ports:
        bugs.append({
            "severity": "HIGH",
            "name": "openclaw_port_missing",
            "detail": "OpenClaw gateway not listening on :18789",
        })

    # Best-effort process presence checks.
    _, procs = run("ps -ef", timeout=5)
    if "openclaw-gatewa" not in procs and "openclaw gateway run" not in procs:
        bugs.append({
            "severity": "HIGH",
            "name": "openclaw_process_missing",
            "detail": "OpenClaw gateway process not found in process list",
        })
    if " -m main" not in procs and "ganjamon-agent" not in procs:
        bugs.append({
            "severity": "HIGH",
            "name": "trading_process_missing",
            "detail": "Trading agent process not found in process list",
        })

    return bugs


def check_imports() -> list[dict]:
    """Test critical imports for SyntaxErrors."""
    bugs = []
    test_imports = [
        (
            "trading_agent_main",
            f"cd {AGENT_DIR} && PYTHONPATH={AGENT_DIR} "
            f"{PROJECT_ROOT}/venv/bin/python -c "
            "'import ast; ast.parse(open(\"src/main.py\").read())' 2>&1",
        ),
        (
            "hal_app",
            f"cd {PROJECT_ROOT} && "
            f"{PROJECT_ROOT}/venv/bin/python -c "
            "'import ast; ast.parse(open(\"src/api/app.py\").read())' 2>&1",
        ),
        (
            "light_scheduler",
            f"cd {PROJECT_ROOT} && "
            f"{PROJECT_ROOT}/venv/bin/python -c "
            "'import ast; ast.parse(open(\"src/scheduling/light_scheduler.py\").read())' 2>&1",
        ),
        (
            "gentle_watering",
            f"cd {PROJECT_ROOT} && "
            f"{PROJECT_ROOT}/venv/bin/python -c "
            "'import ast; ast.parse(open(\"scripts/gentle_daily_watering.py\").read())' 2>&1",
        ),
    ]

    for name, cmd in test_imports:
        rc, out = run(cmd, timeout=15)
        if rc != 0 and ("SyntaxError" in out or "IndentationError" in out):
            # Extract file and line from traceback
            file_match = re.search(r'File "([^"]+)", line (\d+)', out)
            detail = out.split("\n")[-1] if out else "Unknown error"
            bug = {
                "severity": "CRITICAL",
                "name": f"syntax_error_{name}",
                "detail": detail[:200],
            }
            if file_match:
                bug["file"] = file_match.group(1)
                bug["line"] = int(file_match.group(2))
            bugs.append(bug)

    return bugs


def check_api_health() -> list[dict]:
    """Check if FastAPI is responding."""
    bugs = []
    rc, out = run("curl -sf http://localhost:8000/api/health 2>/dev/null", timeout=5)
    if rc != 0:
        bugs.append({
            "severity": "HIGH",
            "name": "api_down",
            "detail": "FastAPI health endpoint not responding",
        })
    else:
        try:
            health = json.loads(out)
            if health.get("status") != "healthy":
                bugs.append({
                    "severity": "MEDIUM",
                    "name": "api_unhealthy",
                    "detail": f"Health status: {health.get('status', 'unknown')}",
                })
        except json.JSONDecodeError:
            pass

    return bugs


def check_data_freshness() -> list[dict]:
    """Check if key data files are being updated."""
    bugs = []
    now = time.time()
    stale_threshold = STALE_MINUTES * 60

    # Trading agent liveness signal.
    consciousness_path = AGENT_DIR / "data" / "consciousness.json"
    if consciousness_path.exists():
        age = now - consciousness_path.stat().st_mtime
        if age > stale_threshold * 6:  # 3 hours
            bugs.append({
                "severity": "MEDIUM",
                "name": "stale_consciousness",
                "detail": f"consciousness.json last updated {int(age/60)} minutes ago",
                "file": str(consciousness_path),
            })
    else:
        bugs.append({
            "severity": "MEDIUM",
            "name": "missing_consciousness",
            "detail": f"{consciousness_path} does not exist",
        })

    # Watering: gentle daily watering cron writes this state file.
    gentle_state = DATA_DIR / "gentle_watering_state.json"
    if gentle_state.exists():
        try:
            state = json.loads(gentle_state.read_text())
            last_ts = state.get("last_water_ts") or ""
            if last_ts:
                last_dt = datetime.fromisoformat(str(last_ts).replace("Z", "+00:00"))
                age_h = (datetime.now(timezone.utc) - last_dt).total_seconds() / 3600.0
                if age_h > 36:
                    bugs.append({
                        "severity": "HIGH",
                        "name": "watering_stale",
                        "detail": f"Last gentle watering is {age_h:.1f}h ago ({last_ts})",
                        "file": str(gentle_state),
                    })
        except Exception as e:
            bugs.append({
                "severity": "MEDIUM",
                "name": "gentle_watering_state_unreadable",
                "detail": str(e)[:200],
                "file": str(gentle_state),
            })
    else:
        bugs.append({
            "severity": "HIGH",
            "name": "missing_gentle_watering_state",
            "detail": "gentle_watering_state.json missing (cron may be broken)",
            "file": str(gentle_state),
        })

    # DB sensor freshness: if this is stale, history/progress panels will look dead.
    db_path = DATA_DIR / "grokmon.db"
    if db_path.exists():
        try:
            import sqlite3
            con = sqlite3.connect(str(db_path))
            cur = con.cursor()
            cur.execute("select max(timestamp) from sensor_readings")
            row = cur.fetchone()
            con.close()
            latest = (row[0] if row else None) or ""
            if latest:
                latest_dt = datetime.strptime(latest, "%Y-%m-%d %H:%M:%S")
                age_min = (datetime.now() - latest_dt).total_seconds() / 60.0
                if age_min > STALE_MINUTES:
                    bugs.append({
                        "severity": "MEDIUM",
                        "name": "stale_sensor_db",
                        "detail": f"sensor_readings latest is {age_min:.0f} min old ({latest})",
                        "file": str(db_path),
                    })
        except Exception as e:
            bugs.append({
                "severity": "MEDIUM",
                "name": "sensor_db_check_failed",
                "detail": str(e)[:200],
                "file": str(db_path),
            })

    # OpenClaw cron store health: detect persistent timeouts/errors.
    cron_path = PROJECT_ROOT / "openclaw-workspace" / "cron" / "cron.json"
    if cron_path.exists():
        try:
            obj = json.loads(cron_path.read_text())
            jobs = obj.get("jobs", [])
            bad = []
            for j in jobs:
                st = (j.get("state") or {})
                if st.get("lastStatus") == "error" and (st.get("consecutiveErrors") or 0) >= 3:
                    bad.append((j.get("name"), st.get("lastError", "")))
            if bad:
                bugs.append({
                    "severity": "HIGH",
                    "name": "openclaw_cron_errors",
                    "detail": f"{len(bad)} cron job(s) failing repeatedly (>=3): " + ", ".join(n for n,_ in bad[:3]),
                    "file": str(cron_path),
                })
        except Exception as e:
            bugs.append({
                "severity": "MEDIUM",
                "name": "openclaw_cron_unreadable",
                "detail": str(e)[:200],
                "file": str(cron_path),
            })

    # Cross-domain learnings JSON frequently truncates on crash; flag early.
    cross_domain = AGENT_DIR / "data" / "cross_domain_learnings.json"
    if cross_domain.exists():
        try:
            json.loads(cross_domain.read_text())
        except Exception as e:
            bugs.append({
                "severity": "HIGH",
                "name": "cross_domain_learnings_corrupt",
                "detail": str(e)[:200],
                "file": str(cross_domain),
            })

    return bugs


def check_memory() -> list[dict]:
    """Check memory usage of grokmon service."""
    bugs = []
    rc, out = run("systemctl --user show grokmon -p MemoryCurrent 2>/dev/null")
    if rc == 0 and "MemoryCurrent=" in out:
        try:
            mem_bytes = int(out.split("=")[1])
            mem_mb = mem_bytes / (1024 * 1024)
            if mem_mb > MEMORY_CRIT_MB:
                bugs.append({
                    "severity": "CRITICAL",
                    "name": "memory_critical",
                    "detail": f"Memory at {mem_mb:.0f}MB (limit ~1500MB)",
                })
            elif mem_mb > MEMORY_WARN_MB:
                bugs.append({
                    "severity": "MEDIUM",
                    "name": "memory_warning",
                    "detail": f"Memory at {mem_mb:.0f}MB, approaching limit",
                })
        except (ValueError, IndexError):
            pass

    return bugs


def check_recent_errors() -> list[dict]:
    """Grep journalctl for errors since last service start."""
    bugs = []
    # Use errors since service start (not fixed 1-hour window) to avoid false positives
    # after restarts that leave old errors in the window
    rc_ts, start_ts = run(
        "systemctl --user show grokmon -p ActiveEnterTimestamp --value 2>/dev/null"
    )
    if rc_ts == 0 and start_ts.strip():
        since = f"--since '{start_ts.strip()}'"
    else:
        since = "--since '1 hour ago'"
    rc, out = run(
        f"journalctl --user -u grokmon --no-pager {since} 2>/dev/null "
        "| grep -iE 'traceback|syntaxerror|importerror|connectionerror|memoryerror' "
        "| tail -5"
    )
    if out:
        lines = out.strip().split("\n")
        error_types = set()
        for line in lines:
            for etype in ["SyntaxError", "ImportError", "ConnectionError", "MemoryError", "Traceback"]:
                if etype.lower() in line.lower():
                    error_types.add(etype)

        if "SyntaxError" in error_types or "ImportError" in error_types:
            severity = "CRITICAL"
        elif "MemoryError" in error_types:
            severity = "HIGH"
        else:
            severity = "MEDIUM"

        bugs.append({
            "severity": severity,
            "name": "recent_errors",
            "detail": f"Errors in last hour: {', '.join(error_types)}. Sample: {lines[0][:150]}",
        })

    return bugs


def check_service_config() -> list[dict]:
    """Check systemd service file for common parsing issues."""
    bugs = []
    svc_path = Path.home() / ".config" / "systemd" / "user" / "grokmon.service"
    if not svc_path.exists():
        return bugs

    content = svc_path.read_text()
    # Check for inline comments on value lines (systemd can't parse these)
    problem_lines = []
    for i, line in enumerate(content.split("\n"), 1):
        stripped = line.strip()
        if "=" in stripped and not stripped.startswith("#") and not stripped.startswith("["):
            key_val = stripped.split("=", 1)
            if len(key_val) == 2 and "#" in key_val[1]:
                problem_lines.append(f"line {i}: {stripped[:60]}")

    if problem_lines:
        bugs.append({
            "severity": "HIGH",
            "name": "systemd_inline_comments",
            "detail": f"Inline comments break systemd parsing: {'; '.join(problem_lines[:3])}",
            "file": str(svc_path),
        })

    return bugs


def check_cloudflared() -> list[dict]:
    """Check cloudflared tunnels and auto-restart if down."""
    bugs = []

    # Check if any cloudflared process is running
    rc, procs = run("pgrep -a cloudflared 2>/dev/null", timeout=5)
    if rc != 0 or not procs.strip():
        bugs.append({
            "severity": "CRITICAL",
            "name": "cloudflared_not_running",
            "detail": "No cloudflared process found — tunnels are down",
        })
        # Attempt auto-restart
        rc2, out2 = run("sudo systemctl restart cloudflared 2>&1 || "
                        "systemctl --user restart cloudflared 2>&1 || "
                        "nohup cloudflared tunnel run ganjamonai >/dev/null 2>&1 &",
                        timeout=15)
        bugs.append({
            "severity": "LOW",
            "name": "cloudflared_restart_attempted",
            "detail": f"Auto-restart attempted (rc={rc2}): {out2[:120]}",
        })
        return bugs

    # Check main tunnel connectivity (ganjamonai → port 8000)
    rc, out = run("curl -sf --max-time 5 http://localhost:8000/api/admin/ping 2>/dev/null",
                  timeout=8)
    if rc != 0:
        bugs.append({
            "severity": "MEDIUM",
            "name": "hal_tunnel_origin_down",
            "detail": "HAL on :8000 not responding (tunnel origin may be unreachable)",
        })

    # Verify tunnel is actually connected to Cloudflare edge
    rc, connectors = run(
        "cloudflared tunnel info ganjamonai 2>&1 | grep -i 'connections\\|connector' | head -3",
        timeout=10)
    if rc != 0 or "0 connections" in connectors.lower():
        bugs.append({
            "severity": "HIGH",
            "name": "ganjamonai_tunnel_disconnected",
            "detail": f"ganjamonai tunnel has 0 edge connections: {connectors[:120]}",
        })

    return bugs


def check_disk() -> list[dict]:
    """Check disk usage."""
    bugs = []
    rc, out = run("df -h / | tail -1")
    if rc == 0:
        parts = out.split()
        for p in parts:
            if p.endswith("%"):
                pct = int(p.rstrip("%"))
                if pct > DISK_WARN_PCT:
                    bugs.append({
                        "severity": "MEDIUM",
                        "name": "disk_usage_high",
                        "detail": f"Disk usage at {pct}%",
                    })
                break

    return bugs


def main():
    """Run all health checks and write report."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    all_bugs = []
    checks = [
        ("subprocesses", check_subprocesses),
        ("imports", check_imports),
        ("api_health", check_api_health),
        ("data_freshness", check_data_freshness),
        ("memory", check_memory),
        ("recent_errors", check_recent_errors),
        ("service_config", check_service_config),
        ("disk", check_disk),
        ("cloudflared", check_cloudflared),
    ]

    for name, fn in checks:
        try:
            bugs = fn()
            all_bugs.extend(bugs)
        except Exception as e:
            all_bugs.append({
                "severity": "LOW",
                "name": f"check_failed_{name}",
                "detail": str(e)[:200],
            })

    # Determine overall status
    severities = [b["severity"] for b in all_bugs]
    if "CRITICAL" in severities:
        overall = "CRITICAL"
    elif "HIGH" in severities:
        overall = "DEGRADED"
    elif "MEDIUM" in severities:
        overall = "WARNING"
    else:
        overall = "HEALTHY"

    report = {
        "timestamp": datetime.now().isoformat(),
        "overall": overall,
        "bug_count": len(all_bugs),
        "critical": sum(1 for s in severities if s == "CRITICAL"),
        "high": sum(1 for s in severities if s == "HIGH"),
        "medium": sum(1 for s in severities if s == "MEDIUM"),
        "low": sum(1 for s in severities if s == "LOW"),
        "bugs": all_bugs,
    }

    REPORT_PATH.write_text(json.dumps(report, indent=2))

    # Console summary
    icon = {"HEALTHY": "OK", "WARNING": "WARN", "DEGRADED": "BAD", "CRITICAL": "CRIT"}
    print(f"[{icon.get(overall, '?')}] {overall} — "
          f"{report['critical']}C {report['high']}H {report['medium']}M {report['low']}L bugs")
    for bug in all_bugs:
        if bug["severity"] in ("CRITICAL", "HIGH"):
            print(f"  [{bug['severity']}] {bug['name']}: {bug['detail'][:120]}")

    if "--json" in sys.argv:
        print(json.dumps(report, indent=2))

    # Exit code: 2 for critical, 1 for high, 0 otherwise
    if report["critical"] > 0:
        sys.exit(2)
    elif report["high"] > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
