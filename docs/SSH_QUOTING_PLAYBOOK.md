# SSH + Quoting Playbook (WSL, PowerShell, Antigravity)

This repo is routinely operated through **three shells in a row**:

1. Local shell (WSL bash OR Windows Git Bash OR Antigravity tool wrapper)
2. Windows PowerShell (`powershell.exe -Command "..."`)
3. Remote bash (Chromebook: `natha@chromebook.lan`)

If you treat it like “just run ssh”, you will lose time to quoting bugs.

## Rule Of Thumb

If the remote command contains **any** of the following, do **not** inline it:
- quotes (`'` or `"`)
- pipes (`|`) or redirects (`>`, `2>&1`)
- regex alternation (`a|b`)
- `$VARS`
- multi-line scripts / heredocs
- `python -c ...` / `jq` one-liners

Instead: **transfer a script and run it** (or write to a remote temp file, then pull it back).

## Known Failure Signatures (And What They Mean)

- `The string is missing the terminator: '.`
  - PowerShell saw an unmatched quote in your `-Command` string.
  - Fix: stop inlining; use the script pattern.

- `error : The term 'error' is not recognized as the name of a cmdlet...`
  - PowerShell parsed a pipeline because your remote string got split on `|`.
  - Common cause: putting a regex like `EADDR|error` somewhere that is not fully inside the remote quoted string.
  - Fix: don’t inline regex with `|`; use script pattern or `grep -F`/two greps.

- `bash: line 1: warning: here-document ...`
  - Newlines/EOF markers got mangled through PS->SSH.
  - Fix: don’t inline heredocs; transfer a script file.

- `$'\\r': command not found`
  - CRLF line endings reached remote bash.
  - Fix: strip CR on the remote before executing (`sed -i 's/\\r$//' file`).

## Patterns That Work Reliably

### A) Trivial inline command (OK)

Use only for simple, single commands:

```bash
powershell.exe -NoProfile -NonInteractive -Command "ssh natha@chromebook.lan 'uptime'"
```

### B) Script pipe + execute (Default for anything non-trivial)

This avoids 99% of quoting pain.

```bash
# local file: tmp_task.sh (must be LF; if created on Windows, expect CRLF)
powershell.exe -NoProfile -NonInteractive -Command "Get-Content 'C:\Users\natha\sol-cannabis\tmp_task.sh' -Raw | ssh natha@chromebook.lan 'cat > /tmp/task.sh && sed -i s/\r$// /tmp/task.sh && bash /tmp/task.sh 2>&1'" > tmp_task_result.txt 2>&1
```

Notes:
- `sed -i s/\r$//` is mandatory when the local file might be CRLF.
- For large outputs, write to a remote file first (e.g. `/tmp/out.txt`) and then pull it back.

### C) Remote output hygiene (avoid garbled logs)

Never stream `journalctl`/`ps aux` directly through an SSH PTY. Redirect on the remote side:

```bash
powershell.exe -NoProfile -NonInteractive -Command "ssh natha@chromebook.lan 'journalctl --user -u grokmon.service --no-pager -n 200 > /tmp/grokmon_log.txt 2>&1; echo DONE'"
powershell.exe -NoProfile -NonInteractive -Command "(ssh natha@chromebook.lan 'cat /tmp/grokmon_log.txt') | Out-File -FilePath 'C:\Users\natha\sol-cannabis\tmp_grokmon_log.txt' -Encoding utf8"
```

## Environment Notes

### Codex CLI (WSL bash)
- Prefer `sshpass` when LAN SSH works (Method 1).
- If WSL can’t reach LAN, use PowerShell SSH (Method 2) and default to Pattern B.

### Antigravity IDE (Windows Git Bash)
- Don’t rely on `cd`; use the tool’s `Cwd` parameter.
- Don’t fight quoting: follow Antigravity’s Pattern B from `antigravity.md`.
