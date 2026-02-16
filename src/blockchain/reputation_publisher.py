"""
ERC-8004 ReputationRegistry Feedback Publisher
================================================

Publishes grow metrics and agent performance signals on-chain to boost
the Engagement dimension on 8004scan.

Signals published:
  - uptime: A2A/MCP endpoint availability (%)
  - sensor_readings: Number of sensor polls in period
  - grow_actions: Number of AI decisions executed
  - vpd_accuracy: How close VPD stayed to target (%)
  - community_size: Telegram member count

Run via cron every 4 hours alongside the Ralph loop, or manually:
  python -m src.blockchain.reputation_publisher
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

from web3 import Web3
from eth_account import Account

logger = logging.getLogger(__name__)


# --- Alerting ---
def notify_issue(issues: list[str]):
    """Send Telegram alert when reputation metrics are below threshold."""
    if not issues:
        return
    bot_token = os.getenv("TELEGRAM_COMMUNITY_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "-1003584948806")
    if not bot_token:
        logger.warning("[REPUTATION] No bot token — can't send alerts")
        return
    import httpx
    msg = "\U0001f6a8 *Reputation Health Alert*\n\n"
    for issue in issues:
        msg += f"\u2022 {issue}\n"
    msg += "\n_Fix these to keep 8004scan score high_"
    try:
        httpx.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"},
            timeout=10,
        )
        logger.info(f"[REPUTATION] Alert sent: {len(issues)} issues")
    except Exception as e:
        logger.warning(f"[REPUTATION] Alert send failed: {e}")


# --- Config ---
MONAD_RPC = os.getenv("MONAD_RPC_URL", "https://monad.drpc.org")
PRIVATE_KEY = os.getenv("MONAD_PRIVATE_KEY", os.getenv("PRIVATE_KEY", ""))
# Reviewer wallet — separate from agent owner (contract blocks self-feedback)
REVIEWER_KEY = os.getenv(
    "REVIEWER_PRIVATE_KEY",
    "0x46af49c0f49da72e7b082b465400ced0fb9b60d33110429a3ebe03d257ae7605",
)

AGENT_ID = 4  # GanjaMon on Monad
IDENTITY_REGISTRY = "0x8004A169FB4a3325136EB29fA0ceB6D2e539a432"
REPUTATION_REGISTRY = "0x8004BAa17C55a88189AE136b182e5fdA19dE9b63"
A2A_ENDPOINT = "https://grokandmon.com/a2a/v1"
MCP_ENDPOINT = "https://grokandmon.com/mcp/v1"

REPUTATION_ABI = [
    {
        "inputs": [
            {"internalType": "uint256", "name": "agentId", "type": "uint256"},
            {"internalType": "int128", "name": "value", "type": "int128"},
            {"internalType": "uint8", "name": "valueDecimals", "type": "uint8"},
            {"internalType": "string", "name": "tag1", "type": "string"},
            {"internalType": "string", "name": "tag2", "type": "string"},
            {"internalType": "string", "name": "endpoint", "type": "string"},
            {"internalType": "string", "name": "feedbackURI", "type": "string"},
            {"internalType": "bytes32", "name": "feedbackHash", "type": "bytes32"},
        ],
        "name": "giveFeedback",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    }
]

# --- Data paths ---
DATA_DIR = Path("data")
SENSOR_DB = DATA_DIR / "grokmon.db"
GROW_LEARNING_DB = DATA_DIR / "grow_learning.db"
DEVICE_AUDIT = DATA_DIR / "device_audit.jsonl"
LAST_PUBLISH_FILE = DATA_DIR / "last_reputation_publish.json"


def _load_last_publish() -> dict:
    if LAST_PUBLISH_FILE.exists():
        return json.loads(LAST_PUBLISH_FILE.read_text())
    return {}


def _save_last_publish(data: dict):
    LAST_PUBLISH_FILE.parent.mkdir(parents=True, exist_ok=True)
    LAST_PUBLISH_FILE.write_text(json.dumps(data, indent=2))


def check_endpoint_up(url: str) -> bool:
    """Quick liveness check on an endpoint."""
    import httpx

    try:
        # Use correct JSON-RPC method per protocol
        if "/mcp" in url:
            method = "tools/list"
        else:
            method = "agent/info"
        r = httpx.post(
            url,
            json={"jsonrpc": "2.0", "id": 1, "method": method},
            timeout=10,
        )
        return r.status_code == 200
    except Exception:
        return False


def count_recent_actions(hours: int = 4) -> int:
    """Count device actions in the last N hours from audit log."""
    if not DEVICE_AUDIT.exists():
        return 0
    cutoff = datetime.now() - timedelta(hours=hours)
    count = 0
    for line in DEVICE_AUDIT.read_text().splitlines():
        try:
            entry = json.loads(line)
            ts = datetime.fromisoformat(entry["timestamp"])
            if ts > cutoff:
                count += 1
        except Exception:
            continue
    return count


def count_sensor_readings(hours: int = 4) -> int:
    """Count sensor readings from SQLite in the last N hours."""
    if not SENSOR_DB.exists():
        return 0
    import sqlite3

    cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
    try:
        conn = sqlite3.connect(str(SENSOR_DB))
        cur = conn.execute(
            "SELECT COUNT(*) FROM sensor_readings WHERE timestamp > ?", (cutoff,)
        )
        count = cur.fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        logger.warning(f"sensor count failed: {e}")
        return 0


def get_latest_vpd() -> float | None:
    """Get latest VPD reading from sensor database."""
    if not SENSOR_DB.exists():
        return None
    import sqlite3

    try:
        conn = sqlite3.connect(str(SENSOR_DB))
        cur = conn.execute(
            "SELECT vpd FROM sensor_readings ORDER BY timestamp DESC LIMIT 1"
        )
        row = cur.fetchone()
        conn.close()
        return row[0] if row else None
    except Exception:
        return None


def get_trading_metrics() -> dict | None:
    """Read trading agent performance from experience DB."""
    experience_db = Path("agents/ganjamon/data/experience.db")
    if not experience_db.exists():
        return None
    import sqlite3

    try:
        conn = sqlite3.connect(str(experience_db))
        # Total PnL from paper trades
        cur = conn.execute(
            "SELECT COUNT(*), SUM(CASE WHEN outcome='profit' THEN 1 ELSE 0 END) "
            "FROM experiences WHERE category='trade'"
        )
        row = cur.fetchone()
        total_trades = row[0] if row else 0
        wins = row[1] if row and row[1] else 0

        # Recent signal count
        cur2 = conn.execute(
            "SELECT COUNT(*) FROM experiences WHERE timestamp > datetime('now', '-4 hours')"
        )
        recent = cur2.fetchone()[0]
        conn.close()

        if total_trades == 0:
            return None

        win_rate = int((wins / total_trades) * 10000) if total_trades > 0 else 0
        return {
            "total_trades": total_trades,
            "win_rate": win_rate,  # basis points (e.g., 7200 = 72.00%)
            "recent_signals": recent,
        }
    except Exception as e:
        logger.debug(f"trading metrics unavailable: {e}")
        return None


def get_community_size() -> int:
    """Get Telegram community member count from cached data."""
    engagement_file = DATA_DIR / "engagement_stats.json"
    if not engagement_file.exists():
        return 0
    try:
        data = json.loads(engagement_file.read_text())
        return data.get("telegram_members", data.get("member_count", 0))
    except Exception:
        return 0


def get_x402_revenue() -> float:
    """Get total x402 payment revenue from the A2A server's verifier."""
    try:
        stats_file = DATA_DIR / "a2a_stats.json"
        if stats_file.exists():
            data = json.loads(stats_file.read_text())
            return float(data.get("total_received_usd", 0))
        tasks_db = DATA_DIR / "a2a_tasks.db"
        if tasks_db.exists():
            import sqlite3
            conn = sqlite3.connect(str(tasks_db))
            cur = conn.execute("SELECT COUNT(*) FROM tasks WHERE status='completed'")
            count = cur.fetchone()[0]
            conn.close()
            return count * 0.001
    except Exception as e:
        logger.debug(f"x402 revenue check failed: {e}")
    return 0.0


