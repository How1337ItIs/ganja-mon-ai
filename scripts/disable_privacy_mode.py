#!/usr/bin/env python3
"""
Disable Group Privacy Mode for @GanjaMonBot via @BotFather.
This allows the bot to see all group messages, not just commands/mentions.
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

BOT_USERNAME = "GanjaMonBot"

async def main():
    print("Connecting to Telegram...")
    client = TelegramClient("telegram_session", API_ID, API_HASH)
    await client.start(phone=PHONE)
    print("Connected!")

    botfather = await client.get_entity("@BotFather")

    # Step 1: Send /setprivacy command
    print("Sending /setprivacy...")
    await client.send_message(botfather, "/setprivacy")
    await asyncio.sleep(2)

    # Get response - should ask which bot
    messages = await client.get_messages(botfather, limit=1)
    print(f"Response: {messages[0].text[:100]}...")

    # Step 2: Send bot username
    print(f"Selecting @{BOT_USERNAME}...")
    await client.send_message(botfather, f"@{BOT_USERNAME}")
    await asyncio.sleep(2)

    # Get response with privacy options
    messages = await client.get_messages(botfather, limit=1)
    msg = messages[0]
    print(f"Response: {msg.text[:200]}...")

    # Step 3: Click "Disable" button if available, or send "Disable"
    if msg.reply_markup and isinstance(msg.reply_markup, ReplyInlineMarkup):
        for row in msg.reply_markup.rows:
            for button in row.buttons:
                if "disable" in button.text.lower():
                    print(f"Clicking '{button.text}'...")
                    await msg.click(data=button.data)
                    await asyncio.sleep(2)
                    break
    else:
        # No buttons, send text
        print("Sending 'Disable'...")
        await client.send_message(botfather, "Disable")
        await asyncio.sleep(2)

    # Check final response
    messages = await client.get_messages(botfather, limit=1)
    print(f"\nFinal response: {messages[0].text}")

    await client.disconnect()
    print("\nDone! Bot should now be able to read all group messages.")

if __name__ == "__main__":
    asyncio.run(main())
