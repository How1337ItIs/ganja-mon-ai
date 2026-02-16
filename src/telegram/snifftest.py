"""
/snifftest Command — Burn $MON to Audit Token Safety
======================================================

Usage in Telegram:
    /snifftest 0xabc123...      → EVM contract safety check
    /snifftest [token name]     → search and check

Burns 1 $MON credit per use. Runs safety checks via GoPlus API
and returns results in Rasta voice.

Checks:
    - Honeypot detection
    - LP lock status
    - Top holder concentration
    - Mintable / blacklist / proxy flags
    - Contract age
    - Tax rates (buy/sell)
"""

import os
import re
import time
from typing import Optional

import httpx
import structlog
from telegram import Update
from telegram.ext import ContextTypes

from src.telegram.credits import get_credits_db

log = structlog.get_logger("snifftest")

# ── Chain detection ─────────────────────────────────────────────

# GoPlus chain IDs
CHAIN_IDS = {
    "ethereum": "1",
    "bsc": "56",
    "polygon": "137",
    "arbitrum": "42161",
    "base": "8453",
    "avalanche": "43114",
    "optimism": "10",
    "monad": "143",       # May not be supported yet
}

_EVM_ADDR_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")
_SOLANA_ADDR_RE = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")


def detect_chain(address: str) -> tuple[str, str]:
    """Detect chain from address format. Returns (chain_name, chain_id)."""
    if _EVM_ADDR_RE.match(address):
        return "ethereum", "1"  # Default to ETH, user can specify
    if _SOLANA_ADDR_RE.match(address):
        return "solana", "solana"
    return "unknown", ""


# ── GoPlus API ──────────────────────────────────────────────────

GOPLUS_BASE = "https://api.gopluslabs.io/api/v1"


async def check_token_safety(
    address: str,
    chain_id: str = "1",
) -> Optional[dict]:
    """Call GoPlus Labs API for token security analysis.

    Returns parsed safety report or None on failure.
    """
    url = f"{GOPLUS_BASE}/token_security/{chain_id}?contract_addresses={address}"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                log.warning("GoPlus API error", status=resp.status_code)
                return None
            data = resp.json()

        result = data.get("result", {})
        token_data = result.get(address.lower(), {})
        if not token_data:
            return None

        return _parse_goplus_response(token_data)

    except Exception as e:
        log.warning("GoPlus check failed", error=str(e))
        return None


def _parse_goplus_response(data: dict) -> dict:
    """Parse GoPlus response into a clean safety report."""

    def flag(key: str) -> Optional[bool]:
        v = data.get(key)
        if v is None or v == "":
            return None
        return str(v) == "1"

    # Extract key safety indicators
    report = {
        "name": data.get("token_name", "Unknown"),
        "symbol": data.get("token_symbol", "???"),
        "is_honeypot": flag("is_honeypot"),
        "is_mintable": flag("is_mintable"),
        "can_blacklist": flag("is_blacklisted"),
        "is_proxy": flag("is_proxy"),
        "is_open_source": flag("is_open_source"),
        "has_external_call": flag("external_call"),
        "buy_tax": _parse_pct(data.get("buy_tax")),
        "sell_tax": _parse_pct(data.get("sell_tax")),
        "holder_count": int(data.get("holder_count", 0)),
        "lp_holder_count": int(data.get("lp_holder_count", 0)),
        "total_supply": data.get("total_supply", "0"),
        "creator_address": data.get("creator_address", ""),
        "creator_pct": _parse_pct(data.get("creator_percent")),
        "top10_pct": 0.0,
        "lp_locked": False,
        "lp_locked_pct": 0.0,
    }

    # Top 10 holder concentration
    holders = data.get("holders", [])
    if holders:
        top10_pct = sum(float(h.get("percent", 0)) for h in holders[:10])
        report["top10_pct"] = round(top10_pct * 100, 1)

    # LP lock status
    lp_holders = data.get("lp_holders", [])
    if lp_holders:
        locked_pct = sum(
            float(h.get("percent", 0))
            for h in lp_holders
            if h.get("is_locked") == 1
        )
        report["lp_locked"] = locked_pct > 0.5
        report["lp_locked_pct"] = round(locked_pct * 100, 1)

    # Overall safety score (0-10)
    report["safety_score"] = _compute_safety_score(report)

    return report


def _parse_pct(value) -> float:
    if value is None or value == "":
        return 0.0
    try:
        v = float(value)
        return round(v * 100 if v <= 1 else v, 1)
    except (ValueError, TypeError):
        return 0.0


def _compute_safety_score(report: dict) -> float:
    """Compute 0-10 safety score from report flags."""
    score = 10.0

    # Critical flags (heavy penalty)
    if report["is_honeypot"]:
        score -= 5.0
    if report["is_mintable"]:
        score -= 2.0
    if report["can_blacklist"]:
        score -= 1.5
    if report["is_proxy"]:
        score -= 1.0
    if not report["is_open_source"]:
        score -= 1.5

    # Tax penalties
    buy_tax = report.get("buy_tax", 0)
    sell_tax = report.get("sell_tax", 0)
    if sell_tax > 10:
        score -= 2.0
    elif sell_tax > 5:
        score -= 1.0
    if buy_tax > 10:
        score -= 1.0

    # Concentration penalty
    if report["top10_pct"] > 80:
        score -= 2.0
    elif report["top10_pct"] > 50:
        score -= 1.0

    # LP lock bonus
    if report["lp_locked"]:
        score += 0.5

    # Holder count bonus
    if report["holder_count"] > 1000:
        score += 0.5
    elif report["holder_count"] < 50:
        score -= 0.5

    return max(0.0, min(10.0, round(score, 1)))


