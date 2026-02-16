"""
Token Sink Credit System
========================

Manages user accounts, credit balances ($MON and $GANJA),
burn history, and community tier progression.

Credits are loaded by burning $MON on-chain via /deposit <tx_hash>.
Credits are spent on agent services: /irie, /askmon, etc.
New accounts get a few free trial uses (no fake credits).

Burn tiers reward USAGE, not holding:
  🌱 Seedling   (0-99 burns)
  🌿 Sprout     (100-499 burns)
  🌳 Tree       (500-1999 burns)
  👑 OG Grower  (2000+ burns)
"""

import json
import sqlite3
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

import structlog

log = structlog.get_logger("credits")

DB_PATH = Path("data/credits.db")

# Service costs in $MON tokens.
# 4200 $MON ≈ $0.15 at current price. Cheap enough to use,
# but enough to dent supply if it catches on.
# Phase 2: Add $GANJA sinks when nad.fun supply exists.
SERVICE_COSTS = {
    "irie": {"token": "MON", "credits": 4200.0},
    "askmon": {"token": "MON", "credits": 4200.0},
    "rollup": {"token": "MON", "credits": 12600.0},    # 3x base
    "passthemic": {"token": "MON", "credits": 21000.0}, # 5x base
    "rastasays": {"token": "MON", "credits": 4200.0},
    "art": {"token": "MON", "credits": 8400.0},         # 2x base — AI art gen
}

# Free trial uses for new accounts — lets people try before buying.
# These are real free uses, NOT fake credits. No $MON is pretended.
FREE_TRIAL_USES = 3


class BurnTier(Enum):
    SEEDLING = ("🌱 Seedling", 0)
    SPROUT = ("🌿 Sprout", 100)
    TREE = ("🌳 Tree", 500)
    OG_GROWER = ("👑 OG Grower", 2000)

    def __init__(self, label: str, threshold: int):
        self.label = label
        self.threshold = threshold


@dataclass
class Account:
    id: int = 0
    telegram_user_id: int = 0
    telegram_username: str = ""
    wallet_address: str = ""
    wallet_verified: bool = False
    mon_credits: float = 0.0
    ganja_credits: float = 0.0
    total_mon_burned: float = 0.0
    total_ganja_burned: float = 0.0
    burn_count: int = 0
    free_uses: int = FREE_TRIAL_USES
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    @property
    def tier(self) -> BurnTier:
        for t in reversed(BurnTier):
            if self.burn_count >= t.threshold:
                return t
        return BurnTier.SEEDLING

    @property
    def tier_label(self) -> str:
        return self.tier.label

    @property
    def next_tier(self) -> Optional[BurnTier]:
        tiers = list(BurnTier)
        idx = tiers.index(self.tier)
        if idx < len(tiers) - 1:
            return tiers[idx + 1]
        return None

    @property
    def burns_to_next_tier(self) -> int:
        nxt = self.next_tier
        if nxt is None:
            return 0
        return max(0, nxt.threshold - self.burn_count)


@dataclass
class Transaction:
    id: int = 0
    account_id: int = 0
    token: str = ""        # 'MON' or 'GANJA'
    amount: float = 0.0
    tx_type: str = ""      # 'load', 'burn', 'refund', 'trial'
    service: str = ""      # 'irie', 'snifftest', etc.
    details: str = ""      # JSON metadata
    created_at: float = field(default_factory=time.time)


