#!/usr/bin/env python3
"""
Acquire (bundle) all "Rasta Voice" materials into a reproducible archive.

Pattern: discover -> manifest -> copy (resume-safe) -> optional zip.

What this collects by default (tunable via flags):
- Code + docs + configs
- Transcript/log artifacts (e.g. live_transcripts.jsonl, ralph_logs/, handoff docs)
- Example media outputs (mp3/wav/mp4/png)
- Voice/RVC assets (rvc_models/, xtts_speaker/)

What it avoids by default:
- venv/ (huge)
- obvious secrets (.env*, *.pem, *.key)

Run examples:
  python rasta-voice/acquire_rasta_materials.py --dry-run
  python rasta-voice/acquire_rasta_materials.py --out-dir rasta-voice/material_exports
  python rasta-voice/acquire_rasta_materials.py --pull-dashboard-transcripts
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import platform
import shutil
import sys
import time
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests


REPO_ROOT = Path(__file__).resolve().parents[1]
RASTA_DIR = Path(__file__).resolve().parent


DEFAULT_INCLUDE_GLOBS = [
    # Code & docs
    "**/*.py",
    "**/*.md",
    "**/*.txt",
    "**/*.json",
    "**/*.jsonl",
    "**/*.html",
    "**/*.ps1",
    "**/*.bat",
    "**/*.png",
    # Media artifacts
    "**/*.wav",
    "**/*.mp3",
    "**/*.mp4",
    # Key config files
    "**/requirements.txt",
    "**/voice_config.json",
    "**/voice_sources.json",
    "**/expression_bank.json",
    "**/pipeline.pid",
    "**/conversation_output.log",
    # Model / voice assets
    "rvc_models/**",
    "xtts_speaker/**",
    "ralph_logs/**",
    "docs/**",
    "music/**",
]

DEFAULT_EXCLUDE_GLOBS = [
    "venv/**",
    "**/__pycache__/**",
    "**/.pytest_cache/**",
    "**/.mypy_cache/**",
    "**/.ruff_cache/**",
    # secrets (conservative)
    ".env",
    ".env.*",
    "**/*.pem",
    "**/*.key",
    "**/*secret*",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rel_to_rasta(path: Path) -> str:
    return path.resolve().relative_to(RASTA_DIR).as_posix()


def any_match(path: str, globs: Iterable[str]) -> bool:
    p = PurePosixPath(path)
    for g in globs:
        # PurePosixPath.match supports ** semantics (unlike naive fnmatch for our use-case).
        if p.match(g):
            return True
        # Pathlib quirk: '**/*.py' does NOT match 'file.py' at root.
        # Treat a leading '**/' as optional so root-level files match too.
        if g.startswith("**/") and p.match(g[3:]):
            return True
    return False


def iter_candidate_files(
    base_dir: Path,
    include_globs: List[str],
    exclude_globs: List[str],
    *,
    follow_symlinks: bool,
) -> List[Path]:
    out: List[Path] = []

    # We do a walk to respect directory excludes efficiently.
    for root, dirs, files in os.walk(base_dir, followlinks=follow_symlinks):
        root_path = Path(root)
        rel_root = root_path.resolve().relative_to(base_dir).as_posix()
        if rel_root == ".":
            rel_root = ""

        # Prune excluded dirs
        pruned_dirs: List[str] = []
        for d in list(dirs):
            rel_dir = f"{rel_root}/{d}" if rel_root else d
            rel_dir_glob = rel_dir + "/"
            if any_match(rel_dir_glob, exclude_globs) or any_match(rel_dir, exclude_globs):
                pruned_dirs.append(d)
        for d in pruned_dirs:
            dirs.remove(d)

        for f in files:
            p = root_path / f
            try:
                rel = rel_to_rasta(p)
            except Exception:
                # outside rasta dir (symlink) - skip unless following symlinks AND it still resolves within
                continue

            if any_match(rel, exclude_globs):
                continue

            if any_match(rel, include_globs):
                out.append(p)

    # stable order for manifests
    out.sort(key=lambda p: rel_to_rasta(p).lower())
    return out


@dataclass
class MaterialItem:
    relpath: str
    size_bytes: int
    sha256: str
    mtime_epoch: float
    copied: bool = False
    error: Optional[str] = None


class Manifest:
    def __init__(self, path: Path):
        self.path = path
        self.data: Dict[str, Any] = {
            "version": 1,
            "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "items": {},  # relpath -> MaterialItem dict
        }
        if path.exists():
            try:
                self.data = json.loads(path.read_text(encoding="utf-8"))
                self.data.setdefault("items", {})
            except Exception:
                # keep going with fresh manifest
                pass

    def get_item(self, relpath: str) -> Optional[Dict[str, Any]]:
        return self.data.get("items", {}).get(relpath)

    def upsert_item(self, item: MaterialItem) -> None:
        self.data.setdefault("items", {})[item.relpath] = asdict(item)
        self.data["updated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.path)


def pull_dashboard_transcripts(dst: Path, url: str = "http://localhost:8085/api/transcripts") -> Optional[str]:
    """
    If the dashboard is running, pulls transcript history into a JSON file.
    Returns error message if it fails; otherwise None.
    """
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(json.dumps(r.json(), indent=2, ensure_ascii=False), encoding="utf-8")
        return None
    except Exception as e:
        return str(e)


def zip_dir(src_dir: Path, zip_path: Path) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in src_dir.rglob("*"):
            if p.is_dir():
                continue
            arcname = p.relative_to(src_dir).as_posix()
            z.write(p, arcname)


def main() -> int:
    parser = argparse.ArgumentParser(description="Bundle rasta-voice materials into a manifest + archive.")
    parser.add_argument("--out-dir", type=str, default=str(RASTA_DIR / "material_exports"), help="Output directory for bundles")
    parser.add_argument("--run-id", type=str, default="", help="Run id (default: timestamp)")
    parser.add_argument("--dry-run", action="store_true", help="List what would be included without copying")
    parser.add_argument("--no-zip", action="store_true", help="Don't create a zip at the end")
    parser.add_argument("--zip-path", type=str, default="", help="Optional explicit zip output path (useful if C: is low on space)")
    parser.add_argument("--follow-symlinks", action="store_true", help="Follow symlinks when walking files")
    parser.add_argument("--include", action="append", default=[], help="Additional include glob (repeatable)")
    parser.add_argument("--exclude", action="append", default=[], help="Additional exclude glob (repeatable)")
    parser.add_argument("--include-venv", action="store_true", help="Include venv/ (not recommended, huge)")
    parser.add_argument("--include-secrets", action="store_true", help="Allow .env* and *secret* files (not recommended)")
    parser.add_argument("--max-file-mb", type=int, default=1024, help="Skip files larger than this (default: 1024MB)")
    parser.add_argument("--pull-dashboard-transcripts", action="store_true", help="If dashboard is running, pull /api/transcripts into bundle")
    args = parser.parse_args()

    run_id = args.run_id.strip() or utc_now()
    out_dir = Path(args.out_dir)
    run_dir = out_dir / run_id
    bundle_dir = run_dir / "bundle"
    manifest_path = run_dir / "manifest.json"
    meta_path = run_dir / "meta.json"
    zip_path = Path(args.zip_path) if args.zip_path else (out_dir / f"rasta_voice_materials_{run_id}.zip")

    include_globs = list(DEFAULT_INCLUDE_GLOBS) + list(args.include or [])
    exclude_globs = list(DEFAULT_EXCLUDE_GLOBS) + list(args.exclude or [])
    if args.include_venv:
        exclude_globs = [g for g in exclude_globs if not g.startswith("venv/")]
    if args.include_secrets:
        exclude_globs = [g for g in exclude_globs if g not in {".env", ".env.*"} and "secret" not in g.lower()]

    manifest = Manifest(manifest_path)

    # Optional: pull dashboard transcripts into the bundle source tree so it gets included
    if args.pull_dashboard_transcripts:
        err = pull_dashboard_transcripts(run_dir / "bundle" / "dashboard_transcripts.json")
        if err:
            print(f"WARNING: dashboard transcripts pull failed: {err}", file=sys.stderr)

    files = iter_candidate_files(
        RASTA_DIR,
        include_globs=include_globs,
        exclude_globs=exclude_globs,
        follow_symlinks=args.follow_symlinks,
    )

    max_bytes = int(args.max_file_mb) * 1024 * 1024
    selected: List[Path] = []
    skipped_large: List[Tuple[str, int]] = []
    for p in files:
        try:
            sz = p.stat().st_size
        except Exception:
            continue
        rel = rel_to_rasta(p)
        if sz > max_bytes:
            skipped_large.append((rel, sz))
            continue
        selected.append(p)

    if args.dry_run:
        total = sum(p.stat().st_size for p in selected if p.exists())
        print(f"Run id: {run_id}")
        print(f"Would include {len(selected)} files, total ~{total/1024/1024:.1f} MB")
        if skipped_large:
            print(f"Skipped {len(skipped_large)} files over {args.max_file_mb}MB")
        for p in selected[:200]:
            print(rel_to_rasta(p))
        if len(selected) > 200:
            print(f"... and {len(selected) - 200} more")
        return 0

    run_dir.mkdir(parents=True, exist_ok=True)
    bundle_dir.mkdir(parents=True, exist_ok=True)

    # Meta info
    meta = {
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "repo_root": str(REPO_ROOT),
        "rasta_dir": str(RASTA_DIR),
        "python": sys.version,
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
        },
        "include_globs": include_globs,
        "exclude_globs": exclude_globs,
        "max_file_mb": args.max_file_mb,
        "zip_path": str(zip_path) if not args.no_zip else None,
    }
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    # Copy with resume
    copied = 0
    already = 0
    failed = 0
    start = time.time()

    for src in selected:
        rel = rel_to_rasta(src)
        existing = manifest.get_item(rel)
        if existing and existing.get("copied") and (bundle_dir / rel).exists():
            already += 1
            continue

        dst = bundle_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            st = src.stat()
            digest = sha256_file(src)
            shutil.copy2(src, dst)
            item = MaterialItem(
                relpath=rel,
                size_bytes=st.st_size,
                sha256=digest,
                mtime_epoch=st.st_mtime,
                copied=True,
                error=None,
            )
            manifest.upsert_item(item)
            copied += 1
            # persist progress frequently
            if copied % 25 == 0:
                manifest.save()
        except Exception as e:
            failed += 1
            item = MaterialItem(relpath=rel, size_bytes=0, sha256="", mtime_epoch=0.0, copied=False, error=str(e))
            manifest.upsert_item(item)
            manifest.save()

    manifest.save()

    if not args.no_zip:
        try:
            zip_dir(bundle_dir, zip_path)
        except OSError as e:
            # Common on Windows: errno 28 no space left on device.
            print(f"WARNING: zip creation failed: {e}", file=sys.stderr)
            # Keep the bundle directory + manifest as the primary artifact.

    elapsed = time.time() - start
    print(f"Bundle complete: {run_dir}")
    print(f"Copied: {copied}, already-present: {already}, failed: {failed}, elapsed: {elapsed:.1f}s")
    if not args.no_zip:
        print(f"Zip: {zip_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

