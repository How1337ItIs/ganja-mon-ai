#!/usr/bin/env python3
"""Remove Rose auto-response filters (Safeguard handles it)"""
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

from telethon import TelegramClient

API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
PHONE = os.getenv("TELEGRAM_PHONE")
GROUP_ID = -1003584948806

async def remove_filters():
    client = TelegramClient("telegram_session", API_ID, API_HASH)
    await client.start(phone=PHONE)

    group = await client.get_entity(GROUP_ID)
    print(f"Connected to: {group.title}")

    # Remove Rose filters
    commands = ["/stop ca", "/stop website", "/stop site"]

    for cmd in commands:
        await client.send_message(group, cmd)
        print(f"✓ {cmd}")
        await asyncio.sleep(1.5)

    print("\n✅ Rose filters removed - Safeguard handles responses now")
    await client.disconnect()

asyncio.run(remove_filters())
