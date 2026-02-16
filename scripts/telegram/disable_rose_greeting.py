#!/usr/bin/env python3
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()
from telethon import TelegramClient

API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
PHONE = os.getenv("TELEGRAM_PHONE")
GROUP_ID = -1003584948806

async def disable_greeting():
    client = TelegramClient("telegram_session", API_ID, API_HASH)
    await client.start(phone=PHONE)
    group = await client.get_entity(GROUP_ID)
    await client.send_message(group, "/welcome off")
    print("✅ Rose greeting disabled")
    await client.disconnect()

asyncio.run(disable_greeting())