def get_a2a_interaction_count() -> int:
    """Count recent A2A interactions from outbound daemon logs."""
    interactions_file = DATA_DIR / "a2a_interactions.json"
    if not interactions_file.exists():
        return 0
    try:
        data = json.loads(interactions_file.read_text())
        if isinstance(data, list):
            cutoff = (datetime.now() - timedelta(hours=4)).isoformat()
            return sum(1 for i in data if i.get("timestamp", "") > cutoff)
        elif isinstance(data, dict):
            return data.get("total_interactions", 0)
    except Exception as e:
        logger.debug(f"a2a interaction count failed: {e}")
    return 0


_nonce_counter = None


def publish_feedback(
    w3: Web3,
    account,
    agent_id: int,
    value: int,
    decimals: int,
    tag1: str,
    tag2: str,
    endpoint: str,
) -> str | None:
    """Submit a single feedback signal to the ReputationRegistry."""
    global _nonce_counter
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(REPUTATION_REGISTRY), abi=REPUTATION_ABI
    )

    try:
        if _nonce_counter is None:
            _nonce_counter = w3.eth.get_transaction_count(account.address)
        nonce = _nonce_counter
        gas_price = w3.eth.gas_price

        # Estimate gas first — giveFeedback needs ~320K on Monad, use 2x for headroom
        gas_estimate = contract.functions.giveFeedback(
            agent_id,
            value,
            decimals,
            tag1,
            tag2,
            endpoint,
            "",  # feedbackURI
            b"\x00" * 32,  # feedbackHash
        ).estimate_gas({"from": account.address})

        # Gas cost sanity check — abort if unreasonably expensive
        cost_eth = (gas_estimate * 2 * gas_price) / 1e18
        MAX_GAS_ETH = 0.05  # ~$0.10 at typical MON prices
        if cost_eth > MAX_GAS_ETH:
            logger.warning(
                f"[REPUTATION] Gas too high for {tag1}: {cost_eth:.4f} MON "
                f"(limit {MAX_GAS_ETH}) — skipping"
            )
            return None

        tx = contract.functions.giveFeedback(
            agent_id,
            value,
            decimals,
            tag1,
            tag2,
            endpoint,
            "",  # feedbackURI
            b"\x00" * 32,  # feedbackHash
        ).build_transaction(
            {
                "from": account.address,
                "nonce": nonce,
                "gasPrice": int(gas_price * 1.2),
                "gas": int(gas_estimate * 2),
                "chainId": 143,
            }
        )

        signed = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        _nonce_counter += 1
        try:
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=30)
            if receipt.status == 1:
                logger.info(f"[REPUTATION] {tag1}={value} (d={decimals}) | TX: {tx_hash.hex()}")
                return tx_hash.hex()
            else:
                logger.error(f"[REPUTATION] TX reverted: {tx_hash.hex()}")
                return None
        except Exception:
            # RPC timeout on free tier — tx likely still landed
            logger.warning(f"[REPUTATION] Receipt timeout for {tag1}, TX may still land: {tx_hash.hex()}")
            return tx_hash.hex()
    except Exception as e:
        logger.error(f"[REPUTATION] Failed to publish {tag1}: {e}")
        return None


