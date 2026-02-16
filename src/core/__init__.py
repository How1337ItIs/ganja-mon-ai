"""
Core Infrastructure
===================

Foundation layer for the unified GanjaMon agent.
Provides: event bus, config, logging, circuit breakers, watchdog, supervisor, health.
"""

from src.core.events import (
    Event,
    EventBus,
    EventPriority,
    get_event_bus,
    # Event types
    SafetyEvent,
    ShutdownEvent,
    CircuitBreakerEvent,
    TradeSignalEvent,
    WalletActivityEvent,
    MarketRegimeEvent,
    ArbitrageOpportunityEvent,
    TokenLaunchEvent,
    WhaleMovementEvent,
    SensorReadingEvent,
    ActuatorCommandEvent,
    AIDecisionEvent,
    SocialPostEvent,
    EngagementEvent,
    CommunitySignalEvent,
    MetricsEvent,
    LearningUpdateEvent,
    PatternDiscoveryEvent,
)
from src.core.config import Settings, get_settings
from src.core.logging_config import setup_logging, get_logger
from src.core.circuit_breaker import (
    CircuitBreaker,
    CircuitOpenError,
    BreakerConfig,
    get_breaker,
    get_all_breakers,
    circuit_breaker,
)
from src.core.watchdog import Watchdog, get_watchdog
from src.core.supervisor import Supervisor, get_supervisor
from src.core.health import health_router

__all__ = [
    # Events
    "Event", "EventBus", "EventPriority", "get_event_bus",
    "SafetyEvent", "ShutdownEvent", "CircuitBreakerEvent",
    "TradeSignalEvent", "WalletActivityEvent", "MarketRegimeEvent",
    "ArbitrageOpportunityEvent", "TokenLaunchEvent", "WhaleMovementEvent",
    "SensorReadingEvent", "ActuatorCommandEvent", "AIDecisionEvent",
    "SocialPostEvent", "EngagementEvent", "CommunitySignalEvent",
    "MetricsEvent", "LearningUpdateEvent", "PatternDiscoveryEvent",
    # Config
    "Settings", "get_settings",
    # Logging
    "setup_logging", "get_logger",
    # Circuit breaker
    "CircuitBreaker", "CircuitOpenError", "BreakerConfig",
    "get_breaker", "get_all_breakers", "circuit_breaker",
    # Watchdog
    "Watchdog", "get_watchdog",
    # Supervisor
    "Supervisor", "get_supervisor",
    # Health
    "health_router",
]
