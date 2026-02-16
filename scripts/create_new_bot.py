#!/usr/bin/env python3
"""
Create a new Telegram bot via BotFather with innocent name.
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

# Innocent bot name - sounds like a community/gardening assistant
BOT_NAME = "Mon Garden Community"
BOT_USERNAME = "MonGardenBot"  # Must end in 'bot' or 'Bot'
BOT_DESCRIPTION = "Community gardening assistant for CA home growers. Legal cultivation tips under Prop 64 guidelines."
BOT_ABOUT = "AI-powered garden assistant. Community tips, growing advice, and chat for legal CA personal cultivation (Prop 64)."

async def main():
    print("Connecting to Telegram...")
    client = TelegramClient("telegram_session", API_ID, API_HASH)
    await client.start(phone=PHONE)
    print("Connected!")

    botfather = await client.get_entity("@BotFather")

    # Step 1: Create new bot
    print("\n--- Creating new bot ---")
    await client.send_message(botfather, "/newbot")
    await asyncio.sleep(2)

    messages = await client.get_messages(botfather, limit=1)
    print(f"BotFather: {messages[0].text[:100]}...")

    # Step 2: Send bot name
    print(f"Sending name: {BOT_NAME}")
    await client.send_message(botfather, BOT_NAME)
    await asyncio.sleep(2)

    messages = await client.get_messages(botfather, limit=1)
    print(f"BotFather: {messages[0].text[:100]}...")

    # Step 3: Send username
    print(f"Sending username: {BOT_USERNAME}")
    await client.send_message(botfather, BOT_USERNAME)
    await asyncio.sleep(3)

    messages = await client.get_messages(botfather, limit=1)
    response = messages[0].text
    print(f"BotFather: {response[:200]}...")

    # Extract token if successful
    if "token" in response.lower() or "HTTP API" in response:
        # Find the token in the message
        lines = response.split('\n')
        for line in lines:
            if ':' in line and 'AAF' in line or ':AAE' in line or ':AAG' in line:
                token = line.strip().split()[-1]
                if ':' in token:
                    print(f"\n*** NEW BOT TOKEN: {token} ***")

                    # Save to file
                    with open("/mnt/c/Users/natha/sol-cannabis/new_bot_token.txt", "w") as f:
                        f.write(f"Bot: @{BOT_USERNAME}\n")
                        f.write(f"Token: {token}\n")
                    print("Token saved to new_bot_token.txt")
                    break

        # Set description
        print("\n--- Setting bot description ---")
        await client.send_message(botfather, "/setdescription")
        await asyncio.sleep(1)
        await client.send_message(botfather, f"@{BOT_USERNAME}")
        await asyncio.sleep(1)
        await client.send_message(botfather, BOT_DESCRIPTION)
        await asyncio.sleep(2)

        # Set about
        print("--- Setting bot about ---")
        await client.send_message(botfather, "/setabouttext")
        await asyncio.sleep(1)
        await client.send_message(botfather, f"@{BOT_USERNAME}")
        await asyncio.sleep(1)
        await client.send_message(botfather, BOT_ABOUT)
        await asyncio.sleep(2)

        # Disable privacy mode (allow reading all group messages)
        print("--- Disabling privacy mode ---")
        await client.send_message(botfather, "/setprivacy")
        await asyncio.sleep(1)
        await client.send_message(botfather, f"@{BOT_USERNAME}")
        await asyncio.sleep(2)

        messages = await client.get_messages(botfather, limit=1)
        msg = messages[0]

        # Click Disable button if available
        if msg.reply_markup and isinstance(msg.reply_markup, ReplyInlineMarkup):
            for row in msg.reply_markup.rows:
                for button in row.buttons:
                    if "disable" in button.text.lower():
                        print(f"Clicking '{button.text}'...")
                        await msg.click(data=button.data)
                        await asyncio.sleep(2)
                        break
        else:
            await client.send_message(botfather, "Disable")
            await asyncio.sleep(2)

        messages = await client.get_messages(botfather, limit=1)
        print(f"Privacy setting: {messages[0].text[:100]}...")

        print("\n=== BOT CREATED SUCCESSFULLY ===")
    else:
        print("\nFailed to create bot. Username may be taken.")
        print(f"Full response: {response}")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
