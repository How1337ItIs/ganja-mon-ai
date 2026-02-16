#!/usr/bin/env python3
"""
Set bot profile picture via BotFather.
"""
import os
import asyncio
from dotenv import load_dotenv
load_dotenv()

from telethon import TelegramClient

API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
PHONE = os.getenv("TELEGRAM_PHONE")

BOT_USERNAME = "MonGardenBot"
IMAGE_PATH = "/mnt/c/Users/natha/sol-cannabis/assets/MON_official_logo.jpg"

async def main():
    print("Connecting to Telegram...")
    client = TelegramClient("telegram_session", API_ID, API_HASH)
    await client.start(phone=PHONE)
    print("Connected!")

    botfather = await client.get_entity("@BotFather")

    # Step 1: Start setuserpic command
    print("\n--- Setting bot profile picture ---")
    await client.send_message(botfather, "/setuserpic")
    await asyncio.sleep(2)

    messages = await client.get_messages(botfather, limit=1)
    print(f"BotFather: {messages[0].text[:100]}...")

    # Step 2: Select the bot
    print(f"Selecting bot: @{BOT_USERNAME}")
    await client.send_message(botfather, f"@{BOT_USERNAME}")
    await asyncio.sleep(2)

    messages = await client.get_messages(botfather, limit=1)
    print(f"BotFather: {messages[0].text[:100]}...")

    # Step 3: Send the image
    print(f"Uploading image: {IMAGE_PATH}")
    await client.send_file(botfather, IMAGE_PATH)
    await asyncio.sleep(3)

    messages = await client.get_messages(botfather, limit=1)
    response = messages[0].text if messages[0].text else "[Image received]"
    print(f"BotFather: {response[:200]}")

    if "success" in response.lower() or "done" in response.lower() or "photo" in response.lower():
        print("\n=== PROFILE PICTURE SET SUCCESSFULLY ===")
    else:
        print(f"\nFull response: {response}")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