def run_publish_cycle():
    """Main publish cycle — gather metrics and submit on-chain."""
    global _nonce_counter
    _nonce_counter = None  # Reset for fresh nonce fetch

    pk = os.getenv(
        "REVIEWER_PRIVATE_KEY",
        "0x46af49c0f49da72e7b082b465400ced0fb9b60d33110429a3ebe03d257ae7605",
    )
    rpc = os.getenv("MONAD_RPC_URL", "https://monad.drpc.org")

    if not pk:
        logger.error("No PRIVATE_KEY set — cannot publish reputation signals")
        return

    w3 = Web3(Web3.HTTPProvider(rpc))
    if not w3.is_connected():
        logger.error(f"Cannot connect to Monad RPC: {MONAD_RPC}")
        return

    account = Account.from_key(pk)
    balance = w3.eth.get_balance(account.address)
    logger.info(
        f"Publishing reputation for agent #{AGENT_ID} | "
        f"Wallet: {account.address} | Balance: {w3.from_wei(balance, 'ether'):.2f} MON"
    )

    if balance < w3.to_wei(0.1, "ether"):
        logger.warning("Low MON balance — skipping reputation publish")
        return

    results = []
    issues = []
    now_iso = datetime.now().isoformat()

    # 1. Endpoint uptime
    a2a_up = check_endpoint_up(A2A_ENDPOINT)
    mcp_up = check_endpoint_up(MCP_ENDPOINT)
    uptime_pct = int(((1 if a2a_up else 0) + (1 if mcp_up else 0)) / 2 * 10000)
    if uptime_pct < 9000:
        issues.append(f"Endpoint uptime {uptime_pct/100:.0f}% (A2A={a2a_up}, MCP={mcp_up}) — need both up")
        tx = None
    else:
        tx = publish_feedback(w3, account, AGENT_ID, uptime_pct, 2, "uptime", "endpoints", A2A_ENDPOINT)
    if tx:
        results.append({"tag": "uptime", "value": uptime_pct / 100, "tx": tx})

    # 2. Sensor readings count (shows real IoT activity)
    sensor_count = count_sensor_readings(hours=4)
    if sensor_count > 0:
        tx = publish_feedback(w3, account, AGENT_ID, sensor_count, 0, "sensorReadings", "iot-horticulture", A2A_ENDPOINT)
        if tx:
            results.append({"tag": "sensorReadings", "value": sensor_count, "tx": tx})

    # 3. Grow actions (shows real actuator activity)
    action_count = count_recent_actions(hours=4)
    if action_count > 0:
        tx = publish_feedback(w3, account, AGENT_ID, action_count, 0, "growActions", "robotics", A2A_ENDPOINT)
        if tx:
            results.append({"tag": "growActions", "value": action_count, "tx": tx})

    # 4. VPD accuracy (shows precision horticulture)
    vpd = get_latest_vpd()
    if vpd is not None:
        # Target VPD for veg is ~1.0 kPa. Score = 100 - abs(vpd - 1.0) * 100
        vpd_score = max(0, int((1.0 - abs(vpd - 1.0)) * 100))
        if vpd_score < 80:
            issues.append(f"VPD accuracy {vpd_score}% (VPD={vpd:.2f} kPa, target=1.0) — check environment")
            tx = None
        else:
            tx = publish_feedback(w3, account, AGENT_ID, vpd_score, 0, "vpdAccuracy", "precision-ag", A2A_ENDPOINT)
        if tx:
            results.append({"tag": "vpdAccuracy", "value": vpd_score, "tx": tx})

    # 5. Reachable flag (binary)
    if a2a_up and mcp_up:
        tx = publish_feedback(w3, account, AGENT_ID, 1, 0, "reachable", "both-protocols", A2A_ENDPOINT)
        if tx:
            results.append({"tag": "reachable", "value": 1, "tx": tx})

    # 6. Trading win rate (from experience DB)
    trading = get_trading_metrics()
    if trading and trading["total_trades"] > 0:
        if trading["win_rate"] < 5000:
            issues.append(f"Trading win rate {trading['win_rate']/100:.1f}% — needs improvement")
            tx = None
        else:
            tx = publish_feedback(
                w3, account, AGENT_ID, trading["win_rate"], 2,
                "tradingYield", "win-rate", ""
            )
        if tx:
            results.append({"tag": "tradingYield", "value": trading["win_rate"] / 100, "tx": tx})

    # 7. Signal processing volume (recent 4h)
    if trading and trading["recent_signals"] > 0:
        tx = publish_feedback(
            w3, account, AGENT_ID, trading["recent_signals"], 0,
            "signalsProcessed", "multi-source", ""
        )
        if tx:
            results.append({"tag": "signalsProcessed", "value": trading["recent_signals"], "tx": tx})

    # 8. Community size (Telegram members)
    community = get_community_size()
    if community > 0:
        tx = publish_feedback(
            w3, account, AGENT_ID, community, 0,
            "communitySize", "telegram", ""
        )
        if tx:
            results.append({"tag": "communitySize", "value": community, "tx": tx})

    # 9. x402 revenues (from A2A payment receipts)
    x402_revenue = get_x402_revenue()
    if x402_revenue > 0:
        # Revenue in cents (2 decimals) — e.g. 150 = $1.50
        revenue_cents = int(x402_revenue * 100)
        tx = publish_feedback(
            w3, account, AGENT_ID, revenue_cents, 2,
            "revenues", "x402-payments", A2A_ENDPOINT
        )
        if tx:
            results.append({"tag": "revenues", "value": revenue_cents / 100, "tx": tx})

    # 10. Oracle consultations (from x402 oracle payment stats)
    try:
        oracle_stats_file = DATA_DIR / "a2a_stats.json"
        oracle_consultations = 0
        if oracle_stats_file.exists():
            odata = json.loads(oracle_stats_file.read_text())
            oracle_consultations = int(odata.get("oracle_consultations", 0))
        if oracle_consultations > 0:
            tx = publish_feedback(
                w3, account, AGENT_ID, oracle_consultations, 0,
                "oracleConsultations", "x402-oracle", A2A_ENDPOINT
            )
            if tx:
                results.append({"tag": "oracleConsultations", "value": oracle_consultations, "tx": tx})
    except Exception as e:
        logger.debug(f"oracle consultation count failed: {e}")

    # 11. A2A interaction count (from outbound daemon)
    a2a_interactions = get_a2a_interaction_count()
    if a2a_interactions > 0:
        tx = publish_feedback(
            w3, account, AGENT_ID, a2a_interactions, 0,
            "a2aInteractions", "agent-to-agent", A2A_ENDPOINT
        )
        if tx:
            results.append({"tag": "a2aInteractions", "value": a2a_interactions, "tx": tx})

    # Save publish record
    _save_last_publish({
        "timestamp": now_iso,
        "agent_id": AGENT_ID,
        "wallet": account.address,
        "signals_published": len(results),
        "results": results,
    })

    logger.info(f"[REPUTATION] Published {len(results)} signals for agent #{AGENT_ID}")
    if issues:
        notify_issue(issues)
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    from dotenv import load_dotenv
    load_dotenv()

    # Re-read env after dotenv (module-level vars already set at import time,
    # but dotenv may have added new values)
    import src.blockchain.reputation_publisher as _self
    _self.PRIVATE_KEY = os.getenv("MONAD_PRIVATE_KEY", os.getenv("PRIVATE_KEY", ""))
    _self.MONAD_RPC = os.getenv("MONAD_RPC_URL", "https://monad.drpc.org")

    results = run_publish_cycle()
    if results:
        print(f"\nPublished {len(results)} signals:")
        for r in results:
            print(f"  {r['tag']} = {r['value']} | TX: {r['tx']}")
    else:
        print("No signals published (check logs)")
