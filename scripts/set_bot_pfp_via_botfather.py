#!/usr/bin/env python3
"""
Set Telegram bot profile picture via @BotFather using Telethon.
"""
import os
import asyncio
from dotenv import load_dotenv
load_dotenv()

from telethon import TelegramClient
from telethon.tl.types import ReplyInlineMarkup

API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
PHONE = os.getenv("TELEGRAM_PHONE")

LOGO_PATH = "/mnt/c/Users/natha/sol-cannabis/assets/MON_official_logo.jpg"
BOT_USERNAME = "GanjaMonBot"  # The bot we want to set pfp for

async def main():
    print("Connecting to Telegram...")
    client = TelegramClient("telegram_session", API_ID, API_HASH)
    await client.start(phone=PHONE)
    print("Connected!")

    botfather = await client.get_entity("@BotFather")

    # Step 1: Send /mybots
    print("Sending /mybots...")
    await client.send_message(botfather, "/mybots")
    await asyncio.sleep(2)

    # Get the response with bot list
    messages = await client.get_messages(botfather, limit=1)
    msg = messages[0]

    # Find and click the button for our bot
    if msg.reply_markup and isinstance(msg.reply_markup, ReplyInlineMarkup):
        for row in msg.reply_markup.rows:
            for button in row.buttons:
                if BOT_USERNAME.lower() in button.text.lower():
                    print(f"Clicking on {button.text}...")
                    await msg.click(data=button.data)
                    await asyncio.sleep(2)
                    break

    # Get response with bot options
    messages = await client.get_messages(botfather, limit=1)
    msg = messages[0]

    # Click "Edit Bot"
    if msg.reply_markup:
        for row in msg.reply_markup.rows:
            for button in row.buttons:
                if "edit bot" in button.text.lower():
                    print("Clicking Edit Bot...")
                    await msg.click(data=button.data)
                    await asyncio.sleep(2)
                    break

    # Get response with edit options
    messages = await client.get_messages(botfather, limit=1)
    msg = messages[0]

    # Click "Edit Botpic"
    if msg.reply_markup:
        for row in msg.reply_markup.rows:
            for button in row.buttons:
                if "botpic" in button.text.lower():
                    print("Clicking Edit Botpic...")
                    await msg.click(data=button.data)
                    await asyncio.sleep(2)
                    break

    # Now send the image
    print(f"Sending logo image: {LOGO_PATH}")
    await client.send_file(botfather, LOGO_PATH)
    await asyncio.sleep(2)

    # Check response
    messages = await client.get_messages(botfather, limit=1)
    print(f"BotFather response: {messages[0].text}")

    await client.disconnect()
    print("Done!")

if __name__ == "__main__":
    asyncio.run(main())
