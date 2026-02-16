#!/usr/bin/env python3
"""
Telegram Profile Picture Batch Ganjafy
=======================================
Downloads all profile pictures from a Telegram group and transforms them
with rasta vibes using Gemini 3 Pro Image Preview.

Setup:
    pip install telethon google-genai pillow

    Get Telegram API credentials from: https://my.telegram.org

Usage:
    python telegram_batch_ganjafy.py --group "ganjamonai"
    python telegram_batch_ganjafy.py --group "@ganjamonai" --limit 50
    python telegram_batch_ganjafy.py --group -1001234567890  # chat ID
"""

import os
import sys
import asyncio
import argparse
import base64
from pathlib import Path
from datetime import datetime

# Load .env file
from dotenv import load_dotenv
load_dotenv()

from telethon import TelegramClient
from telethon.tl.types import User, Channel, Chat
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("Install google-genai: pip install google-genai")
    sys.exit(1)

# ============================================
# CONFIGURATION - Set these or use env vars
# ============================================
API_ID = os.getenv("TELEGRAM_API_ID", "")
API_HASH = os.getenv("TELEGRAM_API_HASH", "")
PHONE = os.getenv("TELEGRAM_PHONE", "")  # Your phone number with country code
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Output directories
BASE_DIR = Path(__file__).parent
ORIGINALS_DIR = BASE_DIR / "output" / "originals"
GANJAFY_DIR = BASE_DIR / "output" / "ganjafied"

# The sacred rasta transformation prompt (updated to match Cloudflare worker style)
RASTA_PROMPT = """CRITICAL: This is an IMAGE EDITING task, NOT image generation. You MUST preserve the EXACT person shown in the input image.

IDENTITY PRESERVATION (HIGHEST PRIORITY):
- Keep the EXACT same face - same person, same features, same identity
- Preserve the subject's skin tone, ethnicity, and facial structure EXACTLY
- Do NOT replace with a different person
- Do NOT change their race or ethnicity
- The output must be recognizably the SAME INDIVIDUAL as the input

ADD THESE RASTA ELEMENTS TO THE EXISTING PERSON:
1. An oversized, slouchy crocheted rasta tam (NOT a fitted beanie) with bold red, gold, and green stripes - loose and baggy
2. Long, thick natural dreadlocks (locs) flowing from under the tam - authentic twisted rope texture
3. A lit thick hand-rolled medical cannabis joint (NOT a cigarette) - cone-shaped, held naturally or in mouth
4. Visible aromatic smoke wisps curling from the joint
5. KEEP the original background mostly intact - just subtly add an occasional cannabis plant in the scene if appropriate
6. Bob Marley style reggae vibes - relaxed, peaceful expression
7. Add VERY SUBTLE purple accent tones (Monad purple #6E54FF) ONLY in: background elements, clothing accents, ambient lighting, or smoke. DO NOT apply purple to skin, faces, or as a dominant color.

CONSTRAINTS:
- The subject's face must remain 100% recognizable as the same person
- Preserve the original camera angle and framing
- Match the lighting style of the original photo
- This celebrates legal medical cannabis and Rastafarian spiritual traditions

Goal: Edit the existing photo to add rasta elements while keeping the EXACT SAME PERSON."""