class CreditsDB:
    """SQLite credit ledger for token sink services."""

    def __init__(self):
        self._db: Optional[sqlite3.Connection] = None

    def _ensure_db(self) -> sqlite3.Connection:
        if self._db is not None:
            return self._db
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(str(DB_PATH))
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA foreign_keys=ON")
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_user_id INTEGER UNIQUE NOT NULL,
                telegram_username TEXT DEFAULT '',
                wallet_address TEXT DEFAULT '',
                wallet_verified INTEGER DEFAULT 0,
                mon_credits REAL DEFAULT 0.0,
                ganja_credits REAL DEFAULT 0.0,
                total_mon_burned REAL DEFAULT 0.0,
                total_ganja_burned REAL DEFAULT 0.0,
                burn_count INTEGER DEFAULT 0,
                free_uses INTEGER DEFAULT 3,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
        """)
        # Migration: add free_uses column to existing DBs
        try:
            self._db.execute("ALTER TABLE accounts ADD COLUMN free_uses INTEGER DEFAULT 3")
            self._db.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                token TEXT NOT NULL,
                amount REAL NOT NULL,
                tx_type TEXT NOT NULL,
                service TEXT DEFAULT '',
                details TEXT DEFAULT '',
                created_at REAL NOT NULL,
                FOREIGN KEY (account_id) REFERENCES accounts(id)
            )
        """)
        self._db.execute("""
            CREATE INDEX IF NOT EXISTS idx_tx_account
            ON transactions(account_id)
        """)
        self._db.execute("""
            CREATE INDEX IF NOT EXISTS idx_tx_service
            ON transactions(service)
        """)
        self._db.commit()
        return self._db

    # ── Account operations ──────────────────────────────────────

    def get_or_create_account(
        self,
        telegram_user_id: int,
        telegram_username: str = "",
    ) -> Account:
        db = self._ensure_db()
        row = db.execute(
            "SELECT * FROM accounts WHERE telegram_user_id = ?",
            (telegram_user_id,),
        ).fetchone()
        if row:
            return self._row_to_account(row)

        now = time.time()
        cursor = db.execute(
            """INSERT INTO accounts
               (telegram_user_id, telegram_username,
                mon_credits, ganja_credits, free_uses, created_at, updated_at)
               VALUES (?, ?, 0, 0, ?, ?, ?)""",
            (telegram_user_id, telegram_username, FREE_TRIAL_USES, now, now),
        )
        db.commit()

        log.info("New account created",
                 user_id=telegram_user_id,
                 username=telegram_username,
                 free_uses=FREE_TRIAL_USES)

        return self.get_account(telegram_user_id)

    def get_account(self, telegram_user_id: int) -> Optional[Account]:
        db = self._ensure_db()
        row = db.execute(
            "SELECT * FROM accounts WHERE telegram_user_id = ?",
            (telegram_user_id,),
        ).fetchone()
        return self._row_to_account(row) if row else None

    def link_wallet(self, telegram_user_id: int, wallet_address: str) -> Account:
        db = self._ensure_db()
        now = time.time()
        db.execute(
            """UPDATE accounts
               SET wallet_address = ?, wallet_verified = 0, updated_at = ?
               WHERE telegram_user_id = ?""",
            (wallet_address, now, telegram_user_id),
        )
        db.commit()
        return self.get_account(telegram_user_id)

    def verify_wallet(self, telegram_user_id: int) -> Account:
        db = self._ensure_db()
        now = time.time()
        db.execute(
            """UPDATE accounts
               SET wallet_verified = 1, updated_at = ?
               WHERE telegram_user_id = ?""",
            (now, telegram_user_id),
        )
        db.commit()
        return self.get_account(telegram_user_id)

    # ── Credit operations ───────────────────────────────────────

    def load_credits(
        self,
        telegram_user_id: int,
        token: str,
        amount: float,
        details: str = "",
    ) -> Account:
        db = self._ensure_db()
        now = time.time()
        col = "mon_credits" if token == "MON" else "ganja_credits"
        db.execute(
            f"UPDATE accounts SET {col} = {col} + ?, updated_at = ? WHERE telegram_user_id = ?",
            (amount, now, telegram_user_id),
        )
        acct = self.get_account(telegram_user_id)
        db.execute(
            """INSERT INTO transactions
               (account_id, token, amount, tx_type, service, details, created_at)
               VALUES (?, ?, ?, 'load', '', ?, ?)""",
            (acct.id, token, amount, details, now),
        )
        db.commit()
        log.info("Credits loaded", user_id=telegram_user_id, token=token, amount=amount)
        return self.get_account(telegram_user_id)

    def spend_credits(
        self,
        telegram_user_id: int,
        service: str,
        details: str = "",
    ) -> tuple[bool, str]:
        """Attempt to spend credits for a service.

        Returns (success, message).
        Checks free trial uses first, then real $MON credits.
        """
        cost_info = SERVICE_COSTS.get(service)
        if not cost_info:
            return False, f"Unknown service: {service}"

        token = cost_info["token"]
        amount = cost_info["credits"]
        acct = self.get_account(telegram_user_id)
        if acct is None:
            return False, "No account found. Send any command to create one."

        # Check if user has free trial uses remaining
        if acct.free_uses > 0:
            db = self._ensure_db()
            now = time.time()
            db.execute(
                """UPDATE accounts
                   SET free_uses = free_uses - 1,
                       burn_count = burn_count + 1,
                       updated_at = ?
                   WHERE telegram_user_id = ?""",
                (now, telegram_user_id),
            )
            db.execute(
                """INSERT INTO transactions
                   (account_id, token, amount, tx_type, service, details, created_at)
                   VALUES (?, ?, 0, 'trial', ?, ?, ?)""",
                (acct.id, token, service, details, now),
            )
            db.commit()
            remaining = acct.free_uses - 1
            log.info("Free trial use",
                     user_id=telegram_user_id, service=service,
                     remaining=remaining)
            return True, f"⚡ Free trial ({remaining} left)"

        # Paid service — check balance
        balance = acct.mon_credits if token == "MON" else acct.ganja_credits
        if balance < amount:
            return False, (
                f"Not enough $MON credits! "
                f"Need {amount:,.0f}, have {balance:,.0f}.\n"
                f"Burn $MON to load credits: /deposit"
            )

        db = self._ensure_db()
        now = time.time()
        col = "mon_credits" if token == "MON" else "ganja_credits"
        burn_col = "total_mon_burned" if token == "MON" else "total_ganja_burned"

        db.execute(
            f"""UPDATE accounts
                SET {col} = {col} - ?,
                    {burn_col} = {burn_col} + ?,
                    burn_count = burn_count + 1,
                    updated_at = ?
                WHERE telegram_user_id = ?""",
            (amount, amount, now, telegram_user_id),
        )
        db.execute(
            """INSERT INTO transactions
               (account_id, token, amount, tx_type, service, details, created_at)
               VALUES (?, ?, ?, 'burn', ?, ?, ?)""",
            (acct.id, token, -amount, service, details, now),
        )
        db.commit()

        updated = self.get_account(telegram_user_id)
        log.info("Credits burned",
                 user_id=telegram_user_id,
                 service=service,
                 token=token,
                 amount=amount,
                 burn_count=updated.burn_count)
        return True, f"🔥 Burned {amount:,.0f} ${token} for {service}"

    # ── Stats & leaderboard ─────────────────────────────────────

    def get_burn_leaderboard(self, limit: int = 10) -> list[Account]:
        db = self._ensure_db()
        rows = db.execute(
            "SELECT * FROM accounts ORDER BY burn_count DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [self._row_to_account(r) for r in rows]

    def get_total_burns(self) -> dict:
        db = self._ensure_db()
        row = db.execute("""
            SELECT
                COALESCE(SUM(total_mon_burned), 0),
                COALESCE(SUM(total_ganja_burned), 0),
                COALESCE(SUM(burn_count), 0),
                COUNT(*)
            FROM accounts
        """).fetchone()
        return {
            "total_mon_burned": row[0],
            "total_ganja_burned": row[1],
            "total_burns": row[2],
            "total_accounts": row[3],
        }

    def get_recent_burns(self, limit: int = 10) -> list[Transaction]:
        db = self._ensure_db()
        rows = db.execute(
            """SELECT t.*, a.telegram_username
               FROM transactions t
               JOIN accounts a ON t.account_id = a.id
               WHERE t.tx_type = 'burn'
               ORDER BY t.created_at DESC
               LIMIT ?""",
            (limit,),
        ).fetchall()
        txs = []
        for r in rows:
            tx = Transaction(
                id=r[0], account_id=r[1], token=r[2], amount=r[3],
                tx_type=r[4], service=r[5], details=r[6], created_at=r[7],
            )
            txs.append(tx)
        return txs

    # ── Internal helpers ────────────────────────────────────────

    def _row_to_account(self, row: tuple) -> Account:
        return Account(
            id=row[0],
            telegram_user_id=row[1],
            telegram_username=row[2] or "",
            wallet_address=row[3] or "",
            wallet_verified=bool(row[4]),
            mon_credits=row[5],
            ganja_credits=row[6],
            total_mon_burned=row[7],
            total_ganja_burned=row[8],
            burn_count=row[9],
            free_uses=row[10] if len(row) > 12 else 0,
            created_at=row[11] if len(row) > 12 else row[10],
            updated_at=row[12] if len(row) > 12 else row[11],
        )


# ── Singleton ───────────────────────────────────────────────────

_instance: Optional[CreditsDB] = None


def get_credits_db() -> CreditsDB:
    global _instance
    if _instance is None:
        _instance = CreditsDB()
    return _instance
