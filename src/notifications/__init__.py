"""
Notifications Module
====================

Multi-channel alert system for grow events.

Supports:
- Discord webhooks
- Telegram bot messages
- Batched info alerts
- Immediate critical alerts

Usage:
    from src.notifications import AlertManager

    manager = AlertManager()

    # Critical (immediate)
    await manager.critical("Temp Critical!", "Temperature at 95F!")

    # Warning (soon)
    await manager.warning("VPD Drift", "VPD at 1.8 kPa")

    # Info (batched)
    await manager.info("Daily Update", "Day 49 complete")

Environment Variables:
    DISCORD_WEBHOOK_URL - Discord webhook URL
    TELEGRAM_BOT_TOKEN - Telegram bot token
    TELEGRAM_CHAT_ID - Telegram chat ID
"""

from .alerts import (
    AlertManager,
    AlertLevel,
    Alert,
    DiscordNotifier,
    TelegramNotifier,
    create_alert_manager,
    alert_temperature_critical,
    alert_water_low,
    alert_stage_change,
    alert_human_action_required,
)

__all__ = [
    "AlertManager",
    "AlertLevel",
    "Alert",
    "DiscordNotifier",
    "TelegramNotifier",
    "create_alert_manager",
    "alert_temperature_critical",
    "alert_water_low",
    "alert_stage_change",
    "alert_human_action_required",
]
