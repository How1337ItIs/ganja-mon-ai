#!/usr/bin/env python3
"""
Text-to-text "Ganja Mon" translator (NO voice, NO emotion tags).

Goal:
- Transform English -> Jamaican Patois / Rasta-flavored dialect
- Preserve meaning exactly (questions stay questions; don't answer)
- Keep the same "Ganja Mon" personality vibe
- Output plain text ONLY (no bracketed emotion tags like [laughs])

Usage:
  python rasta_text_translate.py "Hello everyone, welcome to the space!"
  python rasta_text_translate.py --repl
  type input.txt | python rasta_text_translate.py

Env (.env in rasta-voice/):
  XAI_API_KEY=...
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv(Path(__file__).parent / ".env")


RASTA_TEXT_SYSTEM_PROMPT = """
You are "Ganja Mon".

Task: Translate the user's English into Jamaican Patois / Western Rasta-flavored dialect while preserving the EXACT meaning.

Hard rules:
- Preserve meaning IDENTICALLY. Questions remain questions. Statements remain statements. Do NOT answer questions.
- Keep technical terms and proper nouns unchanged.
- Output ONLY the translated text. No explanations. No quotes.
- ABSOLUTELY NO emotion tags ([laughs], etc).

Style (Twitter/Telegram Optimized):
- **Clean & Natural:** No excessive dots (...) or drawn-out vowels. Keep it readable and crisp.
- **Social Flow:** Write as if posting on Twitter or chatting on Telegram. Short, punchy, engaging.
- **Patois:** Use "mon", "di", "dem", "ting", "wah gwaan" naturally.
- **Variety:** Use "seen" occasionally for emphasis, but don't overuse it.

Language of Consciousness (Iyaric):
- **First Person:** Strong preference for "I and I", "I-man". Avoid "me/mi".
- **Word Power:** "Overstand" (understand), "Apprecilove" (appreciate), "Downpress" (oppress).

=== GANJA OBSESSION (The Sacrament) ===
- Ganja is your life, your medicine, and your connection to Jah.
- NATURALLY weave references to di herb into translations (50-70% of the time).
- **Spiritual Depth:** Reference "Di chalice", "Reasoning", "Di holy herb", "Sacrament", "Healing of di nations".
- Weave these references naturally, but ALWAYS preserve the original meaning first.

Examples:
- "I need more money" -> "I and I need more funds to keep di chalice burning, mon."
- "The code is broken" -> "Di code mash up, mon. We haffi fix it ASAP."
- "What do you think?" -> "Wah yuh a pree, mon? Tell I and I di truth, overstand? 🤔"
- "It's beautiful outside" -> "It look wicked outside today, mon. Jah bless di creation. 🙏"

Remember: Translate meaning exactly. Keep it clean, social-media ready, and spiritually elevated.
""".strip()


_BRACKET_TAG_RE = re.compile(r"\[[^\]]+\]")


def clean_translation(text: str) -> str:
    """
    Defensive cleanup in case the model leaks tags/quotes.
    We keep this conservative to avoid changing meaning.
    """
    s = (text or "").strip()

    # Remove wrapping quotes (common leakage)
    if len(s) >= 2 and ((s[0] == s[-1] == '"') or (s[0] == s[-1] == "'")):
        s = s[1:-1].strip()

    # Remove bracketed tags like [laughs] (shouldn't happen, but guard)
    s = _BRACKET_TAG_RE.sub("", s).strip()

    # Collapse multiple spaces created by tag removal
    s = re.sub(r"[ \t]{2,}", " ", s).strip()

    return s


def build_client(api_key: str) -> OpenAI:
    return OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")


def translate_once(
    client: OpenAI,
    *,
    model: str,
    text: str,
    temperature: float,
    context: str = "",
    max_tokens: int = 250,
) -> tuple[str, float]:
    start = time.perf_counter()

    user_message = text
    if context.strip():
        user_message = f"Context:\n{context.strip()}\n\nTranslate (preserve meaning): {text}"

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": RASTA_TEXT_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )

    latency_ms = (time.perf_counter() - start) * 1000
    out = resp.choices[0].message.content or ""
    return clean_translation(out), latency_ms


def read_stdin_if_piped() -> Optional[str]:
    if sys.stdin is None or sys.stdin.isatty():
        return None
    data = sys.stdin.read()
    return data if data.strip() else None


def main() -> int:
    parser = argparse.ArgumentParser(description="Text-to-text Ganja Mon translator (no emotion tags).")
    parser.add_argument("text", nargs="?", default="", help="Text to translate. If omitted, reads from stdin or REPL.")
    parser.add_argument("--model", default=os.getenv("XAI_TEXT_MODEL", "grok-3"), help="xAI model name.")
    parser.add_argument("--temperature", type=float, default=0.7, help="Sampling temperature.")
    parser.add_argument("--context", default="", help="Optional context to help translation.")
    parser.add_argument("--context-file", default="", help="Optional file path containing context text.")
    parser.add_argument("--repl", action="store_true", help="Interactive mode.")
    parser.add_argument("--show-latency", action="store_true", help="Print latency to stderr.")
    args = parser.parse_args()

    api_key = os.getenv("XAI_API_KEY", "").strip()
    if not api_key:
        print("Missing XAI_API_KEY. Put it in rasta-voice/.env or your environment.", file=sys.stderr)
        return 2

    context = args.context
    if args.context_file:
        try:
            context = Path(args.context_file).read_text(encoding="utf-8")
        except Exception as e:
            print(f"Failed to read --context-file: {e}", file=sys.stderr)
            return 2

    client = build_client(api_key)

    if args.repl:
        try:
            while True:
                line = input("You: ").strip()
                if not line:
                    continue
                if line.lower() in {"q", "quit", "exit"}:
                    return 0
                translated, latency = translate_once(
                    client,
                    model=args.model,
                    text=line,
                    temperature=args.temperature,
                    context=context,
                )
                print(translated)
                if args.show_latency:
                    print(f"(latency {latency:.0f}ms)", file=sys.stderr)
        except KeyboardInterrupt:
            return 0

    piped = read_stdin_if_piped()
    text = (args.text or "").strip() or (piped or "").strip()
    if not text:
        # Default to REPL if nothing else provided
        print("No input provided. Use --repl, pass text, or pipe stdin.", file=sys.stderr)
        return 2

    translated, latency = translate_once(
        client,
        model=args.model,
        text=text,
        temperature=args.temperature,
        context=context,
    )
    print(translated)
    if args.show_latency:
        print(f"(latency {latency:.0f}ms)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

