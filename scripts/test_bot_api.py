#!/usr/bin/env python3
"""
Test @GanjaMonBot using Telegram User API (Telethon).
This lets us interact with groups as a user to test the bot.
"""
import os
import asyncio
from dotenv import load_dotenv
load_dotenv()

from telethon import TelegramClient
from telethon.tl.functions.messages import GetFullChatRequest
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.types import Channel, Chat

API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
PHONE = os.getenv("TELEGRAM_PHONE")

BOT_USERNAME = "GanjaMonBot"

async def main():
    print("Connecting to Telegram as user...")
    client = TelegramClient("telegram_session", API_ID, API_HASH)
    await client.start(phone=PHONE)
    print("Connected!")

    # 1. Get the bot entity
    print(f"\n--- Getting @{BOT_USERNAME} info ---")
    try:
        bot = await client.get_entity(f"@{BOT_USERNAME}")
        print(f"Bot ID: {bot.id}")
        print(f"Bot name: {bot.first_name}")
    except Exception as e:
        print(f"Error getting bot: {e}")
        bot = None

    # 2. Find dialogs where the bot might be
    print("\n--- Scanning your chats for groups with the bot ---")
    groups_with_bot = []

    async for dialog in client.iter_dialogs():
        if dialog.is_group or dialog.is_channel:
            try:
                # Get participants for small groups or search for bot
                chat = dialog.entity
                chat_id = dialog.id

                # Check if it's a channel/supergroup
                if isinstance(chat, Channel):
                    # Try to find the bot in participants
                    async for participant in client.iter_participants(chat, limit=200):
                        if hasattr(participant, 'username') and participant.username == BOT_USERNAME:
                            groups_with_bot.append({
                                'name': dialog.name,
                                'id': chat_id,
                                'entity': chat
                            })
                            print(f"  Found bot in: {dialog.name} (ID: {chat_id})")
                            break
            except Exception as e:
                # Skip chats we can't access participants for
                pass

    print(f"\nFound bot in {len(groups_with_bot)} group(s)")

    # 3. Send a test message to the first group with the bot
    if groups_with_bot:
        test_group = groups_with_bot[0]
        print(f"\n--- Testing bot in '{test_group['name']}' (ID: {test_group['id']}) ---")

        # Send a message that should trigger the bot
        test_message = "yo what's good with the plant today? @GanjaMonBot"
        print(f"Sending: {test_message}")

        msg = await client.send_message(test_group['entity'], test_message)
        print(f"Message sent (ID: {msg.id})")

        # Wait for bot response
        print("Waiting 15 seconds for bot response...")
        await asyncio.sleep(15)

        # Check for new messages
        messages = await client.get_messages(test_group['entity'], limit=5)
        print("\n--- Recent messages in group ---")
        for m in reversed(messages):
            sender = "Bot" if hasattr(m.sender, 'bot') and m.sender.bot else (m.sender.first_name if m.sender else "Unknown")
            is_bot = hasattr(m.sender, 'bot') and m.sender.bot
            prefix = "🤖" if is_bot else "👤"
            text_preview = (m.text[:100] + "...") if m.text and len(m.text) > 100 else (m.text or "[no text]")
            print(f"  {prefix} {sender}: {text_preview}")
    else:
        print("\nNo groups found with the bot. Let's try direct message test...")

        # Test direct message to bot
        if bot:
            print(f"\n--- Sending DM to @{BOT_USERNAME} ---")
            test_dm = "/start"
            await client.send_message(bot, test_dm)
            print(f"Sent: {test_dm}")
            await asyncio.sleep(5)

            messages = await client.get_messages(bot, limit=3)
            print("\n--- Bot DM responses ---")
            for m in reversed(messages):
                print(f"  {m.text[:200] if m.text else '[no text]'}")

    # 4. Also list ALL your groups for debugging
    print("\n--- All your groups (for reference) ---")
    count = 0
    async for dialog in client.iter_dialogs():
        if dialog.is_group or dialog.is_channel:
            count += 1
            if count <= 10:
                print(f"  {dialog.name}: ID={dialog.id}")
    print(f"  ... total {count} groups")

    await client.disconnect()
    print("\nDone!")

if __name__ == "__main__":
    asyncio.run(main())
