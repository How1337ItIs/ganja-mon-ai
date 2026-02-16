#!/usr/bin/env python3
"""
Build a voice-sample dataset (clips + manifest) from *authorized* sources.

This does NOT download from stream-only platforms.
It expects sources to be either:
- local files (recommended), or
- direct downloadable audio URLs you have rights to use.

Input: a JSON file like `voice_sources.json` (schema in this repo).
Output:
  rasta-voice/voice_dataset/<run_id>/
    clips/<voice_id>/<source_id>/clip_00001.wav
    manifest.jsonl   (one record per clip)
    run_meta.json

Requires: ffmpeg available on PATH.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests


RASTA_DIR = Path(__file__).resolve().parent


def now_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def sha1_text(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8"), usedforsecurity=False).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_ffmpeg_bin() -> str:
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
                # Typical: ...\ffmpeg-<ver>_...\bin\ffmpeg.exe
                for p in pkg_root.rglob(exe):
                    if p.name.lower() == exe.lower():
                        return str(p)
            except Exception:
                # If anything goes wrong, fall through to error in ffmpeg_probe().
                pass

    return exe


FFMPEG_BIN = resolve_ffmpeg_bin()


def ffmpeg_probe() -> None:
    try:
        subprocess.run([FFMPEG_BIN, "-version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError as e:
        raise RuntimeError("ffmpeg not found on PATH. Install ffmpeg to build the dataset.") from e


def safe_name(s: str, max_len: int = 80) -> str:
    s = (s or "").strip()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[^a-zA-Z0-9._\- ]+", "_", s)
    s = s.strip(" .")
    if not s:
        return "unknown"
    if len(s) > max_len:
        s = s[:max_len].rstrip(" .")
    return s


def download_to_file(url: str, dest: Path, *, timeout_s: int = 60) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=timeout_s) as r:
        r.raise_for_status()
        tmp = dest.with_suffix(dest.suffix + ".part")
        with tmp.open("wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 256):
                if chunk:
                    f.write(chunk)
        tmp.replace(dest)


def convert_to_wav_48k_mono(src: Path, dst_wav: Path) -> None:
    dst_wav.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        FFMPEG_BIN,
        "-y",
        "-i",
        str(src),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "48000",
        "-c:a",
        "pcm_s16le",
        str(dst_wav),
    ]
    subprocess.run(cmd, check=True)


def segment_wav(
    src_wav: Path,
    out_dir: Path,
    *,
    clip_seconds: int,
) -> List[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_pattern = out_dir / "clip_%05d.wav"
    cmd = [
        FFMPEG_BIN,
        "-y",
        "-i",
        str(src_wav),
        "-f",
        "segment",
        "-segment_time",
        str(int(clip_seconds)),
        "-reset_timestamps",
        "1",
        "-c:a",
        "pcm_s16le",
        str(out_pattern),
    ]
    subprocess.run(cmd, check=True)
    return sorted(out_dir.glob("clip_*.wav"))


@dataclass
class SourceSpec:
    source_id: str
    title: str
    voice_id: str
    voice_name: str
    local_path: Optional[str]
    direct_audio_url: Optional[str]
    license: str  # e.g. "public_domain" | "cc" | "permission" | "owned"


def load_sources(path: Path) -> List[SourceSpec]:
    data = json.loads(path.read_text(encoding="utf-8"))
    voices = data.get("voices") or []
    out: List[SourceSpec] = []

    for v in voices:
        voice_id = v.get("id") or safe_name(v.get("display_name") or "unknown")
        voice_name = v.get("display_name") or voice_id
        for s in (v.get("sources") or []):
            local_path = s.get("local_path")
            direct_audio_url = s.get("direct_audio_url")
            license_name = (s.get("license") or "").strip()

            # Only include sources that are actually usable for dataset building
            if not local_path and not direct_audio_url:
                continue
            if not license_name:
                # Require the user to explicitly label rights (prevents accidental misuse).
                continue

            sid = s.get("id") or sha1_text((local_path or "") + "|" + (direct_audio_url or "") + "|" + voice_id)
            out.append(
                SourceSpec(
                    source_id=sid,
                    title=s.get("title") or sid,
                    voice_id=voice_id,
                    voice_name=voice_name,
                    local_path=local_path,
                    direct_audio_url=direct_audio_url,
                    license=license_name,
                )
            )
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a local voice-sample dataset (authorized sources only).")
    parser.add_argument(
        "--sources",
        type=str,
        default=str(RASTA_DIR / "voice_sources.json"),
        help="Path to voice sources json (default: rasta-voice/voice_sources.json)",
    )
    parser.add_argument("--out-dir", type=str, default=str(RASTA_DIR / "voice_dataset"), help="Output root directory")
    parser.add_argument("--run-id", type=str, default="", help="Run id (default: timestamp)")
    parser.add_argument("--clip-seconds", type=int, default=20, help="Clip length in seconds")
    parser.add_argument("--max-clips-per-source", type=int, default=0, help="Limit clips per source (0 = no limit)")
    parser.add_argument("--download-cache", type=str, default=str(RASTA_DIR / "voice_dataset" / "_downloads"), help="Where to store downloaded sources")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be processed")
    args = parser.parse_args()

    ffmpeg_probe()

    sources_path = Path(args.sources)
    out_root = Path(args.out_dir)
    run_id = args.run_id.strip() or now_id()
    run_dir = out_root / run_id
    clips_root = run_dir / "clips"
    manifest_path = run_dir / "manifest.jsonl"
    meta_path = run_dir / "run_meta.json"
    download_cache = Path(args.download_cache)

    specs = load_sources(sources_path)
    if not specs:
        print(
            "No usable sources found.\n"
            "To use this builder, add sources with either `local_path` or `direct_audio_url`, AND a `license` field.\n"
            "Example source object:\n"
            '  {"title":"My interview","local_path":"C:/path/file.mp4","license":"owned"}\n',
            file=sys.stderr,
        )
        return 2

    if args.dry_run:
        print(f"Would process {len(specs)} sources")
        for s in specs[:200]:
            print(f"- {s.voice_id}: {s.title} ({'local' if s.local_path else 'url'}) license={s.license}")
        if len(specs) > 200:
            print(f"... and {len(specs) - 200} more")
        return 0

    run_dir.mkdir(parents=True, exist_ok=True)
    clips_root.mkdir(parents=True, exist_ok=True)
    meta = {
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "sources_file": str(sources_path),
        "clip_seconds": int(args.clip_seconds),
        "max_clips_per_source": int(args.max_clips_per_source),
        "platform": {
            "cwd": os.getcwd(),
            "python": sys.version,
        },
    }
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    written = 0
    with manifest_path.open("w", encoding="utf-8") as mf:
        for spec in specs:
            # Resolve source file
            if spec.local_path:
                src = Path(spec.local_path)
                # Make relative paths stable: resolve relative to the sources file location.
                if not src.is_absolute():
                    src = sources_path.parent / src
                if not src.exists():
                    print(f"WARNING: missing local_path, skipping: {spec.local_path}", file=sys.stderr)
                    continue
            else:
                # direct downloadable URL (authorized)
                url = spec.direct_audio_url or ""
                ext = Path(url).suffix or ".bin"
                src = download_cache / spec.voice_id / f"{spec.source_id}{ext}"
                if not src.exists():
                    download_to_file(url, src)

            # Convert to wav
            wav_dir = run_dir / "_wav" / safe_name(spec.voice_id)
            wav_path = wav_dir / f"{safe_name(spec.source_id)}.wav"
            if not wav_path.exists():
                convert_to_wav_48k_mono(src, wav_path)

            # Segment into clips
            clip_dir = clips_root / safe_name(spec.voice_id) / safe_name(spec.source_id)
            clips = segment_wav(wav_path, clip_dir, clip_seconds=int(args.clip_seconds))
            if args.max_clips_per_source and args.max_clips_per_source > 0:
                clips = clips[: int(args.max_clips_per_source)]

            for clip in clips:
                record = {
                    "voice_id": spec.voice_id,
                    "voice_name": spec.voice_name,
                    "source_id": spec.source_id,
                    "source_title": spec.title,
                    "license": spec.license,
                    "clip_path": clip.relative_to(run_dir).as_posix(),
                    "clip_bytes": clip.stat().st_size,
                    "clip_sha256": sha256_file(clip),
                    "sample_rate_hz": 48000,
                    "channels": 1,
                    "format": "wav_s16le",
                }
                mf.write(json.dumps(record, ensure_ascii=False) + "\n")
                written += 1

    print(f"Dataset built: {run_dir}")
    print(f"Clips written: {written}")
    print(f"Manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

