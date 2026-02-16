#!/usr/bin/env python3
"""
Setup Rose bot auto-responses for CA and Website
"""
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

from telethon import TelegramClient

API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
PHONE = os.getenv("TELEGRAM_PHONE")

# Private group only
GROUP_ID = -1003584948806

CONTRACT_ADDRESS = "0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b"

async def setup_rose_responses():
    # Kill any existing telegram bot first
    os.system("pkill -f telegram_ca_bot.py 2>/dev/null")
    await asyncio.sleep(2)

    client = TelegramClient("telegram_session", API_ID, API_HASH)
    await client.start(phone=PHONE)

    print("Connected to Telegram")
    group = await client.get_entity(GROUP_ID)
    print(f"Found group: {group.title}")

    # Rose filter commands
    # Format: /filter <keyword> <response>
    commands = [
        # CA response
        f'/filter ca 🌿 **$MON Contract Address:**\n\n`{CONTRACT_ADDRESS}`\n\n🔗 [DexScreener](https://dexscreener.com/monad/{CONTRACT_ADDRESS}) | [Buy on LFJ](https://lfj.gg/monad/trade?outputCurrency={CONTRACT_ADDRESS})\n\n*Powered by Grok AI* 🤖',

        # Website response
        '/filter website 🌿 **Ganja Mon Website:**\n\n🔗 https://grokandmon.com\n\nWatch di AI grow cannabis LIVE 24/7! 🤖',

        # Site alias
        '/filter site 🌿 **Ganja Mon Website:**\n\n🔗 https://grokandmon.com\n\nWatch di AI grow cannabis LIVE 24/7! 🤖',
    ]

    print("\nSetting up Rose auto-responses...")
    for cmd in commands:
        try:
            await client.send_message(group, cmd)
            keyword = cmd.split()[1]
            print(f"  ✓ Filter set for '{keyword}'")
            await asyncio.sleep(2)  # Rate limit
        except Exception as e:
            print(f"  ✗ Error: {e}")

    # List filters to confirm
    await asyncio.sleep(1)
    await client.send_message(group, "/filters")
    print("\n✅ Rose auto-responses configured!")
    print("Rose will now respond to: ca, website, site")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(setup_rose_responses())
