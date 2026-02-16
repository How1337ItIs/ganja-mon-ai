#!/usr/bin/env python3
"""
Generate a *local-only* voice sources JSON from files already present in `voice_samples/`.

This is a pragmatic helper for building a ~N hour dataset without hand-editing `voice_sources.json`.

It does NOT download anything.

Example:
  python make_voice_sources_from_samples.py --target-minutes 180 --out voice_sources_selected.json
  python build_voice_sample_dataset.py --sources voice_sources_selected.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


ROOT = Path(__file__).resolve().parent


def _safe_stdout() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except Exception:
        pass


def _sha1(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8"), usedforsecurity=False).hexdigest()


def _resolve_ffprobe_bin() -> str:
    exe = "ffprobe.exe" if os.name == "nt" else "ffprobe"
    found = shutil.which("ffprobe")
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


FFPROBE_BIN = _resolve_ffprobe_bin()


def duration_seconds(path: Path) -> Optional[float]:
    try:
        out = subprocess.check_output(
            [FFPROBE_BIN, "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
            text=True,
            stderr=subprocess.STDOUT,
        )
        return float(json.loads(out)["format"]["duration"])
    except Exception:
        return None


@dataclass(frozen=True)
class SampleFile:
    voice_id: str
    path: Path
    seconds: float


def iter_samples(samples_dir: Path, *, allowed_exts: Iterable[str]) -> List[SampleFile]:
    out: List[SampleFile] = []
    for p in samples_dir.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() not in allowed_exts:
            continue
        rel = p.relative_to(samples_dir)
        if not rel.parts:
            continue
        voice_id = rel.parts[0]
        secs = duration_seconds(p)
        if secs is None or secs <= 1:
            continue
        out.append(SampleFile(voice_id=voice_id, path=p, seconds=secs))
    return out


def choose_to_quota(
    samples: List[SampleFile],
    *,
    target_minutes_by_voice: Dict[str, float],
    prefer_exts: Tuple[str, ...],
    exclude_title_contains: Tuple[str, ...],
) -> List[SampleFile]:
    selected: List[SampleFile] = []
    by_voice: Dict[str, List[SampleFile]] = {}
    for s in samples:
        by_voice.setdefault(s.voice_id, []).append(s)

    for voice_id, quota_min in target_minutes_by_voice.items():
        quota_sec = quota_min * 60.0
        remaining = quota_sec
        items = by_voice.get(voice_id, [])

        # Filter excluded titles up front.
        filtered: List[SampleFile] = []
        for s in items:
            name = s.path.name.lower()
            if any(tok in name for tok in exclude_title_contains):
                continue
            filtered.append(s)

        def ext_rank(x: SampleFile) -> int:
            ext = x.path.suffix.lower()
            return prefer_exts.index(ext) if ext in prefer_exts else len(prefer_exts) + 1

        # Best-fit greedy selection:
        # - If we can fit something within remaining, pick the longest that still fits (and best ext).
        # - Otherwise pick the smallest file (and best ext) to minimize overshoot.
        pool = sorted(filtered, key=lambda x: (ext_rank(x), x.seconds, str(x.path).lower()))
        used: set[Path] = set()
        while remaining > 0 and pool:
            candidates = [s for s in pool if s.path not in used]
            if not candidates:
                break

            # Prefer files that fit within the remaining budget (with a tiny slack to avoid being too picky).
            slack = 1.05
            fits = [s for s in candidates if s.seconds <= remaining * slack]
            if fits:
                # Among fits: prefer best extension, then longest.
                best = sorted(fits, key=lambda x: (ext_rank(x), -x.seconds, str(x.path).lower()))[0]
            else:
                # Nothing fits: take the smallest (best ext) to minimize overshoot.
                best = sorted(candidates, key=lambda x: (ext_rank(x), x.seconds, str(x.path).lower()))[0]

            selected.append(best)
            used.add(best.path)
            remaining -= best.seconds

    # stable order
    selected.sort(key=lambda x: (x.voice_id.lower(), str(x.path).lower()))
    return selected


def main() -> int:
    _safe_stdout()
    p = argparse.ArgumentParser(description="Generate local-only voice_sources JSON from voice_samples/")
    p.add_argument("--samples-dir", type=str, default=str(ROOT / "voice_samples"))
    p.add_argument("--out", type=str, default=str(ROOT / "voice_sources_selected.json"))
    p.add_argument("--target-minutes", type=float, default=180.0, help="Target total minutes (default: 180 = 3 hours)")
    p.add_argument("--license", type=str, default="user-asserted", help="License label to set on each source")
    args = p.parse_args()

    samples_dir = Path(args.samples_dir)
    if not samples_dir.exists():
        print(f"Missing samples dir: {samples_dir}", file=sys.stderr)
        return 2

    # Fusion recipe (from VOICE_FUSION_HANDOFF.md): 40/30/20/10
    total = float(args.target_minutes)
    target_minutes_by_voice = {
        "little_jacob": total * 0.20,      # half of the 40%
        "hermes": total * 0.20,            # half of the 40%
        "rastamouse": total * 0.30,
        "bob_marley": total * 0.20,
        "lee_perry": total * 0.10,
    }

    allowed_exts = {".mp3", ".wav", ".m4a", ".mp4", ".webm"}
    samples = iter_samples(samples_dir, allowed_exts=allowed_exts)
    if not samples:
        print("No sample media found.", file=sys.stderr)
        return 2

    # Favor audio-only over video containers.
    prefer_exts = (".wav", ".mp3", ".m4a", ".mp4", ".webm")
    exclude_title_contains = (
        "song",
        "mix",
        "dub",
        "instrumental",
        "full album",
        "full concert",
    )

    chosen = choose_to_quota(
        samples,
        target_minutes_by_voice=target_minutes_by_voice,
        prefer_exts=prefer_exts,
        exclude_title_contains=exclude_title_contains,
    )

    # Build output JSON in the schema expected by build_voice_sample_dataset.py
    voices: Dict[str, Dict] = {}
    for s in chosen:
        v = voices.setdefault(
            s.voice_id,
            {
                "id": s.voice_id,
                "display_name": s.voice_id.replace("_", " ").title(),
                "category": "local_samples",
                "notes": "Auto-selected from voice_samples/ to hit target minutes.",
                "sources": [],
            },
        )
        rel_path = s.path.relative_to(ROOT).as_posix()
        sid = _sha1(f"{s.voice_id}|{rel_path}")
        v["sources"].append(
            {
                "id": sid,
                "title": s.path.stem,
                "local_path": rel_path,
                "license": str(args.license),
                "duration_seconds": round(s.seconds, 3),
            }
        )

    out_obj = {
        "schema_version": 1,
        "purpose": "Auto-generated local sources from voice_samples/",
        "copyright_note": "Only include audio you have rights to use.",
        "voices": list(voices.values()),
    }

    out_path = Path(args.out)
    out_path.write_text(json.dumps(out_obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Summary
    mins_by_voice = {k: 0.0 for k in voices.keys()}
    for v in out_obj["voices"]:
        vid = v["id"]
        for src in v["sources"]:
            mins_by_voice[vid] += float(src.get("duration_seconds", 0.0)) / 60.0
    total_mins = sum(mins_by_voice.values())
    print(f"Wrote: {out_path}")
    print(f"Selected voices: {len(mins_by_voice)}")
    for vid, mins in sorted(mins_by_voice.items(), key=lambda x: x[1], reverse=True):
        print(f"- {vid}: {mins:.1f} min")
    print(f"Total selected: {total_mins:.1f} min")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

