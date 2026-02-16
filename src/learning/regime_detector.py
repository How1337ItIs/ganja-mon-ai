"""
Market Regime Detector
======================

Classifies market state as BULL / BEAR / CRAB using price data and volume.
Adapts position sizing, strategy selection, and capital allocation per regime.

Emits MarketRegimeEvent on the event bus when regime changes.

Regimes:
    BULL  — Trending up (momentum strategies, full position sizes)
    BEAR  — Trending down (defensive, 25-50% position, perps/shorts)
    CRAB  — Sideways (mean reversion, reduced position, arb focus)

Data source: CoinGecko free API (BTC price as proxy for overall market).
"""

import asyncio
import json
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
import structlog

from src.core.circuit_breaker import get_breaker
from src.core.events import MarketRegimeEvent, get_event_bus

log = structlog.get_logger("regime")

COINGECKO_PRICE_URL = "https://api.coingecko.com/api/v3/simple/price"
COINGECKO_MARKET_URL = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"

STATE_FILE = Path("data/market_regime.json")


class Regime(str, Enum):
    BULL = "bull"
    BEAR = "bear"
    CRAB = "crab"
    UNKNOWN = "unknown"


# Regime-specific parameters
REGIME_PARAMS = {
    Regime.BULL: {
        "position_scale": 1.0,      # Full positions
        "strategy_weights": {
            "momentum": 1.5,
            "launch_sniper": 1.3,
            "smart_money": 1.2,
            "arb": 0.8,
            "mean_reversion": 0.5,
        },
        "capital_allocation": {
            "on_chain": 0.40,
            "perps": 0.20,
            "prediction": 0.15,
            "arb": 0.15,
            "cash": 0.10,
        },
    },
    Regime.BEAR: {
        "position_scale": 0.35,     # Defensive
        "strategy_weights": {
            "momentum": 0.3,
            "launch_sniper": 0.5,
            "smart_money": 1.0,
            "arb": 1.5,
            "mean_reversion": 1.3,
        },
        "capital_allocation": {
            "on_chain": 0.15,
            "perps": 0.35,       # Shorts profitable
            "prediction": 0.15,
            "arb": 0.20,
            "cash": 0.15,
        },
    },
    Regime.CRAB: {
        "position_scale": 0.5,
        "strategy_weights": {
            "momentum": 0.5,
            "launch_sniper": 0.8,
            "smart_money": 1.0,
            "arb": 1.5,
            "mean_reversion": 1.5,
        },
        "capital_allocation": {
            "on_chain": 0.20,
            "perps": 0.25,
            "prediction": 0.20,
            "arb": 0.25,
            "cash": 0.10,
        },
    },
}


@dataclass
class PriceSnapshot:
    """A price observation."""
    price: float
    volume_24h: float = 0.0
    change_24h: float = 0.0
    change_7d: float = 0.0
    timestamp: float = field(default_factory=time.time)


