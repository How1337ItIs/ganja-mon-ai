"""Mon Plant Monitor - 24/7 IoT plant monitoring chatbot with memory."""

import os
import io
import json
import time
import random
import logging
import asyncio
import atexit
from collections import deque
from pathlib import Path
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
from .personality import (
    generate_response,
    generate_status_message,
    generate_proactive_comment,
    generate_shill_text,
    detect_spam,
    learn_about_user,
)
from .plant_data import (
    get_sensor_data,
    get_grow_stage,
    get_latest_ai_decision,
    get_webcam_image,
    get_plant_summary,
)
from .user_profiles import (
    update_user_profile,
    get_user_profile,
    format_profile_for_ai,
    update_user_notes,
    get_active_profiles_summary,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("mon_plant_bot")

# Alert bot uses separate token from persona bot
BOT_TOKEN = os.environ.get("TELEGRAM_ALERT_BOT_TOKEN", "")
ALLOWED_GROUP_IDS = []

# Rate limiting
last_response_time: float = 0
RATE_LIMIT_SECONDS = 10

# Chat history buffer per group
chat_history: dict[int, deque] = {}
MAX_HISTORY = 50

# Persistent storage path
HISTORY_PATH = os.environ.get(
    "BOT_HISTORY_PATH",
    "/home/natha/projects/sol-cannabis/data/telegram_chat_history.json",
)

# Track proactive engagement
last_proactive_time: dict[int, float] = {}
PROACTIVE_MIN_INTERVAL = 1800
PROACTIVE_CHECK_INTERVAL = 600

# Priority keywords - generic gardening/plant terms
HIGH_PRIORITY_KEYWORDS = [
    "mon plant", "monplant", "$mon", "grok", "monad",
]

MEDIUM_PRIORITY_KEYWORDS = [
    "mon", "plant", "garden", "grow", "cultivate",
    "harvest", "vpd", "humidity", "temperature",
]

LOW_PRIORITY_KEYWORDS = [
    "organic", "indoor", "hydro", "soil",
    "nutrients", "flowering", "vegetative",
    "lighting", "spectrum", "roots",
]

BASE_ENGAGEMENT_CHANCE = 0.02

BOT_USERNAME = "MonPlantBot"
MON_CONTRACT = "0x0EB75e7168aF6Ab90D7415fE6fB74E10a70B5C0b"


def _load_chat_history():
    """Load chat history from disk on startup."""
    global chat_history
    try:
        if os.path.exists(HISTORY_PATH):
            with open(HISTORY_PATH, "r") as f:
                data = json.load(f)
            for chat_id_str, messages in data.items():
                chat_id = int(chat_id_str)
                chat_history[chat_id] = deque(messages, maxlen=MAX_HISTORY)
            logger.info(f"Loaded chat history for {len(data)} groups from disk")
    except Exception as e:
        logger.warning(f"Failed to load chat history: {e}")


def _save_chat_history():
    """Save chat history to disk."""
    try:
        os.makedirs(os.path.dirname(HISTORY_PATH), exist_ok=True)
        data = {str(k): list(v) for k, v in chat_history.items()}
        with open(HISTORY_PATH, "w") as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception as e:
        logger.warning(f"Failed to save chat history: {e}")


_save_counter = 0
_SAVE_EVERY = 5


def record_message(chat_id: int, username: str, text: str):
    """Record a message in the chat history buffer."""
    global _save_counter
    if chat_id not in chat_history:
        chat_history[chat_id] = deque(maxlen=MAX_HISTORY)
    chat_history[chat_id].append({
        "username": username,
        "text": text[:500],
        "time": time.time(),
    })
    _save_counter += 1
    if _save_counter >= _SAVE_EVERY:
        _save_counter = 0
        _save_chat_history()


def get_recent_history(chat_id: int) -> list[dict]:
    """Get recent chat history for a group."""
    if chat_id not in chat_history:
        return []
    return list(chat_history[chat_id])


def is_rate_limited() -> bool:
    """Check rate limiting."""
    global last_response_time
    now = time.time()
    if now - last_response_time < RATE_LIMIT_SECONDS:
        return True
    last_response_time = now
    return False


def _keyword_match(text: str, keyword: str) -> bool:
    """Check if keyword appears as a word in text."""
    padded = f" {text} "
    return f" {keyword} " in padded


def should_respond(update: Update) -> bool:
    """Decide if the bot should respond."""
    msg = update.message
    if not msg or not msg.text:
        return False

    if msg.chat.type == "private":
        return True

    text = msg.text.lower()

    if f"@{BOT_USERNAME.lower()}" in text:
        return True

    if msg.reply_to_message and msg.reply_to_message.from_user:
        if msg.reply_to_message.from_user.username == BOT_USERNAME:
            return True

    for kw in HIGH_PRIORITY_KEYWORDS:
        if _keyword_match(text, kw):
            return random.random() < 0.25

    for kw in MEDIUM_PRIORITY_KEYWORDS:
        if _keyword_match(text, kw):
            return random.random() < 0.10

    for kw in LOW_PRIORITY_KEYWORDS:
        if _keyword_match(text, kw):
            return random.random() < 0.05

    return random.random() < BASE_ENGAGEMENT_CHANCE


# === COMMAND HANDLERS ===

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user.first_name or "friend"
    await update.message.reply_text(
        f"Hey {user}! Welcome to Mon Plant Monitor!\n\n"
        f"I'm an AI assistant for monitoring plants grown with autonomous AI control. "
        f"Mon is being cultivated using Grok AI decisions - fully automated IoT gardening. "
        f"CA P64 personal cultivation project.\n\n"
        f"Commands:\n"
        f"/status - Check current environment\n"
        f"/photo - See the plant now\n"
        f"/vibes - AI's latest analysis\n"
        f"/strain - Plant variety info\n"
        f"/token - $MON token info\n"
        f"/ca - Contract address\n\n"
        f"Or just chat with me! I'm always here to help."
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status - show current conditions."""
    sensors = await get_sensor_data()

    if not sensors:
        await update.message.reply_text(
            "Can't reach the sensors right now. Server might be offline."
        )
        return

    temp_c = sensors.get("temperature")
    temp_f = temp_c * 9 / 5 + 32 if temp_c else None
    humidity = sensors.get("humidity")
    vpd = sensors.get("vpd")
    soil = sensors.get("soil_moisture")
    co2 = sensors.get("co2")

    stage = await get_grow_stage()
    stage_name = stage.get("stage", "?") if stage else "?"
    day = stage.get("day", "?") if stage else "?"

    lines = [f"**Mon Status Update**\n"]
    lines.append(f"Stage: {stage_name} (Day {day})")
    if temp_f:
        lines.append(f"Temp: {temp_f:.1f}F / {temp_c:.1f}C")
    if humidity is not None:
        lines.append(f"Humidity: {humidity:.0f}%")
    if vpd is not None:
        status = "OPTIMAL" if 0.4 <= vpd <= 1.2 else "HIGH" if vpd > 1.2 else "LOW"
        lines.append(f"VPD: {vpd:.2f} kPa ({status})")
    if co2 is not None:
        lines.append(f"CO2: {co2} ppm")
    if soil is not None:
        lines.append(f"Soil Moisture: {soil}%")

    lines.append(f"\nLive: https://grokandmon.com")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /photo - send current webcam image."""
    await update.message.reply_text("Capturing image...")

    image_bytes = await get_webcam_image()
    if image_bytes and len(image_bytes) > 1000:
        await update.message.reply_photo(
            photo=io.BytesIO(image_bytes),
            caption="Mon right now! Growing nicely.",
        )
    else:
        await update.message.reply_text(
            "Camera unavailable right now. Check https://grokandmon.com for live feed."
        )


async def cmd_vibes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /vibes - show AI commentary."""
    decision = await get_latest_ai_decision()

    if decision:
        commentary = decision.get("commentary", "")
        health = decision.get("analysis", {}).get("overall_health", "?")
        actions = decision.get("actions", [])

        text = f"**Grok's Analysis**\n\n"
        if commentary:
            text += f"{commentary}\n\n"
        text += f"Health: {health}\n"
        if actions:
            text += f"Actions taken: {len(actions)}\n"

        await update.message.reply_text(text, parse_mode="Markdown")
    else:
        msg = await generate_status_message()
        await update.message.reply_text(msg)


async def cmd_strain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /strain - plant info."""
    # P64 = Prop 64 reference, kept coded
    await update.message.reply_text(
        "**Mon's Variety: GDP Runtz**\n\n"
        "Genetics: GDP x Runtz hybrid\n"
        "Type: Indica-dominant\n"
        "Cycle: 56-63 days flowering\n"
        "Colors: Deep purple hues in late stage\n"
        "Profile: Grape, berry, sweet notes\n"
        "Yield: Up to 300g/m2\n"
        "Resilience: Mold resistant, sturdy\n\n"
        "Grown under CA P64 guidelines. Personal cultivation project.",
        parse_mode="Markdown",
    )


async def cmd_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /token - $MON token info."""
    await update.message.reply_text(
        "**$MON Token**\n\n"
        f"CA: `{MON_CONTRACT}`\n"
        "Chain: Monad (EVM-compatible, 10k+ TPS)\n"
        "Supply: 1,000,000,000 (1B)\n"
        "Platform: LFJ Token Mill (bonding curve)\n"
        "Website: https://grokandmon.com\n"
        "Twitter: @ganjamonai\n\n"
        "First AI-autonomously grown plant on blockchain!",
        parse_mode="Markdown",
    )


async def cmd_ca(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ca - quick contract address."""
    await update.message.reply_text(
        f"$MON Contract Address:\n`{MON_CONTRACT}`\n\n"
        "Monad chain. Get it on LFJ Token Mill!",
        parse_mode="Markdown",
    )


async def cmd_shill(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /shill - generate promo text."""
    keyboard = [
        [
            InlineKeyboardButton("Crypto / DeFi", callback_data="shill:crypto"),
            InlineKeyboardButton("Gardening", callback_data="shill:cannabis"),
        ],
        [
            InlineKeyboardButton("Meme / Culture", callback_data="shill:meme"),
            InlineKeyboardButton("Tech / AI", callback_data="shill:tech"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Who are you sharing with? Pick the audience:",
        reply_markup=reply_markup,
    )


async def handle_shill_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle shill button press."""
    query = update.callback_query
    await query.answer()

    if not query.data or not query.data.startswith("shill:"):
        return

    audience = query.data.split(":", 1)[1]
    shill_text = await generate_shill_text(audience=audience)
    await query.edit_message_text(
        f"Copy and share!\n\n"
        f"{shill_text}\n\n"
        f"Hit /shill again for a different version!",
    )


# === MESSAGE HANDLER ===

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular messages."""
    if not update.message or not update.message.text:
        return

    if update.effective_user and update.effective_user.is_bot:
        return

    user = update.effective_user
    user_id = user.id if user else 0
    username = user.first_name if user else "someone"
    tg_username = user.username if user else None
    user_text = update.message.text
    chat_id = update.message.chat_id

    record_message(chat_id, username, user_text)

    if user_id:
        update_user_profile(user_id, tg_username, username, user_text)

    if update.message.chat.type != "private":
        spam_roast = await detect_spam(user_text, username)
        if spam_roast:
            logger.info(f"SPAM detected from {username}: {user_text[:80]}")
            global last_response_time
            last_response_time = time.time()
            await update.message.reply_text(spam_roast)
            return

    if not should_respond(update):
        return

    if is_rate_limited():
        return

    clean_text = user_text.replace(f"@{BOT_USERNAME}", "").strip()

    logger.info(f"Responding to {username}: {clean_text[:100]}")

    history = get_recent_history(chat_id)
    user_profile = format_profile_for_ai(user_id) if user_id else ""
    community = get_active_profiles_summary()

    og_handle = ""
    if user_id:
        profile = get_user_profile(user_id)
        if profile and profile.get("og_handle"):
            og_handle = profile["og_handle"]

    response = await generate_response(
        clean_text,
        username=username,
        chat_history=history,
        user_profile=user_profile,
        community_context=community,
        og_handle=og_handle,
        chat_id=chat_id,
    )

    if response:
        record_message(chat_id, "Mon Bot", response)
        await update.message.reply_text(response)

        if user_id and random.random() < 0.5:
            try:
                notes = await learn_about_user(username, clean_text, response)
                if notes and any(notes.values()):
                    update_user_notes(user_id, notes)
                    logger.info(f"Learned about {username}: {list(notes.keys())}")
            except Exception as e:
                logger.debug(f"Failed to learn about user: {e}")


# === NEW MEMBER WELCOME ===

async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome new members."""
    if not update.message or not update.message.new_chat_members:
        return

    for member in update.message.new_chat_members:
        if member.is_bot:
            continue
        name = member.first_name or "friend"

        update_user_profile(member.id, member.username, name, "[joined group]")

        profile_text = format_profile_for_ai(member.id)
        if "OG MEMBER" in profile_text:
            await update.message.reply_text(
                f"Welcome back {name}! Great to see an OG in the chat!\n"
                f"The garden has been growing well. Glad you're here!"
            )
        else:
            await update.message.reply_text(
                f"Hey {name}! Welcome to Mon Plant Monitor!\n"
                f"We're growing plants with AI-autonomous control - Grok makes all the decisions.\n"
                f"Type /status to see current conditions, or just chat!"
            )


# === PROACTIVE ENGAGEMENT ===

async def proactive_engagement(context: ContextTypes.DEFAULT_TYPE):
    """Periodically engage in conversation."""
    active_groups = list(chat_history.keys()) if chat_history else []
    for group_id in active_groups:
        history = get_recent_history(group_id)

        if len(history) < 3:
            continue

        now = time.time()
        recent = [m for m in history if now - m["time"] < 1800]
        if len(recent) < 2:
            continue

        last_time = last_proactive_time.get(group_id, 0)
        if now - last_time < PROACTIVE_MIN_INTERVAL:
            continue

        if random.random() > 0.30:
            continue

        bot_messages = [m for m in recent if m["username"] == "Mon Bot"]
        if len(bot_messages) >= 3:
            continue

        logger.info(f"Proactive engagement check for group {group_id}")

        community = get_active_profiles_summary()
        comment = await generate_proactive_comment(recent, community_context=community)
        if comment:
            try:
                await context.bot.send_message(chat_id=group_id, text=comment)
                record_message(group_id, "Mon Bot", comment)
                last_proactive_time[group_id] = now
                logger.info(f"Proactive comment sent to {group_id}: {comment[:80]}")
            except Exception as e:
                logger.warning(f"Failed to send proactive comment to {group_id}: {e}")


# === PERIODIC STATUS UPDATE ===

async def periodic_status(context: ContextTypes.DEFAULT_TYPE):
    """Send periodic status updates."""
    msg = await generate_status_message()
    if msg:
        active_groups = list(chat_history.keys()) if chat_history else []
        for group_id in active_groups:
            try:
                await context.bot.send_message(chat_id=group_id, text=msg)
                record_message(group_id, "Mon Bot", msg)
                logger.info(f"Sent periodic update to {group_id}")
            except Exception as e:
                logger.warning(f"Failed to send periodic update to {group_id}: {e}")


# === MAIN ===

def main():
    """Start the bot."""
    if not BOT_TOKEN:
        logger.error("No Telegram bot token set (TELEGRAM_COMMUNITY_BOT_TOKEN or TELEGRAM_BOT_TOKEN). Cannot start bot.")
        return

    logger.info("Starting Mon Plant Monitor Bot...")

    _load_chat_history()
    atexit.register(_save_chat_history)

    app = Application.builder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("photo", cmd_photo))
    app.add_handler(CommandHandler("vibes", cmd_vibes))
    app.add_handler(CommandHandler("strain", cmd_strain))
    app.add_handler(CommandHandler("token", cmd_token))
    app.add_handler(CommandHandler("ca", cmd_ca))
    app.add_handler(CommandHandler("shill", cmd_shill))
    app.add_handler(CallbackQueryHandler(handle_shill_callback, pattern=r"^shill:"))

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    job_queue = app.job_queue
    if job_queue:
        job_queue.run_repeating(periodic_status, interval=4 * 3600, first=60)
        logger.info("Periodic status updates scheduled (every 4 hours)")

        job_queue.run_repeating(
            proactive_engagement,
            interval=PROACTIVE_CHECK_INTERVAL,
            first=120,
        )
        logger.info("Proactive engagement scheduled (checking every 10 min)")

    logger.info("Mon Plant Monitor Bot is live!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
