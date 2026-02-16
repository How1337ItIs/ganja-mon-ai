#!/usr/bin/env python3
"""Check recent messages in the Ganja Mon Warroom."""
import os
import asyncio
from dotenv import load_dotenv
load_dotenv()

from telethon import TelegramClient

API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
PHONE = os.getenv("TELEGRAM_PHONE")

GROUP_ID = -5281228293  # Ganja Mon Warroom

async def main():
    client = TelegramClient("telegram_session", API_ID, API_HASH)
    await client.start(phone=PHONE)

    print("Recent messages in Ganja Mon Warroom:\n")
    async for msg in client.iter_messages(GROUP_ID, limit=10):
        sender = "BOT @MonGardenBot" if msg.sender_id == 7077568199 else f"User({msg.sender_id})"
        text = msg.text[:200] if msg.text else "[non-text]"
        print(f"[{sender}]: {text}\n")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
