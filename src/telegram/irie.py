"""
/irie Command — Burn $MON to Irie Up Content
=============================================

Usage in Telegram:
    /irie [tweet URL]     → fetch tweet, ganjafy image or rasta-translate text
    /irie [any text]      → rasta-translate the text
    /irie (reply to photo) → ganjafy the photo
    /irie (reply to msg)   → rasta-translate the message

Burns 1 $MON credit per use. Output is sent back to user
for them to post wherever they want (Twitter, Farcaster, etc).
"""

import io
from typing import Optional

import structlog
from telegram import Update
from telegram.ext import ContextTypes

from src.media.ganjafy import (
    extract_tweet_id,
    fetch_tweet_content,
    ganjafy_from_url,
    ganjafy_image,
    rasta_translate,
)
from src.telegram.credits import get_credits_db

log = structlog.get_logger("irie")


async def handle_irie(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /irie command — ganjafy images or rasta-translate text."""
    if not update.message:
        return

    user = update.message.from_user
    if not user:
        return

    # Ensure account exists
    db = get_credits_db()
    db.get_or_create_account(user.id, user.username or "")

    # Check and spend credits
    ok, spend_msg = db.spend_credits(user.id, "irie")
    if not ok:
        await update.message.reply_text(
            f"❌ {spend_msg}\n\n"
            f"💡 Each /irie costs 4,200 $MON.\n"
            f"Burn $MON on-chain to load credits: /deposit",
            parse_mode="Markdown",
        )
        return

    is_trial = "Free trial" in spend_msg
    await update.message.reply_text("🔥 Irie-ing it up... gimme a sec, bredda")

    result = await _process_irie(update, context)

    if result is None:
        # Refund on failure
        if not is_trial:
            db.load_credits(user.id, "MON", 4200.0, '{"reason":"irie_failed"}')
        else:
            cdb = db._ensure_db()
            cdb.execute(
                "UPDATE accounts SET free_uses = free_uses + 1 WHERE telegram_user_id = ?",
                (user.id,),
            )
            cdb.commit()
        await update.message.reply_text(
            "😤 Couldn't irie dat one up, seen? Refunded.\n"
            "Try again with an image, tweet URL, or text."
        )
        return

    acct = db.get_account(user.id)
    footer = spend_msg

    if isinstance(result, bytes):
        # Image result
        caption = (
            f"🔥 *Irie'd up by Ganja Mon*\n"
            f"{footer} | {acct.tier_label}"
        )
        await update.message.reply_photo(
            photo=io.BytesIO(result),
            caption=caption,
            parse_mode="Markdown",
        )
    elif isinstance(result, str):
        # Text result
        await update.message.reply_text(
            f"🔥 *Irie Translation:*\n\n{result}\n\n"
            f"_{footer} | {acct.tier_label}_",
            parse_mode="Markdown",
        )

    log.info("Irie complete",
             user_id=user.id,
             username=user.username,
             result_type="image" if isinstance(result, bytes) else "text")


async def _process_irie(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> Optional[bytes | str]:
    """Determine content type and process accordingly.

    Returns image bytes, translated text, or None on failure.
    """
    message = update.message
    args_text = " ".join(context.args) if context.args else ""
    reply = message.reply_to_message

    # Priority 1: Reply to a photo → ganjafy it
    if reply and reply.photo:
        photo = reply.photo[-1]  # Highest resolution
        file = await photo.get_file()
        img_bytes = await file.download_as_bytearray()
        context_text = reply.caption or args_text or ""
        return await ganjafy_image(bytes(img_bytes), context_text)

    # Priority 2: Attached photo → ganjafy it
    if message.photo:
        photo = message.photo[-1]
        file = await photo.get_file()
        img_bytes = await file.download_as_bytearray()
        context_text = message.caption or args_text or ""
        return await ganjafy_image(bytes(img_bytes), context_text)

    # Priority 3: Tweet URL → fetch and process
    tweet_id = extract_tweet_id(args_text)
    if tweet_id:
        tweet_url = f"https://x.com/i/status/{tweet_id}"
        content = await fetch_tweet_content(tweet_url)
        if content:
            # If tweet has an image, ganjafy it
            if content.get("image_url"):
                result = await ganjafy_from_url(content["image_url"], content.get("text", ""))
                if result:
                    return result
            # Otherwise rasta-translate the text
            if content.get("text"):
                return await rasta_translate(content["text"])
        # Fallback: just translate the URL text as-is
        return await rasta_translate(f"Check out this tweet: {tweet_url}")

    # Priority 4: Reply to text message → rasta-translate it
    if reply and reply.text:
        return await rasta_translate(reply.text)

    # Priority 5: Text argument → rasta-translate it
    if args_text.strip():
        return await rasta_translate(args_text)

    # Nothing to process
    return None
