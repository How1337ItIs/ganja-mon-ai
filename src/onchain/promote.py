"""
GrowRing Social Promotion Engine
==================================

After minting and listing a GrowRing, promote it across all social channels.
Scales promotion intensity by rarity:
  - COMMON: Twitter only
  - UNCOMMON: Twitter + Telegram
  - RARE: Twitter + Telegram + Farcaster (with countdown posts)
  - LEGENDARY: ALL channels, multiple posts, maximum energy
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


# ─── Promotion Templates ───────────────────────────────────────────────

PROMOTION_TEMPLATES = {
    "Legendary": {
        "energy": "MAXIMUM",
        "channels": ["twitter", "telegram", "farcaster"],
        "repeat_posts": 3,
        "include_countdown": True,
        "emoji": "👑",
    },
    "Rare": {
        "energy": "high",
        "channels": ["twitter", "telegram", "farcaster"],
        "repeat_posts": 2,
        "include_countdown": True,
        "emoji": "💎",
    },
    "Uncommon": {
        "energy": "medium",
        "channels": ["twitter", "telegram"],
        "repeat_posts": 1,
        "include_countdown": False,
        "emoji": "🌿",
    },
    "Common": {
        "energy": "chill",
        "channels": ["twitter"],
        "repeat_posts": 1,
        "include_countdown": False,
        "emoji": "🌱",
    },
}

RARITY_NAMES = {0: "Common", 1: "Uncommon", 2: "Rare", 3: "Legendary"}


async def promote_listing(
    mint_result: dict,
    listing_result: dict,
    narrative: str,
) -> dict:
    """Promote a newly listed GrowRing across social channels.

    Args:
        mint_result: Result dict from mint_growring()
        listing_result: Result dict from auto_list_after_mint()
        narrative: The Rasta-voiced journal entry for this day

    Returns:
        Dict with promotion results
    """
    rarity_name = mint_result.get("rarity_name", "Common")
    template = PROMOTION_TEMPLATES.get(rarity_name, PROMOTION_TEMPLATES["Common"])
    token_id = mint_result["token_id"]
    day_number = mint_result["day_number"]
    art_style = mint_result.get("art_style", "unknown")

    logger.info(
        f"📢 Promoting GrowRing #{token_id} (Day {day_number}, {rarity_name}) "
        f"energy={template['energy']}"
    )

    # Build the promotion content
    promo_content = _build_promo_content(
        mint_result, listing_result, narrative, template
    )

    posted = []

    for channel in template["channels"]:
        try:
            result = await _post_to_channel(channel, promo_content, mint_result)
            posted.append({"channel": channel, "status": "posted", **result})
        except Exception as e:
            logger.warning(f"Failed to post to {channel}: {e}")
            posted.append({"channel": channel, "status": "failed", "error": str(e)})

    # Schedule follow-up posts for Dutch auctions
    if template["include_countdown"] and listing_result.get("listing_type") == "dutch_auction":
        await _schedule_auction_updates(mint_result, listing_result, template["repeat_posts"])

    return {
        "token_id": token_id,
        "rarity": rarity_name,
        "channels_posted": len([p for p in posted if p["status"] == "posted"]),
        "posts": posted,
    }


def _build_promo_content(
    mint_result: dict,
    listing_result: dict,
    narrative: str,
    template: dict,
) -> dict:
    """Build promotion content tailored to the rarity and listing type."""
    token_id = mint_result["token_id"]
    day_number = mint_result["day_number"]
    rarity_name = mint_result.get("rarity_name", "Common")
    art_style = mint_result.get("art_style", "")
    emoji = template["emoji"]
    milestone = mint_result.get("milestone_type", "daily_journal")

    # Truncate narrative for social (max 200 chars)
    short_narrative = narrative[:200] + "..." if len(narrative) > 200 else narrative

    # Build base text — different energy for different rarities
    if rarity_name == "Legendary":
        text = (
            f"{emoji} HARVEST DAY - GrowRing #{token_id}\n\n"
            f"116 days. One plant. One agent. One legendary moment.\n\n"
            f"{short_narrative}\n\n"
            f"The final piece of the collection. Dutch auction LIVE\n"
        )
    elif rarity_name == "Rare":
        text = (
            f"{emoji} MILESTONE — GrowRing #{token_id} (Day {day_number})\n\n"
            f"{milestone.replace('_', ' ').title()} achieved\n\n"
            f"{short_narrative}\n\n"
            f"Dutch auction live — price dropping\n"
        )
    elif rarity_name == "Uncommon":
        text = (
            f"{emoji} GrowRing #{token_id} — Day {day_number}\n\n"
            f"{short_narrative}\n"
        )
    else:
        text = (
            f"{emoji} Day {day_number} — GrowRing #{token_id}\n\n"
            f"{short_narrative}\n"
        )

    # Add pricing info
    if listing_result.get("listing_type") == "dutch_auction":
        start = listing_result.get("start_price_mon", "?")
        end = listing_result.get("end_price_mon", "?")
        hours = listing_result.get("duration_hours", "?")
        url = listing_result.get("auction_url", "")
        text += f"\n{start}→{end} MON over {hours}h\n{url}"
    elif listing_result.get("listing_type") == "fixed_price":
        price = listing_result.get("price_mon", "?")
        url = listing_result.get("token_url", "")
        text += f"\n{price} MON on Magic Eden\n{url}"

    return {
        "text": text,
        "image_uri": mint_result.get("image_uri", ""),
        "art_style": art_style,
        "rarity": rarity_name,
        "token_id": token_id,
        "day_number": day_number,
    }


async def _post_to_channel(channel: str, content: dict, mint_result: dict) -> dict:
    """Post promotion content to a specific social channel.

    Delegates to existing social infrastructure in src/social/.
    """
    text = content["text"]

    if channel == "twitter":
        try:
            from src.social.twitter import post_tweet_with_image
            from src.onchain.ipfs import ipfs_to_gateway

            image_url = ipfs_to_gateway(content["image_uri"])
            result = await post_tweet_with_image(text, image_url)
            return {"tweet_id": result.get("id", ""), "platform": "twitter"}
        except ImportError:
            logger.info(f"[Twitter] Would post: {text[:100]}...")
            return {"platform": "twitter", "mode": "dry_run"}

    elif channel == "telegram":
        try:
            from src.social.telegram_poster import post_to_telegram

            await post_to_telegram(text)
            return {"platform": "telegram"}
        except ImportError:
            logger.info(f"[Telegram] Would post: {text[:100]}...")
            return {"platform": "telegram", "mode": "dry_run"}

    elif channel == "farcaster":
        try:
            from src.social.farcaster import post_cast

            await post_cast(text)
            return {"platform": "farcaster"}
        except ImportError:
            logger.info(f"[Farcaster] Would post: {text[:100]}...")
            return {"platform": "farcaster", "mode": "dry_run"}

    else:
        logger.warning(f"Unknown channel: {channel}")
        return {"platform": channel, "mode": "unsupported"}


async def _schedule_auction_updates(
    mint_result: dict, listing_result: dict, num_updates: int
):
    """Schedule follow-up posts for Dutch auction countdown.

    For RARE: 2 updates (halfway, final hour)
    For LEGENDARY: 3 updates (1/3, 2/3, final hour)
    """
    duration_hours = listing_result.get("duration_hours", 24)
    token_id = mint_result["token_id"]

    # For now, just log the schedule — actual scheduling will integrate
    # with the orchestrator's task system
    intervals = []
    for i in range(1, num_updates + 1):
        hours_from_now = int(duration_hours * i / (num_updates + 1))
        intervals.append(hours_from_now)

    logger.info(
        f"📅 Scheduled {num_updates} auction updates for GrowRing #{token_id} "
        f"at +{intervals}h"
    )

    # TODO: Register with orchestrator scheduler
    # await scheduler.schedule_tasks([
    #     ScheduledTask(
    #         name=f"auction_update_{token_id}_{i}",
    #         run_at=datetime.now() + timedelta(hours=h),
    #         func=_post_auction_update,
    #         args=(mint_result, listing_result, i, num_updates),
    #     )
    #     for i, h in enumerate(intervals, 1)
    # ])
