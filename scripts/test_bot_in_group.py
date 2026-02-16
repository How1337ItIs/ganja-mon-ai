#!/usr/bin/env python3
"""
Test the bot in the group by sending a message that should trigger it.
"""
import os
import asyncio
from dotenv import load_dotenv
load_dotenv()

from telethon import TelegramClient

API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
PHONE = os.getenv("TELEGRAM_PHONE")

GROUP_ID = -5281228293  # Ganja Mon Warroom

async def main():
    print("Connecting to Telegram...")
    client = TelegramClient("telegram_session", API_ID, API_HASH)
    await client.start(phone=PHONE)
    print("Connected!")

    # Send a message to test the bot
    print(f"\nSending test message to group...")
    await client.send_message(GROUP_ID, "@MonGardenBot yo mon, you there?")
    print("Message sent! Check group for bot response.")

    await asyncio.sleep(2)

    # Get recent messages to see if bot responded
    print("\nRecent messages in group:")
    async for msg in client.iter_messages(GROUP_ID, limit=5):
        sender = "Bot" if msg.sender_id == 7077568199 else f"User({msg.sender_id})"
        text = msg.text[:100] if msg.text else "[non-text]"
        print(f"  {sender}: {text}")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
