#!/usr/bin/env python3
"""Test the new @MonPlantBot to verify it's not being censored."""
import os
import asyncio
from dotenv import load_dotenv
load_dotenv()

from telethon import TelegramClient

API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
PHONE = os.getenv("TELEGRAM_PHONE")

async def main():
    print("Connecting to Telegram...")
    client = TelegramClient("telegram_session", API_ID, API_HASH)
    await client.start(phone=PHONE)
    print("Connected!")

    # Get the new bot
    bot = await client.get_entity("@MonPlantBot")
    print(f"Bot: {bot.first_name} (ID: {bot.id})")

    # Send /start to the bot
    print("\n--- Sending /start to @MonPlantBot ---")
    await client.send_message(bot, "/start")
    await asyncio.sleep(5)

    # Check bot response
    messages = await client.get_messages(bot, limit=5)
    print("\n--- Bot Response ---")
    for m in reversed(messages):
        is_from_bot = m.sender_id == bot.id
        prefix = "[BOT]" if is_from_bot else "[YOU]"
        text = m.text[:500] if m.text else "[no text]"
        print(f"{prefix}: {text}\n")

    # Check if response contains the TOS violation message
    for m in messages:
        if m.sender_id == bot.id and m.text:
            if "violated Telegram's Terms of Service" in m.text:
                print("\n❌ BOT IS STILL CENSORED! The TOS warning appeared.")
            else:
                print("\n✅ BOT IS WORKING! No censorship detected.")
            break

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
