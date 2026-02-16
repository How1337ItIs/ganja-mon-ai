"""
Monad Blockchain Integration
============================

Integration with Monad L1 and LFJ Token Mill launchpad.
Mirrors SOLTOMATO's pump.fun integration for $SOL token.

Monad is an EVM-compatible L1 with high throughput.
LFJ Token Mill is the token launchpad (like pump.fun on Solana).
"""

import os
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
import json

import httpx


@dataclass
class TokenMetrics:
    """$MON token metrics"""
    # Core metrics
    address: str = ""
    name: str = "Mon The Cannabis"
    symbol: str = "MON"

    # Price data
    price_usd: float = 0.0
    price_change_24h: float = 0.0
    market_cap: float = 0.0
    market_cap_ath: float = 0.0

    # Trading data
    volume_24h: float = 0.0
    holders: int = 0
    total_supply: int = 1_000_000_000  # 1B tokens

    # Timestamps
    created_at: Optional[datetime] = None
    last_trade_at: Optional[datetime] = None
    last_updated: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to API-friendly dict"""
        # Calculate derived metrics
        age_str = "Unknown"
        if self.created_at:
            age = datetime.utcnow() - self.created_at
            if age.days > 0:
                age_str = f"{age.days}d"
            else:
                hours = age.seconds // 3600
                age_str = f"{hours}h"

        # Use pre-computed last trade string if available
        last_trade_str = getattr(self, '_last_trade_str', None)
        if not last_trade_str:
            if self.last_trade_at:
                since_trade = datetime.utcnow() - self.last_trade_at
                if since_trade.days > 0:
                    last_trade_str = f"{since_trade.days}d ago"
                elif since_trade.seconds > 3600:
                    last_trade_str = f"{since_trade.seconds // 3600}h ago"
                elif since_trade.seconds > 60:
                    last_trade_str = f"{since_trade.seconds // 60}m ago"
                else:
                    last_trade_str = "Just now"
            else:
                last_trade_str = "Unknown"

        ath_percent = 0
        if self.market_cap_ath > 0:
            ath_percent = round((self.market_cap / self.market_cap_ath) * 100, 1)

        return {
            "address": self.address,
            "name": self.name,
            "symbol": self.symbol,
            "price_usd": self.price_usd,
            "price_change_24h": self.price_change_24h,
            "market_cap": self.market_cap,
            "market_cap_formatted": self._format_number(self.market_cap),
            "market_cap_ath": self.market_cap_ath,
            "market_cap_ath_formatted": self._format_number(self.market_cap_ath),
            "ath_percent": ath_percent,
            "volume_24h": self.volume_24h,
            "volume_24h_formatted": self._format_number(self.volume_24h),
            "holders": self.holders,
            "total_supply": self.total_supply,
            "token_age": age_str,
            "last_trade": last_trade_str,
            "last_updated": self.last_updated.isoformat(),
        }

    @staticmethod
    def _format_number(n: float) -> str:
        """Format large numbers for display"""
        if n >= 1_000_000_000:
            return f"${n / 1_000_000_000:.2f}B"
        elif n >= 1_000_000:
            return f"${n / 1_000_000:.2f}M"
        elif n >= 1_000:
            return f"${n / 1_000:.2f}K"
        else:
            return f"${n:.2f}"


@dataclass
class TradeEvent:
    """A token trade event"""
    tx_hash: str
    type: str  # "buy" or "sell"
    amount_tokens: float
    amount_usd: float
    trader: str
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tx_hash": self.tx_hash,
            "type": self.type,
            "amount_tokens": self.amount_tokens,
            "amount_usd": self.amount_usd,
            "trader": self.trader[:8] + "...",
            "timestamp": self.timestamp.isoformat(),
        }


class LFJTokenMillClient:
    """
    Client for $MON token metrics via DexScreener API.

    DexScreener aggregates DEX data across chains including Monad.
    SocialScan provides holder count data.
    """

    # DexScreener API for token data
    DEXSCREENER_API = "https://api.dexscreener.com/latest/dex/tokens"

    # SocialScan API for holder count (Monad mainnet)
    SOCIALSCAN_API = "https://api.socialscan.io/rest/monad-mainnet/v1/explorer/token"

    # $MON token address on Monad
    MON_TOKEN_ADDRESS = "0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b"

    # File to persist ATH across restarts
    ATH_FILE = "data/mon_ath.json"

    def __init__(self, token_address: Optional[str] = None):
        self.token_address = token_address or os.getenv("MON_TOKEN_ADDRESS", self.MON_TOKEN_ADDRESS)
        self._cache: Optional[TokenMetrics] = None
        self._cache_time: Optional[datetime] = None
        self._cache_ttl = timedelta(seconds=30)
        self._market_cap_ath: float = self._load_ath()
        self._holder_count: int = 0  # Cached holder count from SocialScan

    def _load_ath(self) -> float:
        """Load ATH from persistent storage"""
        try:
            with open(self.ATH_FILE, 'r') as f:
                data = json.load(f)
                return float(data.get('ath', 0))
        except:
            return 0.0

    def _save_ath(self, ath: float) -> None:
        """Save ATH to persistent storage"""
        try:
            os.makedirs(os.path.dirname(self.ATH_FILE), exist_ok=True)
            with open(self.ATH_FILE, 'w') as f:
                json.dump({'ath': ath, 'updated': datetime.utcnow().isoformat()}, f)
        except:
            pass

    def _estimate_last_trade(self, txns: dict) -> str:
        """Estimate last trade time from transaction counts"""
        m5 = txns.get('m5', {})
        h1 = txns.get('h1', {})
        h6 = txns.get('h6', {})
        h24 = txns.get('h24', {})

        if (m5.get('buys', 0) + m5.get('sells', 0)) > 0:
            return "< 5m ago"
        elif (h1.get('buys', 0) + h1.get('sells', 0)) > 0:
            return "< 1h ago"
        elif (h6.get('buys', 0) + h6.get('sells', 0)) > 0:
            return "< 6h ago"
        elif (h24.get('buys', 0) + h24.get('sells', 0)) > 0:
            return "< 24h ago"
        else:
            return "> 24h ago"

    async def _fetch_holder_count(self) -> int:
        """Fetch holder count from SocialScan API"""
        if not self.token_address:
            return 0

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.SOCIALSCAN_API}/{self.token_address}/profile"
                )
                if response.status_code == 200:
                    data = response.json()
                    holders = data.get("total_holders", 0)
                    if holders:
                        self._holder_count = int(holders)
                    return self._holder_count
        except Exception as e:
            print(f"Failed to fetch holder count from SocialScan: {e}")

        return self._holder_count  # Return cached value on error

    async def get_token_metrics(self, force_refresh: bool = False) -> TokenMetrics:
        """
        Fetch token metrics from LFJ Token Mill.

        Returns cached data if available and fresh.
        """
        # Check cache
        if not force_refresh and self._cache and self._cache_time:
            if datetime.utcnow() - self._cache_time < self._cache_ttl:
                return self._cache

        # Fetch fresh data
        try:
            metrics = await self._fetch_metrics()
        except Exception as e:
            print(f"Failed to fetch LFJ Token Mill metrics: {e}")
            # Return mock data if API fails
            metrics = self._mock_metrics()

        self._cache = metrics
        self._cache_time = datetime.utcnow()
        return metrics

    async def _fetch_metrics(self) -> TokenMetrics:
        """Fetch metrics from DexScreener API and holder count from SocialScan"""

        if not self.token_address:
            return self._mock_metrics()

        # Fetch holder count from SocialScan (in parallel with DexScreener would be ideal)
        holder_count = await self._fetch_holder_count()

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.DEXSCREENER_API}/{self.token_address}"
            )
            response.raise_for_status()
            data = response.json()

            # Get the first pair (most liquid)
            pairs = data.get("pairs", [])
            if not pairs:
                return self._mock_metrics()

            pair = pairs[0]
            base_token = pair.get("baseToken", {})
            price_change = pair.get("priceChange", {})
            volume = pair.get("volume", {})
            txns = pair.get("txns", {})

            market_cap = float(pair.get("marketCap", 0) or 0)

            # Track ATH - persist to file
            if market_cap > self._market_cap_ath:
                self._market_cap_ath = market_cap
                self._save_ath(market_cap)

            # Parse creation timestamp
            created_ts = pair.get("pairCreatedAt")
            created_at = datetime.fromtimestamp(created_ts / 1000) if created_ts else None

            # Estimate last trade from txn counts
            last_trade_str = self._estimate_last_trade(txns)

            metrics = TokenMetrics(
                address=self.token_address,
                name=base_token.get("name", "MON"),
                symbol=base_token.get("symbol", "MON"),
                price_usd=float(pair.get("priceUsd", 0) or 0),
                price_change_24h=float(price_change.get("h24", 0) or 0),
                market_cap=market_cap,
                market_cap_ath=self._market_cap_ath if self._market_cap_ath > 0 else market_cap,
                volume_24h=float(volume.get("h24", 0) or 0),
                holders=holder_count,  # From SocialScan
                created_at=created_at,
                last_trade_at=None,  # We'll override in to_dict
            )
            # Store last trade string for display
            metrics._last_trade_str = last_trade_str
            return metrics

    def _mock_metrics(self) -> TokenMetrics:
        """Return pre-launch placeholder data"""
        return TokenMetrics(
            address="TBD - Launching on LFJ Token Mill",
            name="Mon The Cannabis",
            symbol="MON",
            price_usd=0.0,
            price_change_24h=0.0,
            market_cap=0.0,
            market_cap_ath=0.0,
            volume_24h=0.0,
            holders=0,
            total_supply=1_000_000_000,
            created_at=None,
            last_trade_at=None,
        )

    async def get_recent_trades(self, limit: int = 10) -> List[TradeEvent]:
        """Get recent trade events"""
        try:
            return await self._fetch_trades(limit)
        except Exception:
            return self._mock_trades(limit)

    async def _fetch_trades(self, limit: int) -> List[TradeEvent]:
        """Fetch trades from API"""
        if not self.token_address:
            return self._mock_trades(limit)

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/token/{self.token_address}/trades",
                params={"limit": limit}
            )
            response.raise_for_status()
            data = response.json()

            return [
                TradeEvent(
                    tx_hash=t["tx_hash"],
                    type=t["type"],
                    amount_tokens=t["amount_tokens"],
                    amount_usd=t["amount_usd"],
                    trader=t["trader"],
                    timestamp=datetime.fromisoformat(t["timestamp"])
                )
                for t in data.get("trades", [])
            ]

    def _mock_trades(self, limit: int) -> List[TradeEvent]:
        """Return empty list when no real trade data available"""
        # No fake data - return empty list
        return []


class MonadClient:
    """
    Direct Monad blockchain client.

    For on-chain operations like checking balances,
    listening to events, etc.
    """

    # Monad Mainnet RPC (placeholder)
    RPC_URL = "https://rpc.monad.xyz"

    def __init__(self, rpc_url: Optional[str] = None):
        self.rpc_url = rpc_url or os.getenv("MONAD_RPC_URL", self.RPC_URL)

    async def get_block_number(self) -> int:
        """Get current block number"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                self.rpc_url,
                json={
                    "jsonrpc": "2.0",
                    "method": "eth_blockNumber",
                    "params": [],
                    "id": 1
                }
            )
            data = response.json()
            return int(data.get("result", "0x0"), 16)

    async def get_balance(self, address: str) -> float:
        """Get MON balance for address"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                self.rpc_url,
                json={
                    "jsonrpc": "2.0",
                    "method": "eth_getBalance",
                    "params": [address, "latest"],
                    "id": 1
                }
            )
            data = response.json()
            wei = int(data.get("result", "0x0"), 16)
            return wei / 1e18  # Convert to MON


# =============================================================================
# Funding Wallet (Trading Fees)
# =============================================================================

@dataclass
class FundingStatus:
    """Status of the project funding wallet"""
    wallet_address: str
    balance_mon: float
    balance_usd: float
    total_received: float
    total_spent: float
    last_updated: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "wallet_address": self.wallet_address,
            "balance_mon": self.balance_mon,
            "balance_usd": self.balance_usd,
            "total_received": self.total_received,
            "total_spent": self.total_spent,
            "last_updated": self.last_updated.isoformat(),
        }


# =============================================================================
# Convenience
# =============================================================================

def create_lfj_client(token_address: Optional[str] = None) -> LFJTokenMillClient:
    """Create an LFJ Token Mill client"""
    return LFJTokenMillClient(token_address=token_address)


# Legacy alias for backwards compatibility
def create_nadfun_client(token_address: Optional[str] = None) -> LFJTokenMillClient:
    """Legacy alias - use create_lfj_client instead"""
    return create_lfj_client(token_address=token_address)


# Class alias for backwards compatibility
NadFunClient = LFJTokenMillClient


def create_monad_client(rpc_url: Optional[str] = None) -> MonadClient:
    """Create a Monad RPC client"""
    return MonadClient(rpc_url=rpc_url)
