#!/usr/bin/env python3
"""Quick check of bot DM content."""
import os
import asyncio
from dotenv import load_dotenv
load_dotenv()

from telethon import TelegramClient

API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
PHONE = os.getenv("TELEGRAM_PHONE")

async def main():
    print("Connecting...")
    client = TelegramClient("telegram_session", API_ID, API_HASH)
    await client.start(phone=PHONE)

    bot = await client.get_entity("@GanjaMonBot")
    print(f"Bot: {bot.first_name} (ID: {bot.id})")

    print("\n--- All messages with bot ---")
    messages = await client.get_messages(bot, limit=10)
    for m in reversed(messages):
        is_from_bot = m.sender_id == bot.id
        prefix = "[BOT]" if is_from_bot else "[YOU]"
        text = m.text[:300] if m.text else "[no text]"
        print(f"{prefix} ({m.date}): {text}")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
