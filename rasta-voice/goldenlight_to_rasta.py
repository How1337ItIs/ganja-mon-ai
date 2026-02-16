#!/usr/bin/env python3
"""
Translate all Goldenlight (and optionally Remilia blog) articles to Rasta Mon.

Uses the same Ganja Mon / Jamaican Patois voice as rasta_text_translate.py.
Processes articles in paragraph-sized chunks to preserve quality and stay within API limits.

Usage:
  python goldenlight_to_rasta.py                    # goldenlight.mirror.xyz only (12 essays)
  python goldenlight_to_rasta.py --all             # goldenlight + blog.remilia.org (71 pages)
  python goldenlight_to_rasta.py --dry-run         # list files only, no API calls
  python goldenlight_to_rasta.py --article "on-jade-posting-gp"  # single article

Output: data/scraped_sites/remilia_goldenlight_text/rasta/...
Env: .env in rasta-voice/ with XAI_API_KEY
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from pathlib import Path
from typing import Optional

# Load env from rasta-voice so XAI_API_KEY is set before importing translator
from dotenv import load_dotenv

_RASTA_VOICE = Path(__file__).resolve().parent
load_dotenv(_RASTA_VOICE / ".env")
if str(_RASTA_VOICE) not in sys.path:
    sys.path.insert(0, str(_RASTA_VOICE))

from rasta_text_translate import (
    build_client,
    translate_once,
)


# Repo-relative paths
DATA_ROOT = Path(__file__).resolve().parent.parent / "data" / "scraped_sites" / "remilia_goldenlight_text"
PAGES = DATA_ROOT / "pages"
GOLDENLIGHT_DIR = PAGES / "goldenlight.mirror.xyz"
BLOG_DIR = PAGES / "blog.remilia.org"
RASTA_OUTPUT_ROOT = DATA_ROOT / "rasta"

# Chunking: max chars per chunk to stay within context; we translate paragraph-by-paragraph
# and merge consecutive short paragraphs up to this size.
MAX_CHUNK_CHARS = 900
MAX_TOKENS_PER_CHUNK = 1024


def get_goldenlight_md_files() -> list[Path]:
    """All .md files in goldenlight.mirror.xyz (exclude README)."""
    if not GOLDENLIGHT_DIR.exists():
        return []
    return [
        p for p in GOLDENLIGHT_DIR.glob("*.md")
        if p.name.lower() != "readme.md"
    ]


def get_all_md_files() -> list[Path]:
    """All .md in goldenlight + blog.remilia.org."""
    out: list[Path] = []
    for d in (GOLDENLIGHT_DIR, BLOG_DIR):
        if d.exists():
            out.extend(p for p in d.glob("*.md") if p.name.lower() != "readme.md")
    return sorted(out, key=lambda p: (p.parent.name, p.name))


def split_frontmatter_and_body(content: str) -> tuple[str, str]:
    """Split markdown into header/metadata (before ---) and body."""
    parts = content.split("\n---\n", 1)
    if len(parts) == 1:
        return "", content
    return parts[0].strip() + "\n", parts[1].strip()


def chunk_body(body: str, max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    """Split body into chunks (paragraphs or groups of short paragraphs)."""
    paragraphs = re.split(r"\n\n+", body)
    chunks: list[str] = []
    current: list[str] = []

    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        # If adding this paragraph would exceed limit, flush current
        combined = "\n\n".join(current + [p])
        if current and len(combined) > max_chars:
            chunks.append("\n\n".join(current))
            current = []
        current.append(p)

        # If this single paragraph is huge, emit it alone (and maybe split by heading later)
        if len(p) > max_chars:
            if current and len(current) > 1:
                chunks.append("\n\n".join(current[:-1]))
                current = [p]
            chunks.append(p)
            current = []

    if current:
        chunks.append("\n\n".join(current))
    return chunks


def translate_chunk(
    client,
    chunk: str,
    *,
    model: str,
    temperature: float,
    article_title: str,
) -> str:
    context = (
        f"This is part of an essay/article titled: {article_title}. "
        "Preserve markdown: keep ### headers, > blockquotes, and line breaks. "
        "Translate the prose to Rasta Mon (Jamaican Patois / Ganja Mon voice)."
    )
    out, _ = translate_once(
        client,
        model=model,
        text=chunk,
        temperature=temperature,
        context=context,
        max_tokens=MAX_TOKENS_PER_CHUNK,
    )
    return out


def extract_title_from_frontmatter(frontmatter: str) -> str:
    """First # line is the title."""
    for line in frontmatter.splitlines():
        s = line.strip()
        if s.startswith("# "):
            return s.lstrip("# ").strip()
    return "Article"


