#!/usr/bin/env python3
"""
Appeal Telegram bot ban via Abuse Notifications bot.
"""
import os
import asyncio
from dotenv import load_dotenv
load_dotenv()

from telethon import TelegramClient

API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
PHONE = os.getenv("TELEGRAM_PHONE")

APPEAL_MESSAGE = """This bot is NOT for selling drugs or illegal activity.

@GanjaMonAIBot is an educational/scientific project for LEGAL personal cannabis cultivation under California Proposition 64, which allows adults 21+ to grow up to 6 plants for personal use.

The bot:
- Monitors plant health sensors (temperature, humidity, CO2)
- Provides automated growing tips based on AI analysis
- Shares progress of a single legal home-grown plant
- Is part of an open-source IoT agriculture project (https://github.com)

We do NOT:
- Sell any cannabis or drugs
- Facilitate any transactions
- Promote illegal activity

This is a legitimate agricultural technology project similar to smart garden monitors. The plant is grown legally in California for personal/educational purposes only.

Please review and restore the bot. Thank you."""

async def main():
    print("Connecting to Telegram...")
    client = TelegramClient("telegram_session", API_ID, API_HASH)
    await client.start(phone=PHONE)
    print("Connected!")

    # Get the abuse notifications bot
    abuse_bot = await client.get_entity("@AbuseNotifications")

    # Send the appeal command
    print("Sending appeal command...")
    await client.send_message(abuse_bot, "/appealbot8392597281")
    await asyncio.sleep(3)

    # Check response
    messages = await client.get_messages(abuse_bot, limit=1)
    print(f"Response: {messages[0].text}")

    # If it asks for explanation, send the appeal
    if "reason" in messages[0].text.lower() or "explain" in messages[0].text.lower() or "why" in messages[0].text.lower():
        print("Sending appeal explanation...")
        await client.send_message(abuse_bot, APPEAL_MESSAGE)
        await asyncio.sleep(3)
        messages = await client.get_messages(abuse_bot, limit=1)
        print(f"Final response: {messages[0].text}")

    await client.disconnect()
    print("Done!")

if __name__ == "__main__":
    asyncio.run(main())
