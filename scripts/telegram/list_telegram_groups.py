#!/usr/bin/env python3
"""
List all Telegram groups you're a member of
"""
import os
import asyncio
from dotenv import load_dotenv
load_dotenv()

from telethon import TelegramClient
from telethon.tl.types import Channel, Chat

API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
PHONE = os.getenv("TELEGRAM_PHONE")

async def list_groups():
    client = TelegramClient("telegram_session", API_ID, API_HASH)
    await client.start(phone=PHONE)

    print("\n" + "="*70)
    print("YOUR TELEGRAM GROUPS")
    print("="*70 + "\n")

    async for dialog in client.iter_dialogs():
        if isinstance(dialog.entity, (Channel, Chat)):
            chat_id = dialog.entity.id
            title = dialog.title
            username = getattr(dialog.entity, 'username', None)

            # Format chat ID (add -100 prefix for supergroups)
            if isinstance(dialog.entity, Channel):
                formatted_id = f"-100{chat_id}"
            else:
                formatted_id = f"-{chat_id}"

            print(f"📱 {title}")
            print(f"   ID: {formatted_id}")
            if username:
                print(f"   Username: @{username}")
            print()

    await client.disconnect()
    print("="*70)
    print("Copy the chat ID for your group and use it with --group")
    print("="*70 + "\n")

if __name__ == "__main__":
    asyncio.run(list_groups())