def translate_article(
    client,
    md_path: Path,
    *,
    model: str,
    temperature: float,
    dry_run: bool,
) -> Optional[str]:
    """Read article, translate body in chunks, return full translated markdown."""
    raw = md_path.read_text(encoding="utf-8")
    frontmatter, body = split_frontmatter_and_body(raw)
    title = extract_title_from_frontmatter(frontmatter)

    if dry_run:
        return f"{frontmatter}\n---\n[DRY RUN - body not translated]\n{body[:200]}..."

    if not body.strip():
        return frontmatter + "\n---\n\n"

    chunks = chunk_body(body)
    translated_parts: list[str] = []
    for i, ch in enumerate(chunks):
        translated_parts.append(
            translate_chunk(
                client,
                ch,
                model=model,
                temperature=temperature,
                article_title=title,
            )
        )
        # Small throttle between chunks to avoid rate limits
        if i < len(chunks) - 1:
            time.sleep(0.3)

    new_body = "\n\n".join(translated_parts)
    return frontmatter + "\n---\n\n" + new_body


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Translate Goldenlight (and optionally Remilia blog) articles to Rasta Mon.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Include blog.remilia.org pages (71 total). Default: goldenlight.mirror.xyz only (12).",
    )
    parser.add_argument(
        "--article",
        type=str,
        default="",
        help="Translate only one article by slug (e.g. on-jade-posting-gp or goldenlight filename without .md).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List files and exit without calling the API.",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("XAI_TEXT_MODEL", "grok-3"),
        help="xAI model name.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="Sampling temperature.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=RASTA_OUTPUT_ROOT,
        help="Base output directory (default: data/.../rasta/).",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip articles that already have a translated file in output.",
    )
    args = parser.parse_args()

    if args.all:
        md_files = get_all_md_files()
        subdirs = ("goldenlight.mirror.xyz", "blog.remilia.org")
    else:
        md_files = get_goldenlight_md_files()
        subdirs = ("goldenlight.mirror.xyz",)

    if args.article:
        slug = args.article.strip().lower().removesuffix(".md")
        md_files = [p for p in md_files if p.stem.lower() == slug or p.name.lower() == slug + ".md"]
        if not md_files:
            print(f"No article matching '{args.article}' found.", file=sys.stderr)
            return 2

    if not md_files:
        print("No markdown files found. Check DATA_ROOT and --all.", file=sys.stderr)
        return 2

    if args.skip_existing:
        missing: list[Path] = []
        for p in md_files:
            rel = p.relative_to(PAGES)
            out_path = args.output_dir / rel
            if not out_path.exists():
                missing.append(p)
        skipped = len(md_files) - len(missing)
        if skipped:
            print(f"Skipping {skipped} already translated.", file=sys.stderr)
        md_files = missing
        if not md_files:
            print("All articles already translated. Done.", file=sys.stderr)
            return 0

    print(f"Found {len(md_files)} article(s) to translate. Output: {args.output_dir}", file=sys.stderr)
    if args.dry_run:
        for p in md_files:
            print(p.relative_to(DATA_ROOT), file=sys.stderr)
        return 0

    api_key = os.getenv("XAI_API_KEY", "").strip()
    if not api_key:
        print("Missing XAI_API_KEY. Set it in rasta-voice/.env or environment.", file=sys.stderr)
        return 2

    client = build_client(api_key)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    for md_path in md_files:
        # Preserve subdir: goldenlight.mirror.xyz/foo.md -> rasta/goldenlight.mirror.xyz/foo.md
        rel = md_path.relative_to(PAGES)
        out_path = args.output_dir / rel
        out_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"Translating: {rel} ...", file=sys.stderr)
        try:
            result = translate_article(
                client,
                md_path,
                model=args.model,
                temperature=args.temperature,
                dry_run=False,
            )
            if result:
                out_path.write_text(result, encoding="utf-8")
                print(f"  -> {out_path.relative_to(args.output_dir)}", file=sys.stderr)
        except Exception as e:
            print(f"  ERROR: {e}", file=sys.stderr)
            raise

    print("Done.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
