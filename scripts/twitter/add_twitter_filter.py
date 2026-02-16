#!/usr/bin/env python3
"""Add twitter/x filter"""
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

from telethon import TelegramClient

API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
PHONE = os.getenv("TELEGRAM_PHONE")
GROUP_ID = -1003584948806

async def add_filter():
    client = TelegramClient("telegram_session", API_ID, API_HASH)
    await client.start(phone=PHONE)

    group = await client.get_entity(GROUP_ID)

    twitter_response = """🌿 **Ganja Mon Socials:**

📱 [X/Twitter](https://x.com/ganjamonai)
👥 [X Community](https://x.com/i/communities/1884077569498071258)

Follow fi di latest updates! 🤖"""

    commands = [
        f'/filter twitter {twitter_response}',
        f'/filter x {twitter_response}',
    ]

    for cmd in commands:
        await client.send_message(group, cmd)
        keyword = cmd.split()[1]
        print(f"✓ Filter set for '{keyword}'")
        await asyncio.sleep(2)

    print("✅ Twitter/X filters added!")
    await client.disconnect()

asyncio.run(add_filter())
