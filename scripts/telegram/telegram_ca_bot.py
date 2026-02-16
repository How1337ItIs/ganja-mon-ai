#!/usr/bin/env python3
"""
Telegram CA Auto-Responder Bot

Automatically replies with the $MON contract address when someone types "ca" in chat.
Uses Telethon (user account API) to monitor and respond in groups.

Usage:
    python telegram_ca_bot.py

Set the CA below before running.
"""
import os
import re
import asyncio
from dotenv import load_dotenv
load_dotenv()

from telethon import TelegramClient, events

# ============================================
# CONFIGURATION - SET YOUR CA HERE
# ============================================
CONTRACT_ADDRESS = "0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b"

# Response message when someone asks for CA
CA_RESPONSE = f"""🌿 **$MON Contract Address:**

`{CONTRACT_ADDRESS}`

🔗 [DexScreener](https://dexscreener.com/monad/{CONTRACT_ADDRESS}) | [Buy on LFJ](https://lfj.gg/monad/trade?outputCurrency={CONTRACT_ADDRESS})

*Powered by Grok AI* 🤖"""

# ============================================
# TELEGRAM CONFIG (from .env)
# ============================================
API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
PHONE = os.getenv("TELEGRAM_PHONE")

# Pattern to match "ca", "CA", "ca?", "what's the ca", etc.
CA_PATTERN = re.compile(r'\b(ca|CA|Ca)\b[\?\!]?$|what.*ca\??|contract.*address', re.IGNORECASE)

# Pattern to match "website", "site", "link"
WEBSITE_PATTERN = re.compile(r'\b(website|site)\b[\?\!]?$', re.IGNORECASE)

WEBSITE_RESPONSE = """🌿 **Ganja Mon Website:**

🔗 https://grokandmon.com

Watch di AI grow cannabis LIVE 24/7! 🤖"""


async def main():
    print("🚀 Starting Telegram CA Bot...")
    print(f"📋 Contract Address: {CONTRACT_ADDRESS}")

    if CONTRACT_ADDRESS == "PASTE_YOUR_CA_HERE":
        print("\n⚠️  WARNING: You need to set the CONTRACT_ADDRESS in the script!")
        print("   Edit telegram_ca_bot.py and replace PASTE_YOUR_CA_HERE with your actual CA")
        return

    client = TelegramClient("telegram_session", API_ID, API_HASH)
    await client.start(phone=PHONE)

    print("✅ Connected to Telegram")
    print("👀 Listening for 'ca' messages in all chats...\n")

    @client.on(events.NewMessage(pattern=CA_PATTERN))
    async def ca_handler(event):
        # Don't respond to our own messages
        me = await client.get_me()
        if event.sender_id == me.id:
            return

        # Get chat info for logging
        chat = await event.get_chat()
        chat_name = getattr(chat, 'title', 'DM')
        sender = await event.get_sender()
        sender_name = getattr(sender, 'first_name', 'Unknown')

        print(f"📨 CA request from {sender_name} in {chat_name}")
        print(f"   Message: {event.text}")

        # Reply with the CA
        await event.reply(CA_RESPONSE, parse_mode='markdown')
        print(f"✅ Replied with CA\n")

    @client.on(events.NewMessage(pattern=WEBSITE_PATTERN))
    async def website_handler(event):
        # Don't respond to our own messages
        me = await client.get_me()
        if event.sender_id == me.id:
            return

        chat = await event.get_chat()
        chat_name = getattr(chat, 'title', 'DM')
        sender = await event.get_sender()
        sender_name = getattr(sender, 'first_name', 'Unknown')

        print(f"🌐 Website request from {sender_name} in {chat_name}")
        await event.reply(WEBSITE_RESPONSE, parse_mode='markdown')
        print(f"✅ Replied with website\n")

    print("=" * 50)
    print("Bot is running! Press Ctrl+C to stop.")
    print("=" * 50)

    await client.run_until_disconnected()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped.")
