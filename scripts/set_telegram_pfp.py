#!/usr/bin/env python3
"""
Set Telegram profile picture using Telethon.
Uses the existing session from telegram_ca_bot.py.
"""
import os
import asyncio
from dotenv import load_dotenv
load_dotenv()

from telethon import TelegramClient
from telethon.tl.functions.photos import UploadProfilePhotoRequest

# Telegram config from .env
API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
PHONE = os.getenv("TELEGRAM_PHONE")

# Logo path
LOGO_PATH = "/mnt/c/Users/natha/sol-cannabis/assets/MON_official_logo.jpg"

async def main():
    print("Connecting to Telegram...")
    client = TelegramClient("telegram_session", API_ID, API_HASH)
    await client.start(phone=PHONE)

    print("Connected! Uploading profile photo...")

    # Upload the photo
    photo = await client.upload_file(LOGO_PATH)

    # Set it as profile photo
    result = await client(UploadProfilePhotoRequest(file=photo))

    print("Profile photo set successfully!")
    print(f"Photo ID: {result.photo.id}")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