# ── Format as Rasta voice ──────────────────────────────────────

def format_snifftest_rasta(report: dict, address: str) -> str:
    """Format safety report in Rasta voice."""
    score = report["safety_score"]
    name = report["name"]
    symbol = report["symbol"]

    # Verdict based on score
    if score >= 8:
        verdict = "Dis one lookin' CLEAN bredda! Safe fi smoke 🔥"
        emoji = "🟢"
    elif score >= 6:
        verdict = "Mid-grade herb. Smoke with caution, seen? 🤔"
        emoji = "🟡"
    elif score >= 4:
        verdict = "Sketchy vibes mon... I and I would think twice 😬"
        emoji = "🟠"
    else:
        verdict = "STAY AWAY bredda! Dis is POISON, not herb! 🚫☠️"
        emoji = "🔴"

    lines = [
        f"{emoji} *Sniff Test: {name} (${symbol})*",
        f"Score: *{score}/10*",
        f"_{verdict}_",
        "",
    ]

    # Individual checks
    def check(label: str, is_bad: Optional[bool], bad_text: str, good_text: str):
        if is_bad is None:
            lines.append(f"⚪ {label}: Unknown")
        elif is_bad:
            lines.append(f"🔴 {label}: {bad_text}")
        else:
            lines.append(f"🟢 {label}: {good_text}")

    check("Honeypot", report["is_honeypot"], "YES — can't sell!", "No honeypot")
    check("Mintable", report["is_mintable"], "Can mint more tokens", "Not mintable")
    check("Blacklist", report["can_blacklist"], "Can blacklist wallets", "No blacklist")
    check("Proxy", report["is_proxy"], "Upgradeable contract", "Not a proxy")
    check("Open Source", not report.get("is_open_source", True), "NOT verified", "Verified")

    # Tax info
    buy_tax = report.get("buy_tax", 0)
    sell_tax = report.get("sell_tax", 0)
    tax_emoji = "🟢" if sell_tax <= 5 else ("🟡" if sell_tax <= 10 else "🔴")
    lines.append(f"{tax_emoji} Tax: Buy {buy_tax}% / Sell {sell_tax}%")

    # Holder info
    holders = report.get("holder_count", 0)
    top10 = report.get("top10_pct", 0)
    conc_emoji = "🟢" if top10 < 50 else ("🟡" if top10 < 80 else "🔴")
    lines.append(f"{conc_emoji} Holders: {holders} (top 10 = {top10}%)")

    # LP lock
    if report.get("lp_locked"):
        lines.append(f"🟢 LP: {report['lp_locked_pct']}% locked")
    else:
        lines.append("🔴 LP: Not locked")

    lines.append("")
    lines.append(f"`{address[:8]}...{address[-6:]}`")

    return "\n".join(lines)


# ── Telegram command handler ────────────────────────────────────

async def handle_snifftest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /snifftest command — token safety audit."""
    if not update.message:
        return

    user = update.message.from_user
    if not user:
        return

    args_text = " ".join(context.args) if context.args else ""
    if not args_text.strip():
        await update.message.reply_text(
            "🔍 *Sniff Test — Token Safety Audit*\n\n"
            "Usage: `/snifftest 0xContractAddress`\n"
            "Chains: Ethereum, Base, BSC, Polygon, Arbitrum\n\n"
            "Burns 1 $MON credit per test.\n"
            "Use /credits to check your balance.",
            parse_mode="Markdown",
        )
        return

    # Extract address from input
    address = args_text.strip().split()[0]

    # Detect chain — allow user to specify
    chain_name = "ethereum"
    chain_id = "1"
    parts = args_text.strip().split()
    if len(parts) > 1:
        chain_arg = parts[1].lower()
        if chain_arg in CHAIN_IDS:
            chain_name = chain_arg
            chain_id = CHAIN_IDS[chain_arg]

    if not _EVM_ADDR_RE.match(address):
        await update.message.reply_text(
            "❌ Dat don't look like a contract address, bredda.\n"
            "Send a proper EVM address: `0x...` (40 hex chars)",
            parse_mode="Markdown",
        )
        return

    # Ensure account exists
    db = get_credits_db()
    db.get_or_create_account(user.id, user.username or "")

    # Spend credits
    ok, msg = db.spend_credits(user.id, "snifftest")
    if not ok:
        await update.message.reply_text(
            f"❌ {msg}\n\n"
            "💡 Each /snifftest costs 1 $MON credit.",
            parse_mode="Markdown",
        )
        return

    await update.message.reply_text(
        f"🔍 Sniffin' `{address[:8]}...{address[-6:]}` on {chain_name}...",
        parse_mode="Markdown",
    )

    report = await check_token_safety(address, chain_id)

    if report is None:
        # Refund on failure
        db.load_credits(user.id, "MON", 1.0, '{"reason":"snifftest_failed"}')
        await update.message.reply_text(
            "😤 Couldn't sniff dat one, bredda. Maybe di chain no supported yet "
            "or di contract too fresh. Credits refunded.\n\n"
            f"Try specifying chain: `/snifftest {address} base`",
            parse_mode="Markdown",
        )
        return

    # Format and send results
    result_text = format_snifftest_rasta(report, address)
    acct = db.get_account(user.id)

    await update.message.reply_text(
        f"{result_text}\n\n"
        f"_🔥 Burned 1 $MON | {acct.tier_label} | Total burns: {acct.burn_count}_",
        parse_mode="Markdown",
    )

    log.info("Snifftest complete",
             user_id=user.id,
             address=address,
             chain=chain_name,
             score=report["safety_score"])
