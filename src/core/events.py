"""
Event Bus
=========

Central nervous system for the unified GanjaMon agent.
asyncio.PriorityQueue-backed pub/sub with typed dataclass events.

Usage:
    bus = get_event_bus()
    bus.subscribe(SensorReadingEvent, my_handler)
    await bus.emit(SensorReadingEvent(temp=77.0, humidity=55.0))
"""

import asyncio
import time
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Callable, Coroutine, Dict, List, Optional, Type


class EventPriority(IntEnum):
    CRITICAL = 0      # SafetyEvent, ShutdownEvent
    HIGH = 10          # TradeSignalEvent, ActuatorCommandEvent
    NORMAL = 20        # SensorReadingEvent, AIDecisionEvent
    LOW = 30           # SocialPostEvent, EngagementEvent
    BACKGROUND = 40    # MetricsEvent, LearningUpdateEvent


@dataclass
class Event:
    """Base event. All events inherit from this."""
    timestamp: float = field(default_factory=time.time)
    source: str = ""

    @property
    def priority(self) -> EventPriority:
        return EventPriority.NORMAL


# ---------------------------------------------------------------------------
# Safety / Lifecycle Events
# ---------------------------------------------------------------------------

@dataclass
class SafetyEvent(Event):
    violation_type: str = ""
    message: str = ""
    device: str = ""

    @property
    def priority(self) -> EventPriority:
        return EventPriority.CRITICAL


@dataclass
class ShutdownEvent(Event):
    reason: str = ""

    @property
    def priority(self) -> EventPriority:
        return EventPriority.CRITICAL


@dataclass
class CircuitBreakerEvent(Event):
    service: str = ""
    state: str = ""  # "opened", "closed", "half_open"
    failure_count: int = 0

    @property
    def priority(self) -> EventPriority:
        return EventPriority.HIGH


# ---------------------------------------------------------------------------
# Trading / Alpha Events
# ---------------------------------------------------------------------------

@dataclass
class TradeSignalEvent(Event):
    asset: str = ""
    chain: str = ""
    direction: str = ""  # "buy", "sell", "hold"
    confidence: float = 0.0
    evidence: str = ""
    confluence_score: float = 0.0

    @property
    def priority(self) -> EventPriority:
        return EventPriority.HIGH


@dataclass
class WalletActivityEvent(Event):
    wallet: str = ""
    chain: str = ""
    action: str = ""
    token: str = ""
    amount: float = 0.0
    amount_usd: float = 0.0
    is_smart_money: bool = False

    @property
    def priority(self) -> EventPriority:
        return EventPriority.NORMAL


@dataclass
class MarketRegimeEvent(Event):
    regime: str = ""  # "bull", "bear", "crab"
    confidence: float = 0.0
    from_regime: str = ""

    @property
    def priority(self) -> EventPriority:
        return EventPriority.HIGH


@dataclass
class ArbitrageOpportunityEvent(Event):
    market: str = ""
    spread: float = 0.0
    capital_needed: float = 0.0
    expected_roi: float = 0.0

    @property
    def priority(self) -> EventPriority:
        return EventPriority.HIGH


@dataclass
class TokenLaunchEvent(Event):
    chain: str = ""
    address: str = ""
    creator: str = ""
    bonding_curve_state: str = ""

    @property
    def priority(self) -> EventPriority:
        return EventPriority.HIGH


@dataclass
class WhaleMovementEvent(Event):
    wallet: str = ""
    chain: str = ""
    token: str = ""
    amount_usd: float = 0.0
    direction: str = ""  # "buy", "sell", "transfer"

    @property
    def priority(self) -> EventPriority:
        return EventPriority.NORMAL


# ---------------------------------------------------------------------------
# Cultivation Events
# ---------------------------------------------------------------------------

@dataclass
class SensorReadingEvent(Event):
    temp_f: float = 0.0
    humidity: float = 0.0
    vpd: float = 0.0
    co2: float = 0.0
    soil_moisture: float = 0.0

    @property
    def priority(self) -> EventPriority:
        return EventPriority.NORMAL


@dataclass
class ActuatorCommandEvent(Event):
    device: str = ""
    state: bool = False
    amount: float = 0.0
    reason: str = ""

    @property
    def priority(self) -> EventPriority:
        return EventPriority.HIGH


@dataclass
class AIDecisionEvent(Event):
    decision: str = ""
    reasoning: str = ""
    actions: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def priority(self) -> EventPriority:
        return EventPriority.NORMAL


# ---------------------------------------------------------------------------
# Social Events
# ---------------------------------------------------------------------------

