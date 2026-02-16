#!/usr/bin/env python3
"""Setup Safeguard auto-responses with X links"""
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

from telethon import TelegramClient

API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
PHONE = os.getenv("TELEGRAM_PHONE")
GROUP_ID = -1003584948806

CONTRACT_ADDRESS = "0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b"

async def setup_responses():
    client = TelegramClient("telegram_session", API_ID, API_HASH)
    await client.start(phone=PHONE)

    group = await client.get_entity(GROUP_ID)
    print(f"Connected to: {group.title}")

    # Try Rose-style filter commands (may work for Safeguard too)
    ca_response = f"""🌿 **$MON Contract Address:**

`{CONTRACT_ADDRESS}`

🔗 [DexScreener](https://dexscreener.com/monad/{CONTRACT_ADDRESS}) | [Buy on LFJ](https://lfj.gg/monad/trade?outputCurrency={CONTRACT_ADDRESS})

📱 [X/Twitter](https://x.com/ganjamonai) | [X Community](https://x.com/i/communities/1884077569498071258)

*Powered by Grok AI* 🤖"""

    website_response = """🌿 **Ganja Mon Website:**

🔗 https://grokandmon.com

📱 [X/Twitter](https://x.com/ganjamonai) | [X Community](https://x.com/i/communities/1884077569498071258)

Watch di AI grow cannabis LIVE 24/7! 🤖"""

    commands = [
        f'/filter ca {ca_response}',
        f'/filter website {website_response}',
        f'/filter site {website_response}',
    ]

    print("\nSetting up auto-responses...")
    for cmd in commands:
        try:
            await client.send_message(group, cmd)
            keyword = cmd.split()[1]
            print(f"  ✓ Filter set for '{keyword}'")
            await asyncio.sleep(2)
        except Exception as e:
            print(f"  ✗ Error: {e}")

    print("\n✅ Auto-responses configured with X links!")
    await client.disconnect()

asyncio.run(setup_responses())
