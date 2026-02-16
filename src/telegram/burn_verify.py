"""
On-Chain Burn Verification
===========================

Verifies $MON token burns on Monad by checking transaction receipts.

Flow:
1. User sends $MON to burn address (0x...dEaD) on Monad
2. User sends /deposit <tx_hash> in Telegram
3. Bot fetches tx receipt from Monad RPC
4. Decodes ERC-20 Transfer event, verifies:
   - Token is $MON contract
   - Recipient is the burn address
   - Tx hasn't been claimed before
5. Credits the user's account with the burned amount
"""

import json
import os
import sqlite3
import time
from typing import Optional

import httpx
import structlog
from telegram import Update
from telegram.ext import ContextTypes

from src.telegram.credits import get_credits_db

log = structlog.get_logger("burn_verify")

# ── Constants ───────────────────────────────────────────────────

MON_CONTRACT = "0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b"
BURN_ADDRESS = "0x000000000000000000000000000000000000dEaD"
MONAD_RPC = os.getenv("MONAD_RPC_URL", "https://rpc.monad.xyz")

# ERC-20 Transfer event topic: Transfer(address,address,uint256)
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

# Minimum deposit: 4200 $MON (one service use)
MIN_DEPOSIT = 4200.0

# $MON has 18 decimals
MON_DECIMALS = 18


# ── RPC helpers ─────────────────────────────────────────────────

async def get_tx_receipt(tx_hash: str) -> Optional[dict]:
    """Fetch transaction receipt from Monad RPC."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                MONAD_RPC,
                json={
                    "jsonrpc": "2.0",
                    "method": "eth_getTransactionReceipt",
                    "params": [tx_hash],
                    "id": 1,
                },
            )
            data = resp.json()
            return data.get("result")
    except Exception as e:
        log.warning("RPC receipt fetch failed", tx_hash=tx_hash, error=str(e))
        return None


async def get_tx(tx_hash: str) -> Optional[dict]:
    """Fetch raw transaction data (for native MON transfers)."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                MONAD_RPC,
                json={
                    "jsonrpc": "2.0",
                    "method": "eth_getTransactionByHash",
                    "params": [tx_hash],
                    "id": 1,
                },
            )
            data = resp.json()
            return data.get("result")
    except Exception as e:
        log.warning("RPC tx fetch failed", tx_hash=tx_hash, error=str(e))
        return None


def decode_erc20_transfer(receipt: dict) -> Optional[dict]:
    """Find and decode ERC-20 Transfer event from tx receipt.

    Returns dict with 'token', 'from', 'to', 'amount' or None.
    """
    for log_entry in receipt.get("logs", []):
        topics = log_entry.get("topics", [])
        if len(topics) < 3:
            continue
        if topics[0].lower() != TRANSFER_TOPIC:
            continue

        token_address = log_entry.get("address", "").lower()
        from_addr = "0x" + topics[1][-40:]
        to_addr = "0x" + topics[2][-40:]
        raw_amount = int(log_entry.get("data", "0x0"), 16)
        amount = raw_amount / (10 ** MON_DECIMALS)

        return {
            "token": token_address,
            "from": from_addr.lower(),
            "to": to_addr.lower(),
            "amount": amount,
        }

    return None


# ── Claimed tx tracking (prevent double-spend) ─────────────────

def _ensure_claims_table(db: sqlite3.Connection):
    """Create claims table if it doesn't exist."""
    db.execute("""
        CREATE TABLE IF NOT EXISTS claimed_txs (
            tx_hash TEXT PRIMARY KEY,
            telegram_user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            claimed_at REAL NOT NULL
        )
    """)
    db.commit()


def is_tx_claimed(db: sqlite3.Connection, tx_hash: str) -> bool:
    """Check if a tx hash has already been claimed."""
    _ensure_claims_table(db)
    row = db.execute(
        "SELECT 1 FROM claimed_txs WHERE tx_hash = ?",
        (tx_hash.lower(),),
    ).fetchone()
    return row is not None


def record_claim(db: sqlite3.Connection, tx_hash: str, user_id: int, amount: float):
    """Record a claimed tx to prevent double-spend."""
    _ensure_claims_table(db)
    db.execute(
        "INSERT INTO claimed_txs (tx_hash, telegram_user_id, amount, claimed_at) VALUES (?, ?, ?, ?)",
        (tx_hash.lower(), user_id, amount, time.time()),
    )
    db.commit()


# ── Core verification ───────────────────────────────────────────

