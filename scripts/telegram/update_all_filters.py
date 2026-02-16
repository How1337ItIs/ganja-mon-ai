#!/usr/bin/env python3
"""Update all filters with correct X Community URL"""
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
X_COMMUNITY = "https://x.com/i/communities/2014085599985291752"

async def update_filters():
    client = TelegramClient("telegram_session", API_ID, API_HASH)
    await client.start(phone=PHONE)

    group = await client.get_entity(GROUP_ID)
    print(f"Connected to: {group.title}")

    ca_response = f"""🌿 **$MON Contract Address:**

`{CONTRACT_ADDRESS}`

🔗 [DexScreener](https://dexscreener.com/monad/{CONTRACT_ADDRESS}) | [Buy on LFJ](https://lfj.gg/monad/trade?outputCurrency={CONTRACT_ADDRESS})

📱 [X/Twitter](https://x.com/GanjaMonAI) | [X Community]({X_COMMUNITY})

*Powered by Grok AI* 🤖"""

    website_response = f"""🌿 **Ganja Mon Website:**

🔗 https://grokandmon.com

📱 [X/Twitter](https://x.com/GanjaMonAI) | [X Community]({X_COMMUNITY})

Watch di AI grow cannabis LIVE 24/7! 🤖"""

    socials_response = f"""🌿 **Ganja Mon Socials:**

📱 [X/Twitter](https://x.com/GanjaMonAI)
👥 [X Community]({X_COMMUNITY})

Follow fi di latest updates! 🤖"""

    commands = [
        f'/filter ca {ca_response}',
        f'/filter website {website_response}',
        f'/filter site {website_response}',
        f'/filter twitter {socials_response}',
        f'/filter x {socials_response}',
    ]

    print("\nUpdating all filters with correct X Community URL...")
    for cmd in commands:
        await client.send_message(group, cmd)
        keyword = cmd.split()[1]
        print(f"  ✓ {keyword}")
        await asyncio.sleep(2)

    print("\n✅ All filters updated!")
    await client.disconnect()

asyncio.run(update_filters())
