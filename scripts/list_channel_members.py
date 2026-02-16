#!/usr/bin/env python3
"""
List all members of a Telegram group/channel by username or title.
Uses TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE from .env.
"""
import os
import asyncio
import json
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from telethon import TelegramClient
from telethon.tl.types import Channel, Chat, InputUser
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import ChannelParticipantsSearch

API_ID = int(os.getenv("TELEGRAM_API_ID", 0))
API_HASH = os.getenv("TELEGRAM_API_HASH", "")
PHONE = os.getenv("TELEGRAM_PHONE", "")


async def get_all_members(group_identifier):
    session_path = Path(__file__).parent.parent / "telegram_session"
    client = TelegramClient(str(session_path), API_ID, API_HASH)
    await client.start(phone=PHONE)

    try:
        entity = await client.get_entity(group_identifier)
    except Exception as e:
        print(f"Could not resolve '{group_identifier}': {e}")
        await client.disconnect()
        return []

    title = getattr(entity, "title", str(group_identifier))
    print(f"Channel/group: {title}\n")

    members = []
    if isinstance(entity, (Channel, Chat)):
        offset = 0
        batch_size = 200
        while True:
            try:
                participants = await client(
                    GetParticipantsRequest(
                        channel=entity,
                        filter=ChannelParticipantsSearch(""),
                        offset=offset,
                        limit=batch_size,
                        hash=0,
                    )
                )
                if not participants.users:
                    break
                for user in participants.users:
                    members.append({
                        "id": user.id,
                        "access_hash": getattr(user, "access_hash", 0),
                        "username": getattr(user, "username", None) or "",
                        "first_name": getattr(user, "first_name", None) or "",
                        "last_name": getattr(user, "last_name", None) or "",
                        "bot": getattr(user, "bot", False),
                        "deleted": getattr(user, "deleted", False),
                        "bio": "",
                        "has_photo": bool(getattr(user, "photo", None)),
                        "pfp": "",
                    })
                offset += len(participants.users)
                if len(participants.users) < batch_size:
                    break
            except Exception as e:
                print(f"Error fetching batch: {e}")
                break
    else:
        async for user in client.iter_participants(entity):
            members.append({
                "id": user.id,
                "access_hash": getattr(user, "access_hash", 0),
                "username": getattr(user, "username", None) or "",
                "first_name": getattr(user, "first_name", None) or "",
                "last_name": getattr(user, "last_name", None) or "",
                "bot": getattr(user, "bot", False),
                "deleted": getattr(user, "deleted", False),
                "bio": "",
                "has_photo": bool(getattr(user, "photo", None)),
                "pfp": "",
            })

    await enrich_members_with_bios(client, members)
    pfp_dir = Path(__file__).parent.parent / "data" / "brackets_pfps"
    await download_member_pfps(client, members, pfp_dir)
    await client.disconnect()
    return members


async def enrich_members_with_bios(client, members_list, delay=0.15):
    """Fetch full user (bio) for each member. delay (seconds) between requests to avoid FloodWait."""
    from telethon.errors import FloodWaitError
    total = len(members_list)
    for i, m in enumerate(members_list, 1):
        try:
            inp = InputUser(user_id=m["id"], access_hash=m.get("access_hash", 0))
            full = await client(GetFullUserRequest(inp))
            m["bio"] = (full.full_user.about or "").strip()
        except FloodWaitError as e:
            print(f"  FloodWait {e.seconds}s, sleeping...")
            await asyncio.sleep(e.seconds)
            # retry this user
            try:
                inp = InputUser(user_id=m["id"], access_hash=m.get("access_hash", 0))
                full = await client(GetFullUserRequest(inp))
                m["bio"] = (full.full_user.about or "").strip()
            except Exception:
                m["bio"] = ""
        except Exception:
            m["bio"] = ""
        if i % 50 == 0 or i == total:
            print(f"  Bios: {i}/{total}")
        await asyncio.sleep(delay)
    print(f"  Bios: {total}/{total}")


async def download_member_pfps(client, members_list, output_dir, delay=0.1):
    """Download profile photos for all members with has_photo. Sets m['pfp'] to relative path."""
    from telethon.errors import FloodWaitError
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    subdir_name = output_dir.name
    to_download = [m for m in members_list if m.get("has_photo")]
    total = len(to_download)
    if not total:
        print("  Pfps: 0 (none have profile photos)")
        return
    print(f"  Pfps: downloading {total} profile photos...")
    for i, m in enumerate(to_download, 1):
        try:
            inp = InputUser(user_id=m["id"], access_hash=m.get("access_hash", 0))
            path = output_dir / f"{m['id']}.jpg"
            await client.download_profile_photo(inp, file=str(path), download_big=True)
            m["pfp"] = f"{subdir_name}/{m['id']}.jpg"
        except FloodWaitError as e:
            print(f"  FloodWait {e.seconds}s, sleeping...")
            await asyncio.sleep(e.seconds)
            try:
                inp = InputUser(user_id=m["id"], access_hash=m.get("access_hash", 0))
                path = output_dir / f"{m['id']}.jpg"
                await client.download_profile_photo(inp, file=str(path), download_big=True)
                m["pfp"] = f"{subdir_name}/{m['id']}.jpg"
            except Exception:
                pass
        except Exception:
            pass
        if i % 50 == 0 or i == total:
            print(f"  Pfps: {i}/{total}")
        await asyncio.sleep(delay)
    print(f"  Pfps: {total}/{total}")