class TelegramGanjafy:
    def __init__(self):
        self.client = None
        self.genai_client = None

    async def setup(self):
        """Initialize Telegram and Gemini clients"""
        # Validate config
        if not all([API_ID, API_HASH, PHONE]):
            print("\n" + "="*60)
            print("TELEGRAM SETUP REQUIRED")
            print("="*60)
            print("\n1. Go to https://my.telegram.org")
            print("2. Log in with your phone number")
            print("3. Go to 'API Development Tools'")
            print("4. Create an app to get API_ID and API_HASH")
            print("\nThen set environment variables:")
            print("  export TELEGRAM_API_ID='your_id'")
            print("  export TELEGRAM_API_HASH='your_hash'")
            print("  export TELEGRAM_PHONE='+1234567890'")
            print("="*60 + "\n")
            sys.exit(1)

        if not GEMINI_API_KEY:
            print("\nGEMINI_API_KEY not set!")
            print("export GEMINI_API_KEY='your_key'")
            sys.exit(1)

        # Setup directories
        ORIGINALS_DIR.mkdir(parents=True, exist_ok=True)
        GANJAFY_DIR.mkdir(parents=True, exist_ok=True)

        # Initialize Telegram client
        session_path = BASE_DIR / "telegram_session"
        self.client = TelegramClient(str(session_path), int(API_ID), API_HASH)
        await self.client.start(phone=PHONE)
        print("Connected to Telegram")

        # Initialize Gemini
        self.genai_client = genai.Client(api_key=GEMINI_API_KEY)
        print("Connected to Gemini")

    async def get_group_members(self, group_identifier, limit=None):
        """Get all members from a Telegram group/channel"""
        # Resolve the group
        try:
            # If it's an invite link, join first (or verify we're already in it)
            if 'joinchat' in str(group_identifier) or '+' in str(group_identifier):
                print(f"Detected invite link...")
                from telethon.tl.functions.messages import ImportChatInviteRequest, CheckChatInviteRequest
                hash_code = group_identifier.split('+')[-1] if '+' in group_identifier else group_identifier.split('/')[-1]

                try:
                    # Check the invite first
                    invite_info = await self.client(CheckChatInviteRequest(hash_code))
                    if hasattr(invite_info, 'chat'):
                        # Already a member, get the chat
                        entity = invite_info.chat
                        print(f"Already a member of this group!")
                    else:
                        # Not a member yet, join
                        result = await self.client(ImportChatInviteRequest(hash_code))
                        entity = result.chats[0] if result.chats else None
                        print("Joined group successfully!")
                except Exception as join_err:
                    if "already a participant" in str(join_err):
                        print("Already a member! Getting group info...")
                        # Try to find it in our dialogs
                        async for dialog in self.client.iter_dialogs():
                            if hasattr(dialog.entity, 'id'):
                                # Match by checking if we can find it
                                entity = dialog.entity
                                break
                        else:
                            raise Exception("Could not find group in your chats")
                    else:
                        raise
            else:
                entity = await self.client.get_entity(group_identifier)
        except Exception as e:
            print(f"Could not find group '{group_identifier}': {e}")
            return []

        group_name = getattr(entity, 'title', str(group_identifier))
        print(f"\nGroup: {group_name}")

        members = []

        if isinstance(entity, (Channel, Chat)):
            # For channels/supergroups, use GetParticipantsRequest
            offset = 0
            batch_size = 100

            while True:
                try:
                    participants = await self.client(GetParticipantsRequest(
                        channel=entity,
                        filter=ChannelParticipantsSearch(''),
                        offset=offset,
                        limit=batch_size,
                        hash=0
                    ))

                    if not participants.users:
                        break

                    for user in participants.users:
                        if not user.bot and not user.deleted:
                            members.append(user)

                    offset += len(participants.users)

                    if limit and len(members) >= limit:
                        members = members[:limit]
                        break

                    if len(participants.users) < batch_size:
                        break

                except Exception as e:
                    print(f"Error fetching participants: {e}")
                    break
        else:
            # For regular groups
            async for user in self.client.iter_participants(entity, limit=limit):
                if not user.bot and not user.deleted:
                    members.append(user)

        print(f"Found {len(members)} members")
        return members

    async def download_profile_photo(self, user):
        """Download a user's profile photo"""
        if not user.photo:
            return None

        # Create safe filename
        username = user.username or f"user_{user.id}"
        first_name = user.first_name or ""
        safe_name = "".join(c for c in f"{username}_{first_name}" if c.isalnum() or c in "_-")
        filename = f"{safe_name}_{user.id}.jpg"
        filepath = ORIGINALS_DIR / filename

        # Skip if already downloaded
        if filepath.exists():
            print(f"  Already have: {filename}")
            return filepath

        try:
            await self.client.download_profile_photo(
                user,
                file=str(filepath),
                download_big=True
            )
            print(f"  Downloaded: {filename}")
            return filepath
        except Exception as e:
            print(f"  Failed to download {username}: {e}")
            return None

    async def ganjafy_image(self, image_path):
        """Transform an image with rasta vibes using Gemini"""
        output_name = f"rasta_{image_path.stem}.png"
        output_path = GANJAFY_DIR / output_name

        # Skip if already processed
        if output_path.exists():
            print(f"  Already ganjafied: {output_name}")
            return output_path

        try:
            # Read and encode image
            with open(image_path, "rb") as f:
                image_data = base64.standard_b64encode(f.read()).decode("utf-8")

            # Determine mime type
            suffix = image_path.suffix.lower()
            mime_map = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp'}
            mime_type = mime_map.get(suffix, 'image/jpeg')

            # Call Gemini with retry logic for rate limits
            max_retries = 3
            retry_delay = 5

            for attempt in range(max_retries):
                try:
                    response = self.genai_client.models.generate_content(
                        model="gemini-3-pro-image-preview",  # Nano Banana Pro - same as web version
                        contents=[
                            types.Content(
                                role="user",
                                parts=[
                                    types.Part.from_text(text=RASTA_PROMPT),
                                    types.Part.from_bytes(
                                        data=base64.standard_b64decode(image_data),
                                        mime_type=mime_type
                                    ),
                                ],
                            ),
                        ],
                        config=types.GenerateContentConfig(
                            response_modalities=["image", "text"],
                        ),
                    )
                    break  # Success, exit retry loop
                except Exception as api_err:
                    if attempt < max_retries - 1 and ("429" in str(api_err) or "rate" in str(api_err).lower()):
                        print(f"  Rate limit hit, waiting {retry_delay}s before retry {attempt + 2}/{max_retries}...")
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        raise  # Re-raise if not rate limit or final attempt

            # Extract generated image
            for part in response.candidates[0].content.parts:
                if part.inline_data is not None:
                    image_bytes = part.inline_data.data
                    with open(output_path, "wb") as f:
                        f.write(image_bytes)
                    print(f"  Ganjafied: {output_name}")
                    return output_path

            print(f"  No image generated for {image_path.name}")
            return None

        except Exception as e:
            print(f"  Ganjafy failed for {image_path.name}: {e}")
            return None

    async def run(self, group_identifier, limit=None, skip_download=False, skip_transform=False):
        """Main workflow"""
        await self.setup()

        print("\n" + "="*60)
        print("TELEGRAM BATCH GANJAFY")
        print("="*60)

        downloaded_photos = []

        if not skip_download:
            # Get group members
            members = await self.get_group_members(group_identifier, limit)

            if not members:
                print("No members found!")
                return

            # Download profile photos
            print(f"\nDownloading profile photos to: {ORIGINALS_DIR}")
            for i, user in enumerate(members, 1):
                display_name = user.username or user.first_name or f"User {user.id}"
                print(f"[{i}/{len(members)}] {display_name}")

                photo_path = await self.download_profile_photo(user)
                if photo_path:
                    downloaded_photos.append(photo_path)

                # Small delay to avoid rate limits
                await asyncio.sleep(0.3)
        else:
            # Use existing photos in originals directory
            downloaded_photos = list(ORIGINALS_DIR.glob("*.jpg")) + list(ORIGINALS_DIR.glob("*.png"))
            print(f"Found {len(downloaded_photos)} existing photos in {ORIGINALS_DIR}")

        print(f"\nTotal photos to process: {len(downloaded_photos)}")

        if skip_transform:
            print("Skipping transformation (--skip-transform)")
            return

        # Transform each photo
        print(f"\nGanjafying images to: {GANJAFY_DIR}")
        successful = 0
        failed = 0

        for i, photo_path in enumerate(downloaded_photos, 1):
            print(f"[{i}/{len(downloaded_photos)}] {photo_path.name}")
            result = await self.ganjafy_image(photo_path)

            if result:
                successful += 1
            else:
                failed += 1

            # Delay between API calls to respect rate limits (3-5 seconds)
            await asyncio.sleep(3)

        # Summary
        print("\n" + "="*60)
        print("JAH BLESS! COMPLETE!")
        print("="*60)
        print(f"Original photos: {ORIGINALS_DIR}")
        print(f"Ganjafied photos: {GANJAFY_DIR}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print("="*60 + "\n")

        await self.client.disconnect()


def main():
    parser = argparse.ArgumentParser(
        description="Download Telegram group profile pics and ganjafy them",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python telegram_batch_ganjafy.py --group "ganjamonai"
  python telegram_batch_ganjafy.py --group "@ganja_mon_ai" --limit 20
  python telegram_batch_ganjafy.py --group -1001234567890
  python telegram_batch_ganjafy.py --skip-download  # Just process existing originals
        """
    )

    parser.add_argument(
        "--group", "-g",
        help="Telegram group username, @handle, or chat ID",
        default=""
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        help="Maximum number of members to process",
        default=None
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip downloading, just process existing photos in originals/"
    )
    parser.add_argument(
        "--skip-transform",
        action="store_true",
        help="Only download photos, don't run ganjafy transformation"
    )

    args = parser.parse_args()

    if not args.group and not args.skip_download:
        parser.print_help()
        print("\nError: --group is required unless using --skip-download")
        sys.exit(1)

    # Run
    bot = TelegramGanjafy()
    asyncio.run(bot.run(
        group_identifier=args.group,
        limit=args.limit,
        skip_download=args.skip_download,
        skip_transform=args.skip_transform
    ))


if __name__ == "__main__":
    main()
