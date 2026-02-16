#!/usr/bin/env python3
"""
Create a test group and add @GanjaMonBot to it, or DM the bot directly.
This initializes the bot so it can function properly.
"""
import os
import asyncio
from dotenv import load_dotenv
load_dotenv()

from telethon import TelegramClient
from telethon.tl.functions.channels import CreateChannelRequest, InviteToChannelRequest
from telethon.tl.functions.messages import AddChatUserRequest

API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
PHONE = os.getenv("TELEGRAM_PHONE")

BOT_USERNAME = "GanjaMonBot"

async def main():
    print("Connecting to Telegram as user...")
    client = TelegramClient("telegram_session", API_ID, API_HASH)
    await client.start(phone=PHONE)
    print("Connected!")

    # Get the bot entity
    print(f"\n--- Getting @{BOT_USERNAME} ---")
    bot = await client.get_entity(f"@{BOT_USERNAME}")
    print(f"Bot: {bot.first_name} (ID: {bot.id})")

    # Option 1: Send a DM to the bot to start conversation
    print(f"\n--- Sending DM to @{BOT_USERNAME} ---")
    await client.send_message(bot, "/start")
    await asyncio.sleep(2)

    # Check bot response
    messages = await client.get_messages(bot, limit=3)
    print("DM Response:")
    for m in messages:
        if m.text:
            print(f"  {m.text[:200]}")

    # Option 2: List existing groups and see if we can add bot
    print("\n--- Checking existing groups ---")
    groups_found = []
    async for dialog in client.iter_dialogs():
        if dialog.is_group and not dialog.entity.broadcast:
            groups_found.append({
                'name': dialog.name,
                'id': dialog.id,
                'entity': dialog.entity
            })
            if len(groups_found) <= 5:
                print(f"  {dialog.name} (ID: {dialog.id})")

    print(f"\nFound {len(groups_found)} groups total")

    if groups_found:
        # Try to add bot to the first group
        target_group = groups_found[0]
        print(f"\n--- Attempting to add bot to '{target_group['name']}' ---")

        try:
            # For supergroups (channels)
            await client(InviteToChannelRequest(
                channel=target_group['entity'],
                users=[bot]
            ))
            print(f"Successfully added @{BOT_USERNAME} to {target_group['name']}!")
        except Exception as e:
            print(f"Failed to add bot: {e}")

            # Maybe it's already there, try sending a message
            print("\nTrying to mention the bot in the group...")
            try:
                await client.send_message(
                    target_group['entity'],
                    f"yo @{BOT_USERNAME} what's good with the plant? test message"
                )
                print("Message sent to group!")

                # Wait for bot response
                await asyncio.sleep(5)

                # Check recent messages
                messages = await client.get_messages(target_group['entity'], limit=5)
                print("\nRecent group messages:")
                for m in messages:
                    sender_name = m.sender.first_name if m.sender else "Unknown"
                    is_bot = hasattr(m.sender, 'bot') and m.sender.bot
                    prefix = "[BOT]" if is_bot else "[USER]"
                    if m.text:
                        print(f"  {prefix} {sender_name}: {m.text[:100]}")
            except Exception as e2:
                print(f"Failed to send message: {e2}")

    # Wait and check for any bot responses
    print("\n--- Waiting 10 seconds for bot responses ---")
    await asyncio.sleep(10)

    # Check DM for response
    messages = await client.get_messages(bot, limit=3)
    print("\nFinal DM messages:")
    for m in messages:
        if m.text:
            print(f"  {m.text[:200]}")

    await client.disconnect()
    print("\nDone!")

if __name__ == "__main__":
    asyncio.run(main())
