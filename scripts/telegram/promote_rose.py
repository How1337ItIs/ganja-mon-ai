#!/usr/bin/env python3
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

from telethon import TelegramClient
from telethon.tl.functions.channels import EditAdminRequest
from telethon.tl.types import ChatAdminRights

API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
PHONE = os.getenv("TELEGRAM_PHONE")
GROUP_ID = -1003584948806

async def promote_rose():
    client = TelegramClient("telegram_session", API_ID, API_HASH)
    await client.start(phone=PHONE)

    group = await client.get_entity(GROUP_ID)
    rose = await client.get_entity("@MissRose_bot")

    rights = ChatAdminRights(
        delete_messages=True,
        ban_users=True,
    )

    await client(EditAdminRequest(group, rose, rights, "Anti-Spam"))
    print("✅ Rose promoted to admin with delete + ban permissions")
    await client.disconnect()

asyncio.run(promote_rose())
