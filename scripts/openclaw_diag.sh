#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "== openclaw diag =="
date
echo

echo "== uptime/load =="
uptime || true
echo

echo "== top (brief) =="
top -b -n 1 | head -n 30 || true
echo

echo "== ports =="
ss -ltnp | grep -E ':8000|:8080|:18789' || true
echo

echo "== openclaw canvas probe =="
curl -sS -m 2 -o /dev/null -w "canvas_http=%{http_code} time=%{time_total}\n" \
  http://127.0.0.1:18789/__openclaw__/canvas/ || true
echo

echo "== openclaw processes =="
ps -eo pid,ppid,etime,pcpu,pmem,rss,vsz,comm,args | grep -i openclaw | grep -v grep || true
echo

echo "== browser processes (chromium/playwright) =="
ps aux | egrep -i 'chromium|chrome|playwright|puppeteer' | grep -v egrep | head -n 60 || true
echo

echo "== gateway pid + /proc stats =="
gateway_pid="$(ss -ltnp 2>/dev/null | grep ':18789' | sed -n 's/.*pid=\\([0-9]\\+\\).*/\\1/p' | head -n 1 || true)"
echo "gateway_pid=${gateway_pid:-}"
if [[ -n "${gateway_pid:-}" ]] && [[ -d "/proc/$gateway_pid" ]]; then
  echo "fd_count=$(ls -1 \"/proc/$gateway_pid/fd\" 2>/dev/null | wc -l | tr -d ' ')"
  grep -E '^(State|Threads|VmRSS|VmSize):' "/proc/$gateway_pid/status" || true
fi
echo

echo "== :18789 tcp state counts =="
ss -tan | awk '$4 ~ /:18789$/ || $5 ~ /:18789$/ {print $1}' | sort | uniq -c | sort -nr | head -n 20 || true
echo

echo "== openclaw log tail (errors/warns) =="
if [[ -f openclaw-workspace/logs/openclaw.log ]]; then
  tail -n 250 openclaw-workspace/logs/openclaw.log | egrep -i 'error|warn|lock timeout|missed jobs|closed before connect|canvas|bonjour|advertise' | tail -n 120 || true
fi
echo

echo "== grokmon journald tail (openclaw lines) =="
journalctl --user -u grokmon.service --no-pager -n 250 | egrep -i 'openclaw|18789|cron store sanitized|unhealthy|restart' | tail -n 160 || true

