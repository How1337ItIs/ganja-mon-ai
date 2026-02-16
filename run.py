#!/usr/bin/env python3
"""
Grok & Mon - Main Entry Point
=============================

Run the complete Grok & Mon system:
- Web server (FastAPI) - Hardware Abstraction Layer (HAL)
- OpenClaw gateway - Primary AI orchestrator (heartbeat-driven)
- Trading agent - GanjaMonAgent isolated subprocess

Legacy modes (kept for fallback):
- Orchestrator (sensor polling + AI decisions) - replaced by OpenClaw heartbeat
- Social daemon - replaced by OpenClaw skills
- Research daemon - replaced by OpenClaw blogwatcher + summarize skills

Usage:
    python run.py server       # Run just the web server (HAL)
    python run.py openclaw     # Run just the OpenClaw gateway
    python run.py orchestrator # Run just the orchestrator (legacy fallback)
    python run.py all          # Run everything: HAL + OpenClaw + Trading (default)
    python run.py legacy       # Run legacy mode: HAL + Orchestrator + Social + Trading
"""

import sys
import asyncio
import subprocess
import signal
import os
import time
import urllib.request
import urllib.error
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

# Configure structured logging
from src.core.logging_config import setup_logging
setup_logging()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


def run_server():
    """Run the FastAPI server"""
    import uvicorn
    from src.api import app

    uvicorn.run(app, host="0.0.0.0", port=8000)


async def run_orchestrator():
    """Run the main orchestrator loop with smart resilience"""
    # Import resilient version (patches base orchestrator)
    try:
        from src.orchestrator.resilient import ResilientOrchestrator as GrokMonOrchestrator
        print("[*] Using resilient orchestrator (smart error handling)")
    except ImportError:
        from src.orchestrator.orchestrator import GrokMonOrchestrator
        print("[*] Using base orchestrator (no resilience enhancements)")

    orchestrator = GrokMonOrchestrator(
        sensor_interval_seconds=120,   # 2 minutes (less load)
        ai_interval_seconds=1800,      # 30 minutes
        plant_name="Mon"
    )

    try:
        await orchestrator.start()
    except KeyboardInterrupt:
        print("\n[*] Keyboard interrupt - shutting down...")
        await orchestrator.stop()
    except Exception as e:
        print(f"[ERR] Fatal orchestrator error: {e}")
        await orchestrator.stop()
        raise  # Let systemd restart us


async def run_social():
    """Run the social engagement daemon"""
    from src.social.engagement_daemon import get_engagement_daemon
    daemon = get_engagement_daemon()
    try:
        await daemon.run()
    except KeyboardInterrupt:
        daemon.stop()

async def run_research():
    """Run the pirate intelligence daemon"""
    from src.research.pirate import get_pirate_daemon
    daemon = get_pirate_daemon()
    try:
        await daemon.run()
    except KeyboardInterrupt:
        daemon.stop()