async def find_channel_by_title(client, title_match):
    """Find first dialog whose title equals or contains title_match (case-insensitive)."""
    async for dialog in client.iter_dialogs():
        if not isinstance(dialog.entity, (Channel, Chat)):
            continue
        t = (dialog.title or "").strip()
        if title_match.lower() in t.lower() or t == title_match:
            return dialog.entity
    return None


def main():
    if not all([API_ID, API_HASH, PHONE]):
        print("Set TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE in .env")
        return
    # Channel: "[ ]" or "brackets" - try resolve by username first, else search dialogs by title
    group_identifier = "brackets"
    members = asyncio.run(get_all_members(group_identifier))
    if not members and group_identifier == "brackets":
        # Fallback: find by title "[ ]" or "brackets" in dialogs
        async def try_by_title():
            session_path = Path(__file__).parent.parent / "telegram_session"
            client = TelegramClient(str(session_path), API_ID, API_HASH)
            await client.start(phone=PHONE)
            for name in ("[ ]", "brackets", "[]"):
                entity = await find_channel_by_title(client, name)
                if entity:
                    print(f"Found channel by title: {getattr(entity, 'title', name)}")
                    ms = await get_members_into_list(client, entity)
                    await client.disconnect()
                    return ms
            await client.disconnect()
            return []

        async def get_members_into_list(client, entity):
            members_list = []
            if isinstance(entity, (Channel, Chat)):
                offset = 0
                batch_size = 200
                while True:
                    try:
                        participants = await client(
                            GetParticipantsRequest(
                                channel=entity,
                                filter=ChannelParticipantsSearch(""),
                                offset=offset,
                                limit=batch_size,
                                hash=0,
                            )
                        )
                        if not participants.users:
                            break
                        for user in participants.users:
                            members_list.append({
                                "id": user.id,
                                "access_hash": getattr(user, "access_hash", 0),
                                "username": getattr(user, "username", None) or "",
                                "first_name": getattr(user, "first_name", None) or "",
                                "last_name": getattr(user, "last_name", None) or "",
                                "bot": getattr(user, "bot", False),
                                "deleted": getattr(user, "deleted", False),
                                "bio": "",
                                "has_photo": bool(getattr(user, "photo", None)),
                                "pfp": "",
                            })
                        offset += len(participants.users)
                        if len(participants.users) < batch_size:
                            break
                    except Exception as e:
                        print(f"Error fetching batch: {e}")
                        break
            else:
                async for user in client.iter_participants(entity):
                    members_list.append({
                        "id": user.id,
                        "access_hash": getattr(user, "access_hash", 0),
                        "username": getattr(user, "username", None) or "",
                        "first_name": getattr(user, "first_name", None) or "",
                        "last_name": getattr(user, "last_name", None) or "",
                        "bot": getattr(user, "bot", False),
                        "deleted": getattr(user, "deleted", False),
                        "bio": "",
                        "has_photo": bool(getattr(user, "photo", None)),
                        "pfp": "",
                    })
            await enrich_members_with_bios(client, members_list)
            pfp_dir = Path(__file__).parent.parent / "data" / "brackets_pfps"
            await download_member_pfps(client, members_list, pfp_dir)
            return members_list

        members = asyncio.run(try_by_title())

    out_path = Path(__file__).parent.parent / "data" / "brackets_members.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(members, f, indent=2, ensure_ascii=False)
    print(f"Total: {len(members)} members (saved to {out_path})\n")

    for i, m in enumerate(members, 1):
        uname = f"@{m['username']}" if m["username"] else "(no username)"
        name = f"{m['first_name']} {m['last_name']}".strip() or "(no name)"
        bot = " [bot]" if m["bot"] else ""
        bio = (m.get("bio") or "")[:60]
        if len(m.get("bio") or "") > 60:
            bio += "..."
        line = f"{i:4}. {name} {uname} (id={m['id']}){bot}"
        if bio:
            line += f"\n      bio: {bio}"
        if m.get("pfp"):
            line += f"\n      pfp: {m['pfp']}"
        # Windows console often can't print emoji/special chars
        print(line.encode("ascii", errors="replace").decode("ascii"))

    print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    main()