@dataclass
class SocialPostEvent(Event):
    platform: str = ""  # "farcaster", "telegram", "twitter"
    content: str = ""
    post_type: str = ""  # "plant_update", "trade_call", "alpha_insight"

    @property
    def priority(self) -> EventPriority:
        return EventPriority.LOW


@dataclass
class EngagementEvent(Event):
    platform: str = ""
    action: str = ""  # "reply", "like", "repost"
    target: str = ""

    @property
    def priority(self) -> EventPriority:
        return EventPriority.LOW


@dataclass
class CommunitySignalEvent(Event):
    member: str = ""
    signal: str = ""
    platform: str = ""

    @property
    def priority(self) -> EventPriority:
        return EventPriority.LOW


# ---------------------------------------------------------------------------
# Learning Events
# ---------------------------------------------------------------------------

@dataclass
class MetricsEvent(Event):
    component: str = ""
    metrics: Dict[str, Any] = field(default_factory=dict)

    @property
    def priority(self) -> EventPriority:
        return EventPriority.BACKGROUND


@dataclass
class LearningUpdateEvent(Event):
    component: str = ""
    metric: str = ""
    old_value: float = 0.0
    new_value: float = 0.0

    @property
    def priority(self) -> EventPriority:
        return EventPriority.BACKGROUND


@dataclass
class PatternDiscoveryEvent(Event):
    pattern_type: str = ""
    conditions: str = ""
    win_rate: float = 0.0
    sample_size: int = 0

    @property
    def priority(self) -> EventPriority:
        return EventPriority.BACKGROUND


# ---------------------------------------------------------------------------
# Event Bus
# ---------------------------------------------------------------------------

# Type alias for handler
EventHandler = Callable[[Event], Coroutine[Any, Any, None]]


class EventBus:
    """
    Central event bus with priority queue and typed pub/sub.

    Thread-safe via asyncio. Events are dispatched by type —
    subscribers only receive events they registered for.
    """

    def __init__(self, maxsize: int = 10000):
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue(maxsize=maxsize)
        self._handlers: Dict[Type[Event], List[EventHandler]] = {}
        self._running = False
        self._dispatch_task: Optional[asyncio.Task] = None
        self._seq = 0  # tiebreaker for same-priority events

    def subscribe(self, event_type: Type[Event], handler: EventHandler) -> None:
        """Subscribe a handler to an event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: Type[Event], handler: EventHandler) -> None:
        """Remove a handler subscription."""
        if event_type in self._handlers:
            self._handlers[event_type] = [
                h for h in self._handlers[event_type] if h is not handler
            ]

    async def emit(self, event: Event) -> None:
        """Emit an event onto the bus."""
        self._seq += 1
        await self._queue.put((event.priority, self._seq, event))

    def emit_nowait(self, event: Event) -> None:
        """Emit without awaiting (fire-and-forget). Drops if queue full."""
        self._seq += 1
        try:
            self._queue.put_nowait((event.priority, self._seq, event))
        except asyncio.QueueFull:
            pass  # drop low-priority events when overloaded

    async def start(self) -> None:
        """Start the dispatch loop."""
        if self._running:
            return
        self._running = True
        self._dispatch_task = asyncio.create_task(self._dispatch_loop())

    async def stop(self) -> None:
        """Stop the dispatch loop and drain remaining events."""
        self._running = False
        if self._dispatch_task:
            self._dispatch_task.cancel()
            try:
                await self._dispatch_task
            except asyncio.CancelledError:
                pass

    async def _dispatch_loop(self) -> None:
        """Main dispatch loop — dequeue and fan out to handlers."""
        while self._running:
            try:
                priority, seq, event = await asyncio.wait_for(
                    self._queue.get(), timeout=1.0
                )
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

            event_type = type(event)
            handlers = self._handlers.get(event_type, [])

            # Also dispatch to base Event handlers (catch-all)
            if event_type is not Event:
                handlers = handlers + self._handlers.get(Event, [])

            for handler in handlers:
                try:
                    await handler(event)
                except Exception as e:
                    # Never let a bad handler kill the bus
                    import structlog
                    structlog.get_logger().error(
                        "event_handler_error",
                        handler=handler.__qualname__,
                        event_type=event_type.__name__,
                        error=str(e),
                    )

    @property
    def pending(self) -> int:
        """Number of events waiting to be dispatched."""
        return self._queue.qsize()

    @property
    def handler_count(self) -> int:
        """Total number of registered handlers."""
        return sum(len(h) for h in self._handlers.values())


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get the global event bus singleton."""
    global _bus
    if _bus is None:
        _bus = EventBus()
    return _bus
