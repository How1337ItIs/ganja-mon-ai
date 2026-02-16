"""
Notifications & Alerts
======================

Multi-channel alert system for grow events.
Supports Discord webhooks and Telegram bots.

Alert Types:
- CRITICAL: Safety issues, hardware failures (immediate)
- WARNING: Environmental drift, low supplies (within 15 min)
- INFO: Daily updates, milestones (batched)
"""

import os
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
import logging
import json

import httpx


logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels"""
    CRITICAL = "critical"  # Immediate - safety issues
    WARNING = "warning"    # Soon - environmental drift
    INFO = "info"          # Batched - daily updates


@dataclass
class Alert:
    """An alert to be sent"""
    level: AlertLevel
    title: str
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    image_url: Optional[str] = None


# =============================================================================
# Generic Webhook Client (Zapier/IFTTT/etc.)
# =============================================================================

class WebhookNotifier:
    """
    Send notifications to an arbitrary webhook URL (Zapier Catch Hook, IFTTT Webhooks, Make.com, etc.).

    Env vars:
        ALERT_WEBHOOK_URL: Webhook endpoint to POST alerts to
        ALERT_WEBHOOK_SECRET: Optional shared secret
        ALERT_WEBHOOK_SECRET_HEADER: Optional header name (default: X-Webhook-Secret)
    """

    def __init__(
        self,
        webhook_url: Optional[str] = None,
        secret: Optional[str] = None,
        secret_header: Optional[str] = None,
    ):
        self.webhook_url = webhook_url or os.getenv("ALERT_WEBHOOK_URL")
        self.secret = secret if secret is not None else os.getenv("ALERT_WEBHOOK_SECRET")
        self.secret_header = secret_header or os.getenv("ALERT_WEBHOOK_SECRET_HEADER") or "X-Webhook-Secret"
        self._configured = bool(self.webhook_url)

        if not self._configured:
            logger.warning("Generic alert webhook not configured")

    async def send(self, alert: Alert) -> bool:
        if not self._configured:
            logger.info(f"[MOCK WEBHOOK] {alert.level.value}: {alert.title}")
            return True

        payload = {
            "level": alert.level.value,
            "title": alert.title,
            "message": alert.message,
            "timestamp": alert.timestamp.isoformat(),
            "data": alert.data or {},
            "image_url": alert.image_url,
            "source": "grokmon",
        }

        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if self.secret:
            headers[self.secret_header] = self.secret

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    headers=headers,
                    timeout=10.0,
                )
                response.raise_for_status()
            logger.info(f"Webhook alert sent: {alert.title}")
            return True
        except Exception as e:
            logger.error(f"Webhook send failed: {e}")
            return False


# =============================================================================
# Signal Client (via signal-cli)
# =============================================================================

class SignalNotifier:
    """
    Send notifications via Signal using signal-cli (headless, self-hosted).

    This is the most reliable way to reach the Signal app, but it requires:
    - signal-cli installed on the machine running the orchestrator
    - a registered Signal account for the sender number

    Env vars:
        SIGNAL_CLI_BIN: Path to signal-cli (default: signal-cli)
        SIGNAL_SENDER: Sender phone number in E164 (+15551234567)
        SIGNAL_RECIPIENTS: Comma-separated recipient phone numbers in E164
    """

    def __init__(
        self,
        cli_bin: Optional[str] = None,
        sender: Optional[str] = None,
        recipients: Optional[str] = None,
    ):
        self.cli_bin = cli_bin or os.getenv("SIGNAL_CLI_BIN") or "signal-cli"
        self.sender = sender or os.getenv("SIGNAL_SENDER")
        recipients_raw = recipients or os.getenv("SIGNAL_RECIPIENTS") or ""
        self.recipients = [r.strip() for r in recipients_raw.split(",") if r.strip()]
        self._configured = bool(self.sender and self.recipients)

        if not self._configured:
            logger.warning("Signal notifier not configured")

    async def send(self, alert: Alert) -> bool:
        if not self._configured:
            logger.info(f"[MOCK SIGNAL] {alert.level.value}: {alert.title}")
            return True

        # Keep it readable on lockscreen
        text = f"{alert.title}\n\n{alert.message}".strip()
        if alert.data:
            # Include a small, bounded set of key/value pairs
            items = list(alert.data.items())[:6]
            kv = "\n".join(f"- {k}: {v}" for k, v in items)
            text = f"{text}\n\n{kv}"

        try:
            # signal-cli -u <sender> send -m "<message>" <recipient1> <recipient2>
            proc = await asyncio.create_subprocess_exec(
                self.cli_bin,
                "-u",
                self.sender,
                "send",
                "-m",
                text,
                *self.recipients,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await proc.communicate()
            if proc.returncode != 0:
                err = (stderr or b"").decode("utf-8", errors="replace").strip()
                logger.error(f"Signal send failed (exit {proc.returncode}): {err}")
                return False
            logger.info(f"Signal alert sent: {alert.title}")
            return True
        except FileNotFoundError:
            logger.error(f"Signal send failed: signal-cli not found ({self.cli_bin})")
            return False
        except Exception as e:
            logger.error(f"Signal send failed: {e}")
            return False


# =============================================================================
# Discord Webhook Client
# =============================================================================

class DiscordNotifier:
    """
    Send notifications via Discord webhook.

    Env vars:
        DISCORD_WEBHOOK_URL: Discord webhook URL
        DISCORD_ALERT_CHANNEL_ID: Optional channel for alerts
    """

    COLORS = {
        AlertLevel.CRITICAL: 0xFF0000,  # Red
        AlertLevel.WARNING: 0xFFA500,   # Orange
        AlertLevel.INFO: 0x00FF00,      # Green
    }

    EMOJIS = {
        AlertLevel.CRITICAL: "",
        AlertLevel.WARNING: "",
        AlertLevel.INFO: "",
    }

    def __init__(
        self,
        webhook_url: Optional[str] = None,
    ):
        self.webhook_url = webhook_url or os.getenv("DISCORD_WEBHOOK_URL")
        self._configured = bool(self.webhook_url)

        if not self._configured:
            logger.warning("Discord webhook not configured")

    async def send(self, alert: Alert) -> bool:
        """Send an alert to Discord"""
        if not self._configured:
            logger.info(f"[MOCK DISCORD] {alert.level.value}: {alert.title}")
            return True

        try:
            embed = {
                "title": f"{self.EMOJIS[alert.level]} {alert.title}",
                "description": alert.message,
                "color": self.COLORS[alert.level],
                "timestamp": alert.timestamp.isoformat(),
                "footer": {"text": "Grok & Mon"},
            }

            if alert.data:
                embed["fields"] = [
                    {"name": k, "value": str(v), "inline": True}
                    for k, v in list(alert.data.items())[:6]
                ]

            if alert.image_url:
                embed["image"] = {"url": alert.image_url}

            payload = {
                "embeds": [embed],
                "username": "Grok",
                "avatar_url": "https://grokandmon.xyz/assets/grok-avatar.png",
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    timeout=10.0,
                )
                response.raise_for_status()

            logger.info(f"Discord alert sent: {alert.title}")
            return True

        except Exception as e:
            logger.error(f"Discord send failed: {e}")
            return False

    async def send_daily_summary(
        self,
        day: int,
        stage: str,
        sensors: Dict[str, Any],
        events: List[str],
    ) -> bool:
        """Send a daily summary embed"""
        alert = Alert(
            level=AlertLevel.INFO,
            title=f"Day {day} Summary",
            message=f"Growth Stage: **{stage.title()}**",
            data={
                "Temperature": f"{sensors.get('air_temp', 0):.1f}F",
                "Humidity": f"{sensors.get('humidity', 0):.0f}%",
                "VPD": f"{sensors.get('vpd', 0):.2f} kPa",
                "CO2": f"{sensors.get('co2', 0)} ppm",
                "Soil": f"{sensors.get('soil_moisture', 0):.0f}%",
                "Events": str(len(events)),
            },
        )
        return await self.send(alert)


# =============================================================================
# Telegram Bot Client
# =============================================================================

class TelegramNotifier:
    """
    Send notifications via Telegram bot.

    Env vars:
        TELEGRAM_BOT_TOKEN: Bot token from @BotFather
        TELEGRAM_CHAT_ID: Chat/group ID to send to
    """

    API_BASE = "https://api.telegram.org/bot"

    def __init__(
        self,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None,
    ):
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        self._configured = bool(self.bot_token and self.chat_id)

        if not self._configured:
            logger.warning("Telegram bot not configured")

    async def send(self, alert: Alert) -> bool:
        """Send an alert to Telegram"""
        if not self._configured:
            logger.info(f"[MOCK TELEGRAM] {alert.level.value}: {alert.title}")
            return True

        try:
            # Format message
            emoji = {"critical": "", "warning": "", "info": ""}.get(
                alert.level.value, ""
            )

            text = f"{emoji} *{alert.title}*\n\n{alert.message}"

            if alert.data:
                text += "\n\n"
                for k, v in alert.data.items():
                    text += f"• {k}: `{v}`\n"

            # Send message
            url = f"{self.API_BASE}{self.bot_token}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "Markdown",
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=10.0)
                response.raise_for_status()

            logger.info(f"Telegram alert sent: {alert.title}")
            return True

        except Exception as e:
            logger.error(f"Telegram send failed: {e}")
            return False

    async def send_photo(
        self,
        image_data: bytes,
        caption: str,
    ) -> bool:
        """Send a photo to Telegram"""
        if not self._configured:
            logger.info(f"[MOCK TELEGRAM PHOTO] {caption[:50]}...")
            return True

        try:
            url = f"{self.API_BASE}{self.bot_token}/sendPhoto"

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    data={"chat_id": self.chat_id, "caption": caption},
                    files={"photo": ("plant.jpg", image_data, "image/jpeg")},
                    timeout=30.0,
                )
                response.raise_for_status()

            logger.info("Telegram photo sent")
            return True

        except Exception as e:
            logger.error(f"Telegram photo failed: {e}")
            return False


# =============================================================================
# Unified Alert Manager
# =============================================================================

class AlertManager:
    """
    Unified alert manager that sends to all configured channels.

    Usage:
        manager = AlertManager()

        # Critical alert (sent immediately to all channels)
        await manager.critical("Temperature Critical", "Temp reached 95F!")

        # Warning (sent within 15 minutes)
        await manager.warning("VPD Drift", "VPD at 1.8 kPa")

        # Info (batched)
        await manager.info("Daily Update", "Day 49 complete")
    """

    def __init__(self):
        self.discord = DiscordNotifier()
        self.telegram = TelegramNotifier()
        self.webhook = WebhookNotifier()
        self.signal = SignalNotifier()

        # Alert queue for batching
        self._queue: List[Alert] = []
        self._batch_task: Optional[asyncio.Task] = None

    async def send(self, alert: Alert) -> Dict[str, bool]:
        """Send alert to all configured channels"""
        results = {}

        # Critical alerts sent immediately
        if alert.level == AlertLevel.CRITICAL:
            results["discord"] = await self.discord.send(alert)
            results["telegram"] = await self.telegram.send(alert)
            results["webhook"] = await self.webhook.send(alert)
            results["signal"] = await self.signal.send(alert)
        else:
            # Queue for batching
            self._queue.append(alert)
            if not self._batch_task or self._batch_task.done():
                self._batch_task = asyncio.create_task(self._process_queue())
            results["queued"] = True

        return results

    async def _process_queue(self):
        """Process queued alerts"""
        await asyncio.sleep(60)  # Wait 1 minute for batching

        if not self._queue:
            return

        # Send warnings immediately
        warnings = [a for a in self._queue if a.level == AlertLevel.WARNING]
        for alert in warnings:
            await self.discord.send(alert)
            await self.telegram.send(alert)
            await self.webhook.send(alert)
            await self.signal.send(alert)

        # Batch info alerts
        infos = [a for a in self._queue if a.level == AlertLevel.INFO]
        if infos:
            batch_message = "\n\n".join(
                f"**{a.title}**: {a.message}" for a in infos
            )
            batch_alert = Alert(
                level=AlertLevel.INFO,
                title=f"{len(infos)} Updates",
                message=batch_message,
            )
            await self.discord.send(batch_alert)
            await self.telegram.send(batch_alert)
            await self.webhook.send(batch_alert)
            await self.signal.send(batch_alert)

        self._queue.clear()

    # Convenience methods
    async def critical(self, title: str, message: str, **data) -> Dict[str, bool]:
        """Send critical alert immediately"""
        return await self.send(Alert(
            level=AlertLevel.CRITICAL,
            title=title,
            message=message,
            data=data,
        ))

    async def warning(self, title: str, message: str, **data) -> Dict[str, bool]:
        """Send warning alert"""
        return await self.send(Alert(
            level=AlertLevel.WARNING,
            title=title,
            message=message,
            data=data,
        ))

    async def info(self, title: str, message: str, **data) -> Dict[str, bool]:
        """Send info alert (batched)"""
        return await self.send(Alert(
            level=AlertLevel.INFO,
            title=title,
            message=message,
            data=data,
        ))


# =============================================================================
# Pre-defined Alert Templates
# =============================================================================

async def alert_temperature_critical(manager: AlertManager, temp_f: float):
    """Alert for critical temperature"""
    await manager.critical(
        "Temperature Critical!",
        f"Temperature at {temp_f:.1f}F - immediate action needed!",
        temperature=f"{temp_f:.1f}F",
        action="Check HVAC and ventilation",
    )


async def alert_water_low(manager: AlertManager, level_percent: float):
    """Alert for low water reservoir"""
    await manager.warning(
        "Water Level Low",
        f"Reservoir at {level_percent:.0f}% - refill soon",
        level=f"{level_percent:.0f}%",
    )


async def alert_stage_change(manager: AlertManager, old_stage: str, new_stage: str, day: int):
    """Alert for growth stage change"""
    await manager.info(
        "Growth Stage Change!",
        f"Transitioned from {old_stage} to {new_stage} on Day {day}",
        from_stage=old_stage,
        to_stage=new_stage,
        day=day,
    )


async def alert_human_action_required(
    manager: AlertManager,
    title: str,
    message: str,
    *,
    day: Optional[int] = None,
    stage: Optional[str] = None,
    urgency: Optional[str] = None,
    **data,
):
    """
    Alert that a human needs to do something physical/manual.

    Sent as CRITICAL so it goes out immediately (no batching).
    """
    payload = dict(data)
    if day is not None:
        payload["day"] = day
    if stage is not None:
        payload["stage"] = stage
    if urgency is not None:
        payload["urgency"] = urgency
    await manager.critical(title, message, **payload)


# =============================================================================
# Convenience Functions
# =============================================================================

def create_alert_manager() -> AlertManager:
    """Create an AlertManager instance"""
    return AlertManager()
