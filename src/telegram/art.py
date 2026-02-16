"""
/art Command — Commission GanjaMon Art via Telegram
=====================================================

Usage in Telegram:
    /art meme <prompt>        -> Generate a Rasta meme
    /art pfp <description>    -> Generate a profile picture
    /art banner <info>        -> Generate a social/DexScreener banner
    /art ganjafy              -> (reply to photo) Transform into Rasta style
    /art commission <prompt>  -> Full custom art commission
    /art                      -> Show available modes and pricing

Burns 8,400 $MON credits per use (~2x /irie cost, covers AI image gen).
"""

import io
import base64

import structlog
from telegram import Update
from telegram.ext import ContextTypes

from src.telegram.credits import get_credits_db

log = structlog.get_logger("telegram.art")

ART_MODES_HELP = {
    "meme": ("Rasta meme from any topic", "/art meme when your plant grows faster than your portfolio"),
    "pfp": ("Unique profile picture", "/art pfp cyberpunk rasta warrior with dreadlocks"),
    "banner": ("Social media / DexScreener banner", "/art banner $MON — the token that grows itself"),
    "ganjafy": ("Transform a photo into Rasta style", "/art ganjafy (reply to any photo)"),
    "commission": ("Full custom art — your vision, Mon's brush", "/art commission a sunset over a cannabis field with Bob Marley vibes"),
}


async def handle_art(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /art command — create AI art in various modes."""
    if not update.message:
        return

    user = update.message.from_user
    if not user:
        return

    # Parse args: /art <mode> <prompt...>
    args = context.args or []

    # No args — show help
    if not args:
        help_lines = [
            "GanjaMon Art Studio\n",
            "Every piece carries Mon's evolving signature.\n",
            "Modes:",
        ]
        for mode, (desc, example) in ART_MODES_HELP.items():
            help_lines.append(f"  *{mode}* — {desc}")
            help_lines.append(f"  `{example}`\n")
        help_lines.append("Cost: 8,400 $MON per piece | /credits to check balance")
        await update.message.reply_text("\n".join(help_lines), parse_mode="Markdown")
        return

    mode = args[0].lower()
    prompt = " ".join(args[1:]) if len(args) > 1 else ""

    # Validate mode
    valid_modes = {"meme", "pfp", "banner", "ganjafy", "commission"}
    if mode not in valid_modes:
        await update.message.reply_text(
            f"Unknown mode: *{mode}*\n\n"
            f"Available: {', '.join(valid_modes)}\n"
            f"Try: `/art meme your topic here`",
            parse_mode="Markdown",
        )
        return

    # Ganjafy requires a photo
    source_image_b64 = None
    if mode == "ganjafy":
        reply = update.message.reply_to_message
        photo = None
        if reply and reply.photo:
            photo = reply.photo[-1]
        elif update.message.photo:
            photo = update.message.photo[-1]

        if not photo:
            await update.message.reply_text(
                "Reply to a photo with `/art ganjafy` to transform it into Rasta style.",
                parse_mode="Markdown",
            )
            return

        file = await photo.get_file()
        img_bytes = await file.download_as_bytearray()
        source_image_b64 = base64.b64encode(bytes(img_bytes)).decode()

    # Check and spend credits
    db = get_credits_db()
    db.get_or_create_account(user.id, user.username or "")
    ok, spend_msg = db.spend_credits(user.id, "art")
    if not ok:
        await update.message.reply_text(
            f"{spend_msg}\n\n"
            f"Each /art costs 8,400 $MON.\n"
            f"Burn $MON on-chain to load credits: /deposit",
            parse_mode="Markdown",
        )
        return

    is_trial = "Free trial" in spend_msg

    await update.message.reply_text(
        f"Creating *{mode}* art... gimme a moment, the muse is speaking",
        parse_mode="Markdown",
    )

    # Import art studio and create
    try:
        from src.x402_hackathon.oracle.art_studio import create_art

        result = await create_art(
            mode=mode,
            prompt=prompt,
            source_image_b64=source_image_b64,
            style_hints={"style": ""},
            growth_stage="vegetative",
            mood="creative",
            grow_day=0,
        )

        if "error" in result:
            # Refund on failure
            _refund(db, user.id, is_trial)
            await update.message.reply_text(
                f"Art generation failed: {result['error']}\n"
                f"Credits refunded. Try again, bredda."
            )
            return

        # Send the image back
        image_b64 = result.get("image_b64")
        if not image_b64:
            _refund(db, user.id, is_trial)
            await update.message.reply_text("No image generated. Refunded.")
            return

        image_bytes = base64.b64decode(image_b64)
        artist_note = result.get("artist_note", "")
        gallery_id = result.get("gallery_id", "")

        caption_parts = [f"*{mode.upper()}* by GanjaMon"]
        if artist_note:
            # Truncate long notes
            note = artist_note[:200]
            caption_parts.append(f"\n_{note}_")
        caption_parts.append(f"\n{spend_msg}")

        acct = db.get_account(user.id)
        if acct:
            caption_parts.append(f" | {acct.tier_label}")

        await update.message.reply_photo(
            photo=io.BytesIO(image_bytes),
            caption="\n".join(caption_parts),
            parse_mode="Markdown",
        )

        # Post about it on socials (fire-and-forget)
        try:
            from src.x402_hackathon.oracle.art_studio import post_art_to_socials
            import asyncio
            asyncio.create_task(post_art_to_socials(
                result, mode=mode, prompt=prompt,
                commissioned_by=user.username or user.first_name or "a Telegram user",
            ))
        except Exception:
            pass  # Social posting is best-effort

        log.info("Art created via Telegram",
                 user_id=user.id, username=user.username,
                 mode=mode, gallery_id=gallery_id)

    except Exception as e:
        _refund(db, user.id, is_trial)
        log.error("Art command failed", error=str(e), user_id=user.id)
        await update.message.reply_text(
            f"Something went wrong: {str(e)[:100]}\nCredits refunded."
        )


def _refund(db, user_id: int, is_trial: bool) -> None:
    """Refund credits on art generation failure."""
    if not is_trial:
        db.load_credits(user_id, "MON", 8400.0, '{"reason":"art_failed"}')
    else:
        try:
            cdb = db._ensure_db()
            cdb.execute(
                "UPDATE accounts SET free_uses = free_uses + 1 WHERE telegram_user_id = ?",
                (user_id,),
            )
            cdb.commit()
        except Exception:
            pass
