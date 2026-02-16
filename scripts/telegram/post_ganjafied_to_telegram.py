#!/usr/bin/env python3
"""
Post Ganjafied Profile Pictures to Telegram
============================================
Posts each ganjafied image to the Telegram group and tags the user.

Usage:
    python post_ganjafied_to_telegram.py --group -1003584948806
    python post_ganjafied_to_telegram.py --group "https://t.me/+Gr_AiuruKKUwOTlh" --dry-run
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from telethon import TelegramClient
from telethon.tl.types import InputPeerUser

# Config
API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
PHONE = os.getenv("TELEGRAM_PHONE")

BASE_DIR = Path(__file__).parent
GANJAFY_DIR = BASE_DIR / "output" / "ganjafied"

# 88 unique messages - one for each person, no repeats!
MESSAGES = [
    "{mention} just leveled up to rasta mode 🌿",
    "Jah blessed {mention} wit' di tam and dreads! 🦁",
    "{mention} looking irie today mon 💚💛❤️",
    "One Love {mention}! Di vibes are immaculate ✨",
    "{mention} got di ganja glow-up 🔥",
    "Blessed and highly favored {mention} 🍃",
    "{mention} transcended to di higher realm 🌴",
    "Welcome to di irie side {mention} 🌿",
    "{mention} unlocked: Rasta Achievement 🏆",
    "Di herb chose {mention} today 💨",
    "{mention} feeling di good vibrations now 🎵",
    "Positive vibes only {mention}! 💜",
    "{mention} ascended mon 🚀",
    "Jah provides for {mention} 🙏",
    "{mention} wit' di eternal sunshine ☀️",
    "{mention} reached peak irie status 🏔️",
    "Di universe blessed {mention} dis day 🌌",
    "{mention} on di path to enlightenment now 🛤️",
    "Respect to {mention} fi keeping it real 🤝",
    "{mention} joined di rasta renaissance 🎨",
    "Di vibes found {mention} worthy 🌊",
    "{mention} got di spiritual upgrade ⬆️",
    "Everything irie for {mention} now 🌈",
    "{mention} wit' di wisdom of di elders 👴",
    "Nature blessed {mention} today 🌳",
    "{mention} riding di wavelength 〰️",
    "Pure irie energy for {mention} 💫",
    "{mention} in perfect harmony now 🎶",
    "Di cosmos aligned for {mention} ⭐",
    "{mention} found di sacred path 🛕",
    "Meditation mode activated {mention} 🧘",
    "{mention} living di best timeline 📜",
    "Di herb spoke to {mention} 🗣️",
    "{mention} achieved maximum chill 😌",
    "Serenity unlocked for {mention} 🔓",
    "{mention} on di good frequency 📻",
    "Di tam chose {mention} 🎩",
    "{mention} accepted di calling 📞",
    "Cosmic vibes fo' {mention} 🪐",
    "{mention} in di zone now 🎯",
    "Di dreadlocks suit {mention} well 💈",
    "{mention} radiating peace ☮️",
    "Blessed beyond measure {mention} 📏",
    "{mention} wit' di golden aura ✨",
    "Di prophecy mentioned {mention} 📖",
    "{mention} found inner peace 🧘‍♀️",
    "Respect di journey {mention} 🚶",
    "{mention} embodying di spirit 👻",
    "Di ancestors smile on {mention} 😊",
    "Tranquility achieved {mention} 🕊️",
    "{mention} keeper of di vibes 🔑",
    "Di transformation suits {mention} 🦋",
    "{mention} reached di mountaintop ⛰️",
    "Harmony flows through {mention} 🌊",
    "{mention} wit' di blessed locks 🔒",
    "Di sacred smoke surrounds {mention} 💨",
    "Peace be wit' {mention} ✌️",
    "{mention} joined di circle ⭕",
    "Di tam fits {mention} perfectly 🎯",
    "Righteous vibes {mention}! 🙌",
    "{mention} walking di righteous path 🚶‍♂️",
    "Di energy is strong wit' {mention} ⚡",
    "{mention} living di dream now 💭",
    "Blessings upon {mention} 🌟",
    "{mention} found di light 💡",
    "Di dreads flow naturally on {mention} 🌊",
    "{mention} embraced di culture 🫂",
    "Serendipity blessed {mention} 🍀",
    "{mention} wit' di peaceful warrior energy ⚔️",
    "Di universe conspired fo' {mention} 🌍",
    "{mention} discovered di way 🧭",
    "Infinite blessings {mention} ♾️",
    "{mention} on di wavelength of love 📡",
    "Di sacred geometry chose {mention} 📐",
    "{mention} aligned wit' di cosmos 🌌",
    "Natural mystic surrounds {mention} 🌫️",
    "{mention} living proof of di blessings 📜",
    "Di transformation is complete {mention} ✅",
    "{mention} found di eternal groove 🎵",
    "Blessed frequencies for {mention} 📻",
    "{mention} keeper of di flame 🔥",
    "Di wisdom flows to {mention} 💧",
    "{mention} walking in greatness 👑",
    "Perfect timing for {mention} ⏰",
    "{mention} accepted di gift 🎁",
    "Di circle is complete wit' {mention} 🔄",
    "{mention} became legend today 📚",
    "Respect di vision {mention} 👁️",
    "{mention} channeling pure peace 🕊️",
]


class TelegramPoster:
    def __init__(self):
        self.client = None
        self.message_queue = []  # Shuffled message queue to avoid repeats

    def get_next_message(self):
        """Get next unique message - each person gets a different one"""
        if not self.message_queue:
            # First time: shuffle all 88 messages
            import random
            self.message_queue = MESSAGES.copy()
            random.shuffle(self.message_queue)
        return self.message_queue.pop(0)

    async def setup(self):
        """Initialize Telegram client"""
        session_path = BASE_DIR / "telegram_session"
        self.client = TelegramClient(str(session_path), API_ID, API_HASH)
        await self.client.start(phone=PHONE)
        print("✅ Connected to Telegram")

    async def get_group_entity(self, group_identifier):
        """Get the group entity from identifier"""
        try:
            # Handle invite links
            if 'joinchat' in str(group_identifier) or '+' in str(group_identifier):
                from telethon.tl.functions.messages import CheckChatInviteRequest
                hash_code = group_identifier.split('+')[-1] if '+' in group_identifier else group_identifier.split('/')[-1]
                invite_info = await self.client(CheckChatInviteRequest(hash_code))
                if hasattr(invite_info, 'chat'):
                    return invite_info.chat

            # Regular entity lookup
            return await self.client.get_entity(group_identifier)
        except Exception as e:
            print(f"❌ Could not find group: {e}")
            return None

    async def post_ganjafied_images(self, group_identifier, dry_run=False, delay=5):
        """Post all ganjafied images to the group"""
        # Get group entity
        group = await self.get_group_entity(group_identifier)
        if not group:
            return

        group_name = getattr(group, 'title', str(group_identifier))
        print(f"\n📱 Group: {group_name}")

        # Get all ganjafied images
        images = sorted(GANJAFY_DIR.glob("rasta_*.png"))
        if not images:
            print("❌ No ganjafied images found!")
            return

        print(f"📸 Found {len(images)} ganjafied images\n")

        if dry_run:
            print("🔍 DRY RUN MODE - No posts will be made\n")

        successful = 0
        failed = 0

        for i, image_path in enumerate(images, 1):
            try:
                # Parse filename: rasta_username_firstname_userid.png
                filename = image_path.stem  # Remove .png
                parts = filename.replace('rasta_', '').rsplit('_', 1)

                if len(parts) < 2:
                    print(f"⚠️  [{i}/{len(images)}] Skipping {image_path.name} - invalid filename format")
                    failed += 1
                    continue

                name_part = parts[0]
                user_id = int(parts[1])

                # Get user entity for proper mention
                try:
                    user = await self.client.get_entity(user_id)
                    username = user.username if user.username else name_part.split('_')[0]

                    # Create mention
                    if user.username:
                        mention = f"@{user.username}"
                    else:
                        # Use text mention for users without username
                        mention = f"[{user.first_name}](tg://user?id={user_id})"

                except Exception as e:
                    print(f"⚠️  [{i}/{len(images)}] Could not get user {user_id}: {e}")
                    mention = f"User {user_id}"

                # Get next message from shuffled queue (prevents consecutive repeats)
                message = self.get_next_message().format(mention=mention)

                print(f"📤 [{i}/{len(images)}] Posting for {username} (ID: {user_id})")
                print(f"   Message: {message}")

                if not dry_run:
                    # Send photo with caption
                    await self.client.send_file(
                        group,
                        str(image_path),
                        caption=message,
                        parse_mode='md'
                    )
                    successful += 1
                    print(f"   ✅ Posted!")

                    # Delay to avoid spam limits
                    if i < len(images):
                        print(f"   ⏳ Waiting {delay}s before next post...")
                        await asyncio.sleep(delay)
                else:
                    print(f"   [DRY RUN] Would post here")
                    successful += 1

            except Exception as e:
                print(f"   ❌ Failed: {e}")
                failed += 1
                continue

        # Summary
        print("\n" + "="*60)
        print("🎉 POSTING COMPLETE!")
        print("="*60)
        print(f"✅ Posted: {successful}")
        print(f"❌ Failed: {failed}")
        print("="*60 + "\n")

        await self.client.disconnect()


async def main():
    parser = argparse.ArgumentParser(
        description="Post ganjafied images to Telegram group",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--group", "-g",
        required=True,
        help="Telegram group username, @handle, chat ID, or invite link"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be posted without actually posting"
    )
    parser.add_argument(
        "--delay", "-d",
        type=int,
        default=5,
        help="Delay in seconds between posts (default: 5)"
    )

    args = parser.parse_args()

    poster = TelegramPoster()
    await poster.setup()
    await poster.post_ganjafied_images(
        args.group,
        dry_run=args.dry_run,
        delay=args.delay
    )


if __name__ == "__main__":
    asyncio.run(main())