class RegimeDetector:
    """
    Detects market regime using BTC price as proxy.

    Algorithm:
    1. Track 7d rolling price data
    2. Compute: trend direction, volatility, momentum
    3. Classify regime using simple thresholds
    4. Emit event on regime change

    Thresholds (tunable):
    - BULL: 7d change > +5% AND 24h change > -2%
    - BEAR: 7d change < -5% AND 24h change < +2%
    - CRAB: neither (oscillating within ±5%)
    """

    def __init__(
        self,
        poll_interval: float = 600.0,  # 10 min
        bull_threshold: float = 5.0,
        bear_threshold: float = -5.0,
    ):
        self.poll_interval = poll_interval
        self.bull_threshold = bull_threshold
        self.bear_threshold = bear_threshold
        self._running = False
        self._client: Optional[httpx.AsyncClient] = None
        self._current_regime = Regime.UNKNOWN
        self._regime_confidence = 0.0
        self._price_history: List[PriceSnapshot] = []
        self._regime_since: float = time.time()

        # Load persisted state
        self._load_state()

    async def start(self) -> None:
        self._running = True
        self._client = httpx.AsyncClient(timeout=15.0)
        log.info("regime_detector_started", current=self._current_regime.value)

        while self._running:
            try:
                await self._detect()
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error("regime_detect_error", error=str(e))

            await asyncio.sleep(self.poll_interval + random.uniform(-30, 30))

    async def stop(self) -> None:
        self._running = False
        self._save_state()
        if self._client:
            await self._client.aclose()

    async def _detect(self) -> None:
        """Fetch price data and classify regime."""
        breaker = get_breaker("coingecko_api")
        if breaker is None:
            # CoinGecko doesn't have a pre-configured breaker, use default
            from src.core.circuit_breaker import CircuitBreaker
            breaker = CircuitBreaker("coingecko_api", failure_max=5, reset_timeout=120)

        try:
            async with breaker:
                resp = await self._client.get(
                    COINGECKO_PRICE_URL,
                    params={
                        "ids": "bitcoin",
                        "vs_currencies": "usd",
                        "include_24hr_vol": "true",
                        "include_24hr_change": "true",
                        "include_7d_change": "true",  # May not work on free tier
                    },
                )
        except Exception:
            return

        if resp.status_code != 200:
            return

        data = resp.json().get("bitcoin", {})
        if not data:
            return

        price = data.get("usd", 0)
        vol_24h = data.get("usd_24h_vol", 0)
        change_24h = data.get("usd_24h_change", 0)

        if price <= 0:
            return

        snapshot = PriceSnapshot(
            price=price,
            volume_24h=vol_24h,
            change_24h=change_24h,
        )
        self._price_history.append(snapshot)

        # Keep 7 days of snapshots (at 10min intervals = ~1008)
        if len(self._price_history) > 1100:
            self._price_history = self._price_history[-1000:]

        # Compute 7d change from our own history
        change_7d = 0.0
        seven_days_ago = time.time() - 7 * 86400
        old_prices = [p for p in self._price_history if p.timestamp < seven_days_ago + 3600]
        if old_prices:
            old_price = old_prices[-1].price
            change_7d = ((price - old_price) / old_price) * 100
            snapshot.change_7d = change_7d

        # Classify regime
        old_regime = self._current_regime
        new_regime, confidence = self._classify(change_24h, change_7d, vol_24h)

        if new_regime != old_regime and confidence >= 0.5:
            self._current_regime = new_regime
            self._regime_confidence = confidence
            self._regime_since = time.time()
            self._save_state()

            # Emit regime change event
            bus = get_event_bus()
            await bus.emit(MarketRegimeEvent(
                regime=new_regime.value,
                confidence=confidence,
                from_regime=old_regime.value,
            ))

            log.info(
                "regime_change",
                old=old_regime.value,
                new=new_regime.value,
                confidence=round(confidence, 2),
                btc_price=round(price),
                change_24h=round(change_24h, 1),
                change_7d=round(change_7d, 1),
            )
        else:
            # Update confidence even without regime change
            self._regime_confidence = confidence

    def _classify(
        self, change_24h: float, change_7d: float, volume: float
    ) -> tuple:
        """Classify market regime from price data. Returns (regime, confidence)."""

        # Strong signals
        if change_7d >= self.bull_threshold and change_24h > -2:
            confidence = min(0.5 + abs(change_7d - self.bull_threshold) / 20, 0.95)
            return Regime.BULL, confidence

        if change_7d <= self.bear_threshold and change_24h < 2:
            confidence = min(0.5 + abs(change_7d - self.bear_threshold) / 20, 0.95)
            return Regime.BEAR, confidence

        # Moderate signals (look at 24h for direction hint)
        if change_7d > 2 and change_24h > 1:
            return Regime.BULL, 0.4 + min(change_7d / 10, 0.3)

        if change_7d < -2 and change_24h < -1:
            return Regime.BEAR, 0.4 + min(abs(change_7d) / 10, 0.3)

        # Default: crab
        confidence = 0.5 + (1.0 - min(abs(change_7d) / 5, 1.0)) * 0.3
        return Regime.CRAB, confidence

    def get_regime(self) -> Regime:
        return self._current_regime

    def get_regime_params(self) -> Dict:
        """Get current regime's position/strategy parameters."""
        return REGIME_PARAMS.get(self._current_regime, REGIME_PARAMS[Regime.CRAB])

    def get_position_scale(self) -> float:
        """Get position size multiplier for current regime."""
        return self.get_regime_params()["position_scale"]

    def get_strategy_weight(self, strategy: str) -> float:
        """Get strategy weight multiplier for current regime."""
        return self.get_regime_params()["strategy_weights"].get(strategy, 1.0)

    def get_status(self) -> Dict[str, Any]:
        return {
            "regime": self._current_regime.value,
            "confidence": round(self._regime_confidence, 2),
            "since": self._regime_since,
            "position_scale": self.get_position_scale(),
            "price_history_points": len(self._price_history),
            "latest_price": round(self._price_history[-1].price) if self._price_history else 0,
        }

    def _save_state(self) -> None:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        state = {
            "regime": self._current_regime.value,
            "confidence": self._regime_confidence,
            "since": self._regime_since,
            "updated": time.time(),
        }
        STATE_FILE.write_text(json.dumps(state, indent=2))

    def _load_state(self) -> None:
        if STATE_FILE.exists():
            try:
                state = json.loads(STATE_FILE.read_text())
                self._current_regime = Regime(state.get("regime", "unknown"))
                self._regime_confidence = state.get("confidence", 0.0)
                self._regime_since = state.get("since", time.time())
            except (json.JSONDecodeError, ValueError):
                pass


# Singleton
_detector: Optional[RegimeDetector] = None


def get_regime_detector() -> RegimeDetector:
    global _detector
    if _detector is None:
        _detector = RegimeDetector()
    return _detector
