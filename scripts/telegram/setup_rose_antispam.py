#!/usr/bin/env python3
"""
Setup Rose bot anti-spam for Ganja Mon private group
"""
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

from telethon import TelegramClient
from telethon.tl.functions.channels import InviteToChannelRequest

API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
PHONE = os.getenv("TELEGRAM_PHONE")

# Private group only (not the public portal)
GROUP_ID = -1003584948806

async def setup_rose():
    client = TelegramClient("telegram_session", API_ID, API_HASH)
    await client.start(phone=PHONE)

    print("Connected to Telegram")

    # Get the group entity
    group = await client.get_entity(GROUP_ID)
    print(f"Found group: {group.title}")

    # Try to add Rose bot
    try:
        rose = await client.get_entity("@MissRose_bot")
        await client(InviteToChannelRequest(group, [rose]))
        print("✅ Added @MissRose_bot to group")
    except Exception as e:
        print(f"Note: {e}")
        print("Rose may already be in the group or needs manual add as admin")

    # Send config commands - just global antispam database
    commands = [
        "/antispam on",           # Block known spam accounts from Rose's global database
    ]

    print("\nSending config commands...")
    for cmd in commands:
        try:
            await client.send_message(group, cmd)
            print(f"  ✓ {cmd}")
            await asyncio.sleep(1.5)  # Rate limit
        except Exception as e:
            print(f"  ✗ {cmd}: {e}")

    print("\n✅ Anti-spam configured for Ganja $Mon AI private group!")
    print("\nIMPORTANT: Make sure @MissRose_bot is promoted to admin with delete messages permission!")
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(setup_rose())