def _run_trading_agent():
    """Run GanjaMonAgent in subprocess with isolated PYTHONPATH"""
    import traceback
    import shutil
    from src.core.paths import AGENT_DIR
    agent_dir = AGENT_DIR
    if not agent_dir.exists():
        print("[WARN] Trading agent directory not found, skipping")
        return

    # If the legacy systemd unit is active, it will fight `run.py all` and cause PID-lock loops.
    # Intended architecture (per docs): trading runs as a subprocess of grokmon.
    try:
        systemctl = shutil.which("systemctl")
        if systemctl:
            r = subprocess.run(
                [systemctl, "--user", "is-active", "ganjamon-agent.service"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
            )
            if r.stdout.strip() == "active":
                print("[WARN] ganjamon-agent.service is active; stopping it to avoid conflicts with run.py all")
                subprocess.run([systemctl, "--user", "stop", "ganjamon-agent.service"], check=False)
    except Exception as e:
        print(f"[WARN] Could not check/stop ganjamon-agent.service: {e}")

    env = os.environ.copy()
    # Ensure user-global npm bins (clawhub, etc.) are visible to the gateway process.
    # systemd user services often start with a minimal PATH that omits ~/.npm-global/bin.
    try:
        npm_bin = Path.home() / ".npm-global" / "bin"
        if npm_bin.exists():
            env["PATH"] = f"{npm_bin}{os.pathsep}{env.get('PATH', '')}"
    except Exception:
        pass
    env["PYTHONPATH"] = str(agent_dir / "src")

    # Run the agent as a child process and ensure it is terminated on SIGTERM/SIGINT.
    # Without this, systemd restarts can leave orphaned trading processes behind.
    child = None

    def _term_child(signum, frame):
        nonlocal child
        try:
            if child and child.poll() is None:
                child.terminate()
        except Exception:
            pass

    try:
        signal.signal(signal.SIGTERM, _term_child)
        signal.signal(signal.SIGINT, _term_child)
    except Exception:
        pass

    try:
        child = subprocess.Popen(
            [sys.executable, "-m", "main"],
            cwd=str(agent_dir),
            env=env,
        )
        child.wait()
    except Exception as e:
        print(f"[ERR] Trading agent crashed: {e}")
        traceback.print_exc()
    finally:
        try:
            if child and child.poll() is None:
                child.terminate()
                child.wait(timeout=5)
        except Exception:
            try:
                if child and child.poll() is None:
                    child.kill()
            except Exception:
                pass


def _run_openclaw_gateway():
    """Run OpenClaw gateway as primary AI orchestrator"""
    import traceback
    import shutil
    import re

    # Deprioritize OpenClaw vs. networking/SSH and the HAL server. This helps keep the
    # Chromebook reachable under load without impacting correctness.
    try:
        import os as _os
        nice = int(_os.getenv("OPENCLAW_NICE", "10"))
        if nice:
            _os.nice(nice)
    except Exception:
        pass

    # Some OpenClaw workspace skills expect chain env vars (PRIVATE_KEY, MONAD_RPC_URL, etc.)
    # which currently live in the trading agent's isolated env file. Load them here so the
    # OpenClaw gateway can use the same creds without duplicating secrets into the root .env.
    try:
        agent_env = Path(__file__).parent / "agents" / "ganjamon" / ".env"
        if agent_env.exists():
            load_dotenv(agent_env, override=False)
    except Exception:
        pass

    config_path = Path(__file__).parent / "openclaw-workspace" / "config" / "openclaw.json"
    openclaw_bin = shutil.which("openclaw")
    if not openclaw_bin:
        print("[WARN] OpenClaw not installed (npm install -g openclaw), falling back to legacy orchestrator")
        asyncio.run(run_orchestrator())
        return
    if not config_path.exists():
        print(f"[WARN] OpenClaw config not found at {config_path}, falling back to legacy orchestrator")
        asyncio.run(run_orchestrator())
        return

    # OpenClaw skill gating checks for required binaries on PATH. The gateway often runs under
    # systemd with a minimal PATH; ensure `clawhub` is reachable via the venv bin dir (already on PATH).
    try:
        venv_bin = Path(__file__).parent / "venv" / "bin"
        venv_bin.mkdir(parents=True, exist_ok=True)
        wrapper = venv_bin / "clawhub"
        real = Path.home() / ".npm-global" / "bin" / "clawhub"
        if not wrapper.exists() and real.exists():
            wrapper.write_text(
                "#!/usr/bin/env bash\n"
                "exec \"" + str(real) + "\" \"$@\"\n",
                encoding="utf-8",
            )
            wrapper.chmod(0o755)
    except Exception:
        pass

    def _http_status(url: str, timeout_s: float = 2.0) -> int:
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=timeout_s) as resp:
                return int(getattr(resp, "status", 200))
        except urllib.error.HTTPError as e:
            return int(getattr(e, "code", 0) or 0)
        except Exception:
            return 0

    def _openclaw_ok() -> bool:
        # Canvas is a stable "is the gateway actually responding?" check.
        return _http_status("http://127.0.0.1:18789/__openclaw__/canvas/") == 200

    def _find_listener_pid(port: int) -> int | None:
        """Return PID listening on TCP port, if visible via `ss -ltnp`."""
        try:
            out = subprocess.check_output(["ss", "-ltnp"], text=True, stderr=subprocess.DEVNULL)
        except Exception:
            return None
        needle = f":{port} "
        for line in out.splitlines():
            if needle not in line:
                continue
            # Example: users:(("openclaw-gatewa",pid=82279,fd=21))
            m = re.search(r"pid=(\d+)", line)
            if m:
                try:
                    return int(m.group(1))
                except Exception:
                    return None
        return None

    def _stop_openclaw_gateway_best_effort():
        """
        OpenClaw sometimes leaves an orphan `openclaw-gateway` behind across restarts,
        which causes `openclaw gateway run` to fail with a lock timeout. Prefer a clean
        `openclaw gateway stop`, then fall back to killing the port listener.
        """
        def _pid_alive(pid: int) -> bool:
            try:
                os.kill(pid, 0)
                return True
            except Exception:
                return False

        def _clear_tmp_locks():
            """
            OpenClaw uses a JSON lock file under /tmp/openclaw-<uid>/gateway.*.lock.
            If a gateway dies uncleanly, the lock can stick around and block restarts.
            """
            try:
                lock_dir = Path("/tmp") / f"openclaw-{os.getuid()}"
                if not lock_dir.exists():
                    return
                for p in lock_dir.glob("gateway.*.lock"):
                    try:
                        raw = p.read_text(encoding="utf-8", errors="replace").strip()
                        pid = None
                        if raw.startswith("{") and raw.endswith("}"):
                            import json as _json

                            pid = int(_json.loads(raw).get("pid") or 0) or None
                        if pid and _pid_alive(pid):
                            # Still owned by a live process; don't remove here.
                            continue
                    except Exception:
                        # If we can't parse it, it's safer to delete it after a stop attempt.
                        pass
                    try:
                        p.unlink(missing_ok=True)
                    except Exception:
                        pass
            except Exception:
                pass

        try:
            subprocess.run(
                [openclaw_bin, "gateway", "stop"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=10,
            )
        except Exception:
            pass

        pid = _find_listener_pid(18789)
        if not pid:
            # No listener, but a stale lock file can still block a new gateway.
            _clear_tmp_locks()
            return
        try:
            os.kill(pid, signal.SIGTERM)
        except Exception:
            _clear_tmp_locks()
            return
        # Give it a moment to exit; if it doesn't, hard-kill.
        for _ in range(10):
            time.sleep(0.3)
            if _find_listener_pid(18789) != pid:
                _clear_tmp_locks()
                return
        try:
            os.kill(pid, signal.SIGKILL)
        except Exception:
            pass
        _clear_tmp_locks()

    # OpenClaw reads config from ~/.openclaw/openclaw.json (no --config CLI flag)
    home_config = Path.home() / ".openclaw" / "openclaw.json"
    home_config.parent.mkdir(parents=True, exist_ok=True)

    gateway_child = None

    def _term_gateway(signum, frame):
        nonlocal gateway_child
        try:
            if gateway_child and gateway_child.poll() is None:
                gateway_child.terminate()
        except Exception:
            pass

    try:
        signal.signal(signal.SIGTERM, _term_gateway)
        signal.signal(signal.SIGINT, _term_gateway)
    except Exception:
        pass

    # If a gateway is already running (e.g., after a partial restart), do NOT overwrite config:
    # touching ~/.openclaw/openclaw.json triggers a gateway reload/restart loop.
    if _openclaw_ok():
        print("[*] OpenClaw gateway already responding on :18789; entering monitor loop (no restart)")
        while True:
            time.sleep(30)
            if not _openclaw_ok():
                print("[WARN] OpenClaw gateway no longer responding; attempting restart")
                break
    else:
        # If something is still bound to 18789 but not responding, stop it first to avoid
        # lock-timeout flapping on restarts.
        if _find_listener_pid(18789):
            print("[WARN] OpenClaw port 18789 is already bound but canvas is not responding; stopping stale gateway")
            _stop_openclaw_gateway_best_effort()

    def _files_differ(a: Path, b: Path) -> bool:
        try:
            if not a.exists() or not b.exists():
                return True
            return a.read_bytes() != b.read_bytes()
        except Exception:
            return True

    def _backup(path: Path, label: str) -> Path | None:
        try:
            if not path.exists():
                return None
            backup_dir = home_config.parent / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            ts = time.strftime("%Y%m%d_%H%M%S")
            out = backup_dir / f"{path.name}.{label}.{ts}.bak"
            shutil.copy2(str(path), str(out))
            return out
        except Exception:
            return None

    # Only sync once we're about to start (or restart) the gateway.
    # IMPORTANT: avoid destructive one-way overwrite. Previous behavior copied
    # workspace -> home unconditionally, which could silently erase hotfixes made
    # directly in ~/.openclaw/openclaw.json.
    try:
        sync_mode = os.getenv("OPENCLAW_CONFIG_SYNC_MODE", "prefer_newer").strip().lower()
        allowed_modes = {"prefer_newer", "prefer_workspace", "prefer_home", "none"}
        if sync_mode not in allowed_modes:
            print(
                f"[WARN] Unknown OPENCLAW_CONFIG_SYNC_MODE={sync_mode!r}; "
                "using 'prefer_newer'"
            )
            sync_mode = "prefer_newer"

        if not home_config.exists():
            shutil.copy2(str(config_path), str(home_config))
            print(f"[*] OpenClaw config initialized at {home_config} from workspace")
        elif sync_mode == "none":
            print("[*] OpenClaw config sync disabled (OPENCLAW_CONFIG_SYNC_MODE=none)")
        elif sync_mode == "prefer_workspace":
            if _files_differ(config_path, home_config):
                b = _backup(home_config, "pre_workspace_sync")
                shutil.copy2(str(config_path), str(home_config))
                print(
                    f"[*] OpenClaw config synced workspace -> home "
                    f"(backup={b if b else 'none'})"
                )
            else:
                print("[*] OpenClaw config already in sync (workspace/home)")
        elif sync_mode == "prefer_home":
            if _files_differ(config_path, home_config):
                b = _backup(config_path, "pre_home_sync")
                shutil.copy2(str(home_config), str(config_path))
                print(
                    f"[*] OpenClaw config synced home -> workspace "
                    f"(backup={b if b else 'none'})"
                )
            else:
                print("[*] OpenClaw config already in sync (workspace/home)")
        else:
            # prefer_newer (default): preserve latest edit from either side.
            w_mtime = config_path.stat().st_mtime
            h_mtime = home_config.stat().st_mtime
            if not _files_differ(config_path, home_config):
                print("[*] OpenClaw config already in sync (workspace/home)")
            elif h_mtime > w_mtime + 1:
                b = _backup(config_path, "pre_newer_home_sync")
                shutil.copy2(str(home_config), str(config_path))
                print(
                    f"[*] OpenClaw config prefers NEWER home copy -> workspace "
                    f"(backup={b if b else 'none'})"
                )
            elif w_mtime > h_mtime + 1:
                b = _backup(home_config, "pre_newer_workspace_sync")
                shutil.copy2(str(config_path), str(home_config))
                print(
                    f"[*] OpenClaw config prefers NEWER workspace copy -> home "
                    f"(backup={b if b else 'none'})"
                )
            else:
                # Near-simultaneous writes: keep home as runtime source of truth.
                b = _backup(config_path, "pre_tie_break_home_sync")
                shutil.copy2(str(home_config), str(config_path))
                print(
                    f"[*] OpenClaw config tie-break -> home copy preserved "
                    f"(backup={b if b else 'none'})"
                )
    except Exception as e:
        print(f"[WARN] Could not sync OpenClaw config safely: {e}")

    # Ensure required workspace directories exist
    workspace_dir = config_path.parent.parent
    for subdir in ["logs", "ganjamon/memory", "cron"]:
        (workspace_dir / subdir).mkdir(parents=True, exist_ok=True)

    # OpenClaw will run "missed jobs after restart" during cron init. In practice, if the
    # gateway was down for a while, or if multiple jobs are scheduled to fire shortly after
    # startup, immediately running long isolated-agent runs can wedge the gateway (canvas
    # becomes unresponsive and health checks go green via TCP-only probes).
    #
    # Strategy:
    # - Always clear stale running markers.
    # - Avoid "catch up all missed jobs now": if a job is overdue, advance it to the
    #   *next scheduled cron time* instead of pushing everything to "soon".
    # - Exception: schedule the Grow Decision Cycle soon after restart so plant ops
    #   regains awareness quickly without starting every other heavy job immediately.
    try:
        import json as _json
        from datetime import datetime, timedelta
        from zoneinfo import ZoneInfo

        cron_store = workspace_dir / "cron" / "cron.json"
        if cron_store.exists():
            data = _json.loads(cron_store.read_text(encoding="utf-8"))
            jobs = data.get("jobs")
            if isinstance(jobs, list):
                now_ms = int(time.time() * 1000)

                def _parse_hour_field(field: str) -> list[int] | None:
                    field = (field or "").strip()
                    if field == "*":
                        return list(range(24))
                    if field.startswith("*/"):
                        try:
                            step = int(field.split("/", 1)[1])
                            if step <= 0:
                                return None
                            return list(range(0, 24, step))
                        except Exception:
                            return None
                    if "," in field:
                        out: list[int] = []
                        for part in field.split(","):
                            part = part.strip()
                            if not part:
                                continue
                            try:
                                v = int(part)
                            except Exception:
                                return None
                            if v < 0 or v > 23:
                                return None
                            out.append(v)
                        return sorted(set(out))
                    try:
                        v = int(field)
                    except Exception:
                        return None
                    if v < 0 or v > 23:
                        return None
                    return [v]

                def _parse_dow_field(field: str) -> set[int] | None:
                    field = (field or "").strip()
                    if field == "*":
                        return None
                    try:
                        v = int(field)
                    except Exception:
                        return None
                    # Cron: 0/7=Sun, 1=Mon ... 6=Sat
                    if v == 7:
                        v = 0
                    if v < 0 or v > 6:
                        return None
                    return {v}

                def _next_cron_ms(expr: str, tz_name: str) -> int | None:
                    try:
                        fields = (expr or "").split()
                        if len(fields) != 5:
                            return None
                        minute_s, hour_s, dom, month, dow_s = fields
                        if dom != "*" or month != "*":
                            return None
                        minute = int(minute_s)
                        if minute < 0 or minute > 59:
                            return None
                        hours = _parse_hour_field(hour_s)
                        if not hours:
                            return None
                        dow_allowed = _parse_dow_field(dow_s)
                        tz = ZoneInfo(tz_name or "America/Los_Angeles")
                        now_dt = datetime.fromtimestamp(now_ms / 1000.0, tz=tz)
                        now_floor = now_dt.replace(second=0, microsecond=0)

                        # Search up to ~2 weeks (covers weekly jobs).
                        for day_off in range(0, 15):
                            day = (now_floor + timedelta(days=day_off)).date()
                            for h in hours:
                                cand = datetime(day.year, day.month, day.day, h, minute, tzinfo=tz)
                                if cand <= now_floor:
                                    continue
                                # datetime.weekday(): Mon=0 ... Sun=6; cron uses Sun=0.
                                cand_cron_dow = (cand.weekday() + 1) % 7
                                if dow_allowed is not None and cand_cron_dow not in dow_allowed:
                                    continue
                                return int(cand.timestamp() * 1000)
                    except Exception:
                        return None
                    return None

                # How soon to run Grow Decision after restart (ms). Keep small so plant ops
                # regains awareness quickly, but avoid the thundering herd.
                try:
                    grow_soon_ms = int(os.getenv("OPENCLAW_GROW_STARTUP_SOON_MS", "150000"))
                except Exception:
                    grow_soon_ms = 150000

                changed = False
                for job in jobs:
                    job_id = str(job.get("id") or "")
                    st = job.get("state")
                    if not isinstance(st, dict):
                        st = {}
                        job["state"] = st
                        changed = True
                    # Always clear stale running markers (OpenClaw also does this, but
                    # we want the on-disk state clean even if the gateway crashes early).
                    if isinstance(st.get("runningAtMs"), (int, float)):
                        st.pop("runningAtMs", None)
                        changed = True
                    next_ms = st.get("nextRunAtMs")

                    # If nextRunAtMs is missing or overdue, advance to the next cron time
                    # instead of trying to run the backlog immediately.
                    if (not isinstance(next_ms, (int, float))) or int(next_ms) <= now_ms:
                        sched = job.get("schedule") or {}
                        expr = (sched.get("expr") or "").strip()
                        tz_name = (sched.get("tz") or "America/Los_Angeles").strip()
                        nxt = _next_cron_ms(expr, tz_name)
                        if nxt is not None:
                            st["nextRunAtMs"] = int(nxt)
                            changed = True

                    # Plant ops: if Grow Decision is stale, schedule it soon after restart.
                    if (job.get("name") or "") == "Grow Decision Cycle":
                        last = st.get("lastRunAtMs")
                        stale = (not isinstance(last, (int, float))) or (now_ms - int(last) > (20 * 60 * 1000))
                        if stale:
                            desired = now_ms + max(30_000, int(grow_soon_ms))
                            cur = st.get("nextRunAtMs")
                            if not isinstance(cur, (int, float)) or int(cur) > desired:
                                st["nextRunAtMs"] = int(desired)
                                changed = True

                if changed:
                    try:
                        ts = time.strftime("%Y%m%d_%H%M%S")
                        cron_store_backup = cron_store.with_suffix(cron_store.suffix + f".bak.{ts}")
                        shutil.copy2(str(cron_store), str(cron_store_backup))
                    except Exception:
                        pass
                    cron_store.write_text(_json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                    print("[*] OpenClaw cron store sanitized (cleared running markers; advanced overdue nextRunAtMs to next cron; grow decision may run soon)")
    except Exception as e:
        print(f"[WARN] OpenClaw cron store sanitize failed: {e}")

    env = os.environ.copy()
    # Ensure venv shims (clawhub wrapper, gemini/summarize/blogwatcher, etc.) are available.
    try:
        venv_bin = Path(__file__).parent / "venv" / "bin"
        env["PATH"] = f"{venv_bin}{os.pathsep}{env.get('PATH', '')}"
    except Exception:
        pass
    try:
        print("[*] Starting OpenClaw gateway (port 18789, bind loopback)")
        # Ensure we don't hit OpenClaw's lock-timeout path if a previous gateway lingered.
        _stop_openclaw_gateway_best_effort()
        gateway_child = subprocess.Popen(
            # Avoid `--force`: it can create multiple concurrent gateways and cause mDNS/canvas flapping.
            [openclaw_bin, "gateway", "run", "--bind", "loopback", "--port", "18789"],
            cwd=str(workspace_dir),
            env=env,
        )
        gateway_child.wait()
    except Exception as e:
        print(f"[ERR] OpenClaw gateway crashed: {e}")
        traceback.print_exc()
        print("[*] Falling back to legacy orchestrator...")
        asyncio.run(run_orchestrator())
    finally:
        try:
            if gateway_child and gateway_child.poll() is None:
                gateway_child.terminate()
                gateway_child.wait(timeout=5)
        except Exception:
            try:
                if gateway_child and gateway_child.poll() is None:
                    gateway_child.kill()
            except Exception:
                pass

def run_openclaw():
    """Run just the OpenClaw gateway"""
    _run_openclaw_gateway()


def run_all():
    """Run HAL server + OpenClaw gateway + Trading agent (3 subprocesses)"""
    # Social posting, research, and all scheduled activities run through OpenClaw
    # cron jobs — NOT as Python daemons. See scripts/setup_openclaw_crons.sh.
    import multiprocessing
    import threading
    import json
    import urllib.request
    import socket
    from datetime import datetime

    def _start_trading():
        p = multiprocessing.Process(target=_run_trading_agent, name="trading")
        p.start()
        return p

    def _start_openclaw():
        p = multiprocessing.Process(target=_run_openclaw_gateway, name="openclaw")
        p.start()
        return p

    try:
        openclaw_health_timeout_s = float(os.getenv("OPENCLAW_HEALTH_TIMEOUT_SECONDS", "5.5"))
    except Exception:
        openclaw_health_timeout_s = 5.5
    try:
        openclaw_health_probe_retries = int(os.getenv("OPENCLAW_HEALTH_PROBE_RETRIES", "2"))
    except Exception:
        openclaw_health_probe_retries = 2

    def _openclaw_health_ok():
        """Best-effort readiness check for OpenClaw gateway."""
        retries = max(1, openclaw_health_probe_retries)
        for attempt in range(retries):
            try:
                # Use GET and read a small amount to ensure the handler isn't wedged.
                req = urllib.request.Request("http://127.0.0.1:18789/__openclaw__/canvas/", method="GET")
                with urllib.request.urlopen(req, timeout=openclaw_health_timeout_s) as resp:
                    _ = resp.read(1)
                    if int(getattr(resp, "status", 200)) == 200:
                        return True
            except Exception:
                pass
            if attempt + 1 < retries:
                time.sleep(0.8)
        return False

    # Start all subprocesses. On the Chromebook, OpenClaw and other UI/streaming workloads
    # can saturate CPU during boot and make SSH/tunnels unreliable. Start HAL + trading
    # first, then delay OpenClaw so the machine stays reachable.
    openclaw_delay_s = 0
    try:
        openclaw_delay_s = int(os.getenv("OPENCLAW_START_DELAY_SECONDS", "60"))
    except Exception:
        openclaw_delay_s = 60

    server_proc = multiprocessing.Process(target=run_server, name="server")
    server_proc.start()
    trading_proc = _start_trading()
    if openclaw_delay_s > 0:
        print(f"[*] Delaying OpenClaw startup by {openclaw_delay_s}s (OPENCLAW_START_DELAY_SECONDS)")
        time.sleep(openclaw_delay_s)
    openclaw_proc = _start_openclaw()
    openclaw_started_at = time.time()
    try:
        # OpenClaw can take multiple minutes to become fully responsive on the Chromebook,
        # especially right after restarts or during heavy skill pack loading.
        openclaw_health_grace_s = int(os.getenv("OPENCLAW_HEALTH_GRACE_SECONDS", "360"))
    except Exception:
        openclaw_health_grace_s = 300
    try:
        openclaw_unhealthy_restart_threshold = int(
            os.getenv("OPENCLAW_UNHEALTHY_RESTART_THRESHOLD", "6")
        )
    except Exception:
        openclaw_unhealthy_restart_threshold = 3
    openclaw_unhealthy_count = 0

    print("[*] HAL server started on http://localhost:8000 (FastAPI)")
    print("[*] OpenClaw gateway started on http://localhost:18789 (primary orchestrator)")
    print("[*] Trading agent started (GanjaMonAgent)")
    print("[*] Social/research/scheduling handled by OpenClaw cron jobs")

    # --- Crash watchdog: respawn openclaw/trading if they die ---
    _shutdown = threading.Event()

    def _watchdog():
        nonlocal openclaw_proc, trading_proc, openclaw_started_at, openclaw_unhealthy_count
        try:
            watchdog_interval_s = int(os.getenv("PROC_WATCHDOG_INTERVAL_SECONDS", "20"))
        except Exception:
            watchdog_interval_s = 20
        while not _shutdown.is_set():
            _shutdown.wait(max(10, watchdog_interval_s))
            if _shutdown.is_set():
                break

            if not openclaw_proc.is_alive():
                print("[WARN] OpenClaw gateway died; respawning...")
                openclaw_proc = _start_openclaw()
                openclaw_started_at = time.time()
                openclaw_unhealthy_count = 0
            else:
                # Process liveness is not enough: ensure the gateway is actually reachable.
                uptime_s = time.time() - openclaw_started_at
                if uptime_s >= openclaw_health_grace_s:
                    if _openclaw_health_ok():
                        if openclaw_unhealthy_count > 0:
                            print("[*] OpenClaw gateway health recovered")
                        openclaw_unhealthy_count = 0
                    else:
                        openclaw_unhealthy_count += 1
                        print(
                            "[WARN] OpenClaw process alive but unhealthy "
                            f"(canvas not responding on :18789), count={openclaw_unhealthy_count}/"
                            f"{openclaw_unhealthy_restart_threshold}"
                        )
                        if openclaw_unhealthy_count >= openclaw_unhealthy_restart_threshold:
                            print("[WARN] Restarting unhealthy OpenClaw subprocess...")
                            try:
                                openclaw_proc.terminate()
                                openclaw_proc.join(timeout=10)
                            except Exception:
                                pass
                            try:
                                if openclaw_proc.is_alive() and hasattr(openclaw_proc, "kill"):
                                    openclaw_proc.kill()
                                    openclaw_proc.join(timeout=5)
                            except Exception:
                                pass
                            openclaw_proc = _start_openclaw()
                            openclaw_started_at = time.time()
                            openclaw_unhealthy_count = 0

            if not trading_proc.is_alive():
                print("[WARN] Trading agent died; respawning...")
                trading_proc = _start_trading()

    watchdog_thread = threading.Thread(target=_watchdog, daemon=True, name="proc-watchdog")
    watchdog_thread.start()

    # --- Mirror: deterministic sensor snapshot into OpenClaw memory (do not rely on LLM compliance) ---
    #
    # OpenClaw is intended to write `memory/YYYY-MM-DD.md` every heartbeat, but in practice
    # heartbeat runs can be "HEARTBEAT_OK"-only and skip file writes depending on tool policy
    # and provider behavior. This mirror keeps the daily log alive without requiring model/tool calls.
    #
    # Idempotence: if the memory file was updated recently, skip to avoid duplicates.
    def _openclaw_memory_mirror_loop():
        mem_dir = Path(__file__).parent / "openclaw-workspace" / "ganjamon" / "memory"
        mem_dir.mkdir(parents=True, exist_ok=True)

        def _append_lineblock(text: str):
            # Best-effort append; never crash the main supervisor.
            with open(text_path, "a", encoding="utf-8") as f:
                f.write(text)

        while not _shutdown.is_set():
            try:
                now = datetime.now()
                text_path = mem_dir / f"{now:%Y-%m-%d}.md"

                # Skip if someone (OpenClaw or an operator) updated the file recently.
                try:
                    mtime = text_path.stat().st_mtime
                    if (time.time() - mtime) < (25 * 60):
                        _shutdown.wait(60)
                        continue
                except FileNotFoundError:
                    pass

                req = urllib.request.Request("http://127.0.0.1:8000/api/sensors", method="GET")
                with urllib.request.urlopen(req, timeout=3.0) as resp:
                    raw = resp.read().decode("utf-8", errors="replace")
                data = json.loads(raw)

                block = (
                    f"\n\n## {now:%H:%M} — Heartbeat (Mirror)\n"
                    f"- Temperature: {data.get('air_temp')}°C\n"
                    f"- Humidity: {data.get('humidity')}%\n"
                    f"- VPD: {data.get('vpd')} kPa\n"
                    f"- Soil Moisture: {data.get('soil_moisture')}%\n"
                    f"- CO2: {data.get('co2')} ppm\n"
                )
                _append_lineblock(block)
            except Exception as e:
                try:
                    now = datetime.now()
                    text_path = mem_dir / f"{now:%Y-%m-%d}.md"
                    block = f"\n\n## {now:%H:%M} — Heartbeat (Mirror)\n- Error: {e}\n"
                    with open(text_path, "a", encoding="utf-8") as f:
                        f.write(block)
                except Exception:
                    pass

            # Run roughly every 30 minutes; wake early on shutdown.
            _shutdown.wait(30 * 60)

    mirror_thread = threading.Thread(
        target=_openclaw_memory_mirror_loop,
        daemon=True,
        name="openclaw-memory-mirror",
    )
    mirror_thread.start()

    # --- Bridge: OpenClaw self-improvement -> trading agent upgrade_requests.json ---
    #
    # OpenClaw cron/self-improvement tends to produce plans in OpenClaw memory, but the legacy
    # Ralph pipeline expects structured requests in `cloned-repos/ganjamon-agent/data/upgrade_requests.json`.
    # This bridge ingests `UPGRADE_REQUEST_JSON: {...}` lines from memory/YYYY-MM-DD.md and uses
    # UpgradeSystem to create/dedupe requests.
    def _openclaw_upgrade_bridge_loop():
        try:
            from src.learning.openclaw_upgrade_bridge import default_config, run_loop
            cfg = default_config(Path(__file__).parent)
            cfg.memory_dir.mkdir(parents=True, exist_ok=True)
            cfg.ganjamon_data_dir.mkdir(parents=True, exist_ok=True)
            run_loop(cfg, _shutdown)
        except Exception:
            # Never crash the supervisor for a self-improvement helper.
            return

    upgrade_bridge_thread = threading.Thread(
        target=_openclaw_upgrade_bridge_loop,
        daemon=True,
        name="openclaw-upgrade-bridge",
    )
    upgrade_bridge_thread.start()

    # --- Helper: keep outbound A2A outreach alive in OpenClaw mode ---
    #
    # The legacy orchestrator starts the outbound A2A daemon, but `run.py all`
    # intentionally does not run that orchestrator loop. Start the daemon here
    # so A2A interactions/reliability stay fresh while OpenClaw is primary.
    def _openclaw_a2a_outbound_loop():
        loop = None
        daemon = None
        try:
            from src.a2a.outbound_daemon import get_outbound_daemon
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def _runner():
                nonlocal daemon
                daemon = get_outbound_daemon()
                await daemon.start()
                print("[*] A2A outbound daemon started (OpenClaw mode helper)")
                while not _shutdown.is_set():
                    await asyncio.sleep(2)

            loop.run_until_complete(_runner())
        except Exception as e:
            print(f"[WARN] A2A outbound helper unavailable: {e}")
        finally:
            if loop is not None and daemon is not None:
                try:
                    loop.run_until_complete(daemon.stop())
                except Exception:
                    pass
            if loop is not None:
                try:
                    loop.close()
                except Exception:
                    pass

    a2a_outbound_enabled = str(os.getenv("A2A_OUTBOUND_ENABLED", "true")).strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    if a2a_outbound_enabled:
        a2a_outbound_thread = threading.Thread(
            target=_openclaw_a2a_outbound_loop,
            daemon=True,
            name="openclaw-a2a-outbound",
        )
        a2a_outbound_thread.start()

    _stop = threading.Event()

    def _request_stop(signum, frame):
        _stop.set()

    try:
        signal.signal(signal.SIGTERM, _request_stop)
        signal.signal(signal.SIGINT, _request_stop)
    except Exception:
        pass

    # Main process waits for stop request (SIGTERM/SIGINT) or server proc exit.
    try:
        while not _stop.is_set():
            if not server_proc.is_alive():
                break
            time.sleep(1)
    finally:
        _shutdown.set()
        for proc in [trading_proc, openclaw_proc, server_proc]:
            try:
                proc.terminate()
            except Exception:
                pass
        for proc in [trading_proc, openclaw_proc, server_proc]:
            try:
                proc.join(timeout=10)
            except Exception:
                pass
        for proc in [trading_proc, openclaw_proc, server_proc]:
            try:
                if proc.is_alive() and hasattr(proc, "kill"):
                    proc.kill()
            except Exception:
                pass
        for proc in [trading_proc, openclaw_proc, server_proc]:
            try:
                proc.join(timeout=5)
            except Exception:
                pass


def run_legacy():
    """Run legacy mode: HAL + Orchestrator + Social + Trading (pre-OpenClaw)"""
    import multiprocessing
    import threading

    def _run_social_logged():
        import traceback
        try:
            asyncio.run(run_social())
        except Exception as e:
            print(f"[ERR] Social daemon crashed: {e}")
            traceback.print_exc()

    def _run_research_logged():
        import traceback
        try:
            asyncio.run(run_research())
        except Exception as e:
            print(f"[ERR] Pirate daemon crashed: {e}")
            traceback.print_exc()

    def _start_social():
        p = multiprocessing.Process(target=_run_social_logged, name="social")
        p.start()
        return p

    def _start_trading():
        p = multiprocessing.Process(target=_run_trading_agent, name="trading")
        p.start()
        return p

    def _start_research():
        p = multiprocessing.Process(target=_run_research_logged, name="research")
        p.start()
        return p

    # Start all subprocesses
    server_proc = multiprocessing.Process(target=run_server, name="server")
    server_proc.start()
    social_proc = _start_social()
    trading_proc = _start_trading()
    research_proc = _start_research()

    print("[*] [LEGACY MODE] Web server started on http://localhost:8000")
    print("[*] [LEGACY MODE] Social engagement daemon started")
    print("[*] [LEGACY MODE] Trading agent started (GanjaMonAgent)")
    print("[*] [LEGACY MODE] Pirate intelligence daemon started")

    _shutdown = threading.Event()

    def _watchdog():
        nonlocal social_proc, trading_proc, research_proc
        while not _shutdown.is_set():
            _shutdown.wait(30)
            if _shutdown.is_set():
                break
            if not social_proc.is_alive():
                print("[WARN] Social daemon died — respawning...")
                social_proc = _start_social()
            if not trading_proc.is_alive():
                print("[WARN] Trading agent died — respawning...")
                trading_proc = _start_trading()
            if not research_proc.is_alive():
                print("[WARN] Pirate daemon died — respawning...")
                research_proc = _start_research()

    watchdog_thread = threading.Thread(target=_watchdog, daemon=True, name="proc-watchdog")
    watchdog_thread.start()

    # Run orchestrator in main process
    try:
        asyncio.run(run_orchestrator())
    finally:
        _shutdown.set()
        for proc in [research_proc, trading_proc, social_proc, server_proc]:
            proc.terminate()
            proc.join(timeout=5)


def init_db():
    """Initialize the database with seed data"""
    from src.db.init_db import main as init_main
    asyncio.run(init_main())


async def run_test():
    """Quick system test"""
    print("\n[TEST] Running System Tests...\n")
    results = []

    # Test database
    try:
        from src.db.connection import init_database, close_database
        await init_database()
        await close_database()
        results.append(("Database", True))
        print("  [OK] Database")
    except Exception as e:
        results.append(("Database", False))
        print(f"  [FAIL] Database: {e}")

    # Test sensors
    try:
        from src.hardware import MockSensorHub
        sensors = MockSensorHub()
        await sensors.read_all()
        results.append(("Sensors", True))
        print("  [OK] Sensors")
    except Exception as e:
        results.append(("Sensors", False))
        print(f"  [FAIL] Sensors: {e}")

    # Test cultivation
    try:
        from src.cultivation import calculate_vpd
        calculate_vpd(77.0, 50.0)
        results.append(("Cultivation", True))
        print("  [OK] Cultivation")
    except Exception as e:
        results.append(("Cultivation", False))
        print(f"  [FAIL] Cultivation: {e}")

    # Test AI
    try:
        from src.ai import GrokBrain
        GrokBrain()
        results.append(("AI Brain", True))
        print("  [OK] AI Brain")
    except Exception as e:
        results.append(("AI Brain", False))
        print(f"  [FAIL] AI Brain: {e}")

    # Summary
    passed = sum(1 for _, r in results if r)
    print(f"\n  Passed: {passed}/{len(results)}")
    return all(r for _, r in results)


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        command = "all"
    else:
        command = sys.argv[1].lower()

    commands = {
        "server": run_server,
        "openclaw": run_openclaw,
        "orchestrator": lambda: asyncio.run(run_orchestrator()),
        "social": lambda: asyncio.run(run_social()),
        "research": lambda: asyncio.run(run_research()),
        "all": run_all,
        "legacy": run_legacy,
        "init": init_db,
        "test": lambda: asyncio.run(run_test()),
    }

    if command in commands:
        print(f"[*] Grok & Mon - Running: {command}")
        print("=" * 50)
        commands[command]()
    elif command in ("-h", "--help", "help"):
        print(__doc__)
    else:
        print(f"Unknown command: {command}")
        print(f"Available: {', '.join(commands.keys())}")
        sys.exit(1)


if __name__ == "__main__":
    main()
