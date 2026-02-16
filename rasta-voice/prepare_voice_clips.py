#!/usr/bin/env python3
"""
Prepare long-form speaking clips for voice reference.

This script is intentionally conservative:
- It WILL NOT download from YouTube/streaming sites.
- It only supports:
  - local files you already have, OR
  - direct-download URLs you are allowed to download (e.g., CC/public-domain, or you have explicit permission).

It can optionally trim a long file into one or more short reference clips via ffmpeg.

Usage examples:
  python prepare_voice_clips.py --list
  python prepare_voice_clips.py --add-direct-url bob_marley "https://example.com/file.wav"
  python prepare_voice_clips.py --trim bob_marley --input "C:\\path\\to\\file.wav" --start 60 --duration 90
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = ROOT / "voice_sources.json"
OUT_DIR = ROOT / "voice_clips"


def _resolve_ffmpeg_bin() -> str:
    """
    Resolve an ffmpeg executable path.

    On Windows, winget installs may not be visible on PATH for this process.
    We fall back to the WinGet packages location if needed.
    """
    exe = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
    found = shutil.which("ffmpeg")
    if found:
        return found

    if os.name == "nt":
        local_appdata = os.environ.get("LOCALAPPDATA") or ""
        if local_appdata:
            pkg_root = Path(local_appdata) / "Microsoft" / "WinGet" / "Packages"
            try:
                for p in pkg_root.rglob(exe):
                    if p.name.lower() == exe.lower():
                        return str(p)
            except Exception:
                pass

    return exe


FFMPEG_BIN = _resolve_ffmpeg_bin()


def _load_manifest() -> dict[str, Any]:
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Missing manifest: {MANIFEST_PATH}")
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _save_manifest(manifest: dict[str, Any]) -> None:
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _find_voice(manifest: dict[str, Any], voice_id: str) -> dict[str, Any]:
    for v in manifest.get("voices", []):
        if v.get("id") == voice_id:
            return v
    raise KeyError(f"Unknown voice id: {voice_id}")


def _run_ffmpeg_trim(src: Path, dst: Path, start_s: int, duration_s: int) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        FFMPEG_BIN,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-ss",
        str(start_s),
        "-t",
        str(duration_s),
        "-i",
        str(src),
        str(dst),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\n{r.stderr.strip()}")


def _download_direct(url: str, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as resp:
        dst.write_bytes(resp.read())


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--list", action="store_true", help="List known voices and current sources.")
    p.add_argument("--add-direct-url", nargs=2, metavar=("VOICE_ID", "URL"), help="Add a direct-download URL.")
    p.add_argument("--download-direct", nargs=3, metavar=("VOICE_ID", "URL", "FILENAME"), help="Download a direct URL into voice_clips/")
    p.add_argument("--trim", metavar="VOICE_ID", help="Trim an input file into a clip under voice_clips/<voice_id>/")
    p.add_argument("--input", help="Input file path for --trim")
    p.add_argument("--start", type=int, default=0, help="Start seconds for --trim")
    p.add_argument("--duration", type=int, default=60, help="Duration seconds for --trim")
    p.add_argument(
        "--rights-ok",
        action="store_true",
        help="Acknowledge you have rights to download/trim the provided material.",
    )
    args = p.parse_args()

    manifest = _load_manifest()

    if args.list:
        for v in manifest.get("voices", []):
            vid = v.get("id")
            name = v.get("display_name")
            sources = v.get("sources", [])
            print(f"- {vid}: {name} ({len(sources)} sources)")
        return 0

    if args.add_direct_url:
        if not args.rights_ok:
            print("Refusing: pass --rights-ok to confirm you have rights to use this material.", file=sys.stderr)
            return 2
        voice_id, url = args.add_direct_url
        v = _find_voice(manifest, voice_id)
        v.setdefault("sources", []).append(
            {
                "title": "Direct download (user-provided)",
                "url": url,
                "platform": "direct",
                "kind": "download",
                "downloadable": True,
                "license": "user-asserted",
                "suggested_segments": [],
            }
        )
        _save_manifest(manifest)
        print(f"Added direct URL for {voice_id}.")
        return 0

    if args.download_direct:
        if not args.rights_ok:
            print("Refusing: pass --rights-ok to confirm you have rights to download this material.", file=sys.stderr)
            return 2
        voice_id, url, filename = args.download_direct
        _find_voice(manifest, voice_id)  # validate
        dst = OUT_DIR / voice_id / filename
        _download_direct(url, dst)
        print(f"Downloaded to: {dst}")
        return 0

    if args.trim:
        if not args.rights_ok:
            print("Refusing: pass --rights-ok to confirm you have rights to trim this material.", file=sys.stderr)
            return 2
        if not args.input:
            print("--input is required with --trim", file=sys.stderr)
            return 2
        voice_id = args.trim
        _find_voice(manifest, voice_id)  # validate
        src = Path(args.input).expanduser().resolve()
        if not src.exists():
            print(f"Input file not found: {src}", file=sys.stderr)
            return 2
        dst = OUT_DIR / voice_id / f"{voice_id}_s{args.start}_d{args.duration}{src.suffix}"
        _run_ffmpeg_trim(src, dst, args.start, args.duration)
        print(f"Wrote clip: {dst}")
        return 0

    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