async def verify_burn(tx_hash: str) -> dict:
    """Verify an on-chain $MON burn transaction.

    Returns:
        {
            "valid": bool,
            "error": str or None,
            "amount": float,        # $MON burned
            "from": str,            # sender wallet
            "tx_hash": str,
        }
    """
    result = {"valid": False, "error": None, "amount": 0.0, "from": "", "tx_hash": tx_hash}

    # Normalize tx hash
    if not tx_hash.startswith("0x"):
        tx_hash = "0x" + tx_hash
    if len(tx_hash) != 66:
        result["error"] = "Invalid transaction hash format"
        return result

    # Fetch receipt
    receipt = await get_tx_receipt(tx_hash)
    if not receipt:
        result["error"] = "Transaction not found on Monad. Make sure it's confirmed."
        return result

    # Check tx succeeded
    status = receipt.get("status", "0x0")
    if status != "0x1":
        result["error"] = "Transaction failed on-chain"
        return result

    # Look for ERC-20 Transfer to burn address
    transfer = decode_erc20_transfer(receipt)
    if not transfer:
        result["error"] = "No token transfer found in this transaction"
        return result

    # Verify it's $MON
    if transfer["token"] != MON_CONTRACT.lower():
        result["error"] = (
            f"Wrong token. Expected $MON (`{MON_CONTRACT[:10]}...`), "
            f"got `{transfer['token'][:10]}...`"
        )
        return result

    # Verify recipient is burn address
    if transfer["to"] != BURN_ADDRESS.lower():
        result["error"] = (
            f"Not a burn. Tokens were sent to `{transfer['to'][:10]}...`, "
            f"not the burn address `{BURN_ADDRESS[:10]}...`"
        )
        return result

    # Check minimum amount
    if transfer["amount"] < MIN_DEPOSIT:
        result["error"] = (
            f"Below minimum. Burned {transfer['amount']:,.0f} $MON, "
            f"minimum is {MIN_DEPOSIT:,.0f}."
        )
        return result

    result["valid"] = True
    result["amount"] = transfer["amount"]
    result["from"] = transfer["from"]
    return result


# ── Telegram command handler ────────────────────────────────────

async def handle_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /deposit <tx_hash> — verify on-chain burn and credit account."""
    if not update.message:
        return

    user = update.message.from_user
    if not user:
        return

    tx_hash = " ".join(context.args).strip() if context.args else ""

    if not tx_hash:
        await update.message.reply_text(
            "🔥 *Deposit $MON Credits*\n\n"
            "Burn $MON on-chain to load credits for bot services.\n\n"
            "*How it works:*\n"
            f"1. Send $MON to the burn address on Monad:\n"
            f"   `{BURN_ADDRESS}`\n"
            f"2. Copy the transaction hash\n"
            f"3. Send: `/deposit 0xYourTxHash`\n\n"
            f"*Token:* `{MON_CONTRACT}`\n"
            f"*Min deposit:* {MIN_DEPOSIT:,.0f} $MON\n"
            f"*1 use =* 4,200 $MON (~$0.15)\n\n"
            "Your burned $MON becomes credits 1:1. "
            "Burned tokens are gone forever — real deflation.",
            parse_mode="Markdown",
        )
        return

    # Ensure account
    db = get_credits_db()
    db.get_or_create_account(user.id, user.username or "")

    await update.message.reply_text("🔍 Verifying burn on Monad...")

    # Check double-claim first
    credits_db = db._ensure_db()
    if is_tx_claimed(credits_db, tx_hash):
        await update.message.reply_text(
            "❌ This transaction has already been claimed.",
            parse_mode="Markdown",
        )
        return

    # Verify on-chain
    result = await verify_burn(tx_hash)

    if not result["valid"]:
        await update.message.reply_text(
            f"❌ {result['error']}",
            parse_mode="Markdown",
        )
        return

    amount = result["amount"]

    # Record claim and load credits
    record_claim(credits_db, tx_hash, user.id, amount)
    db.load_credits(
        user.id,
        "MON",
        amount,
        json.dumps({"tx_hash": tx_hash, "from": result["from"], "type": "burn_deposit"}),
    )

    acct = db.get_account(user.id)
    uses = int(amount // 4200)

    await update.message.reply_text(
        f"🔥 *Burn Verified!*\n\n"
        f"Burned: *{amount:,.0f} $MON*\n"
        f"Credits loaded: *{amount:,.0f}*\n"
        f"That's ~{uses} service uses\n\n"
        f"💰 New balance: *{acct.mon_credits:,.0f} $MON*\n"
        f"{acct.tier_label} | Total burns: {acct.burn_count}\n\n"
        f"Try /irie or /askmon to use your credits!",
        parse_mode="Markdown",
    )

    log.info("Burn deposit verified",
             user_id=user.id,
             amount=amount,
             tx_hash=tx_hash,
             from_addr=result["from"])
