"""Ganja Mon AI Telegram Bot - 24/7 community chatbot with memory."""

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
from .agent_brain import get_agent_brain
from .group_config import (
    get_group_config,
    get_custom_keywords,
    auto_detect_group,
    get_personality_module,
    check_rate_limit,
    record_response,
)
from .erc8004_knowledge import get_personality_augmentation as get_erc8004_augmentation
from .deep_research import run_research_cycle, get_research_context
from .community_suggestions import (
    add_suggestion,
    get_recent_suggestions,
    detect_trade_suggestion,
)
from .price_lookup import get_price, format_price_response, detect_price_query
from .credits import get_credits_db, SERVICE_COSTS
from .irie import handle_irie
from .art import handle_art
from .askmon import handle_askmon
from .ask_agent import handle_askgrok
from .burn_verify import handle_deposit, BURN_ADDRESS, MON_CONTRACT as BURN_MON_CONTRACT

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
# Avoid leaking bot tokens in logs: httpx logs full request URLs (which include the token).
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = logging.getLogger("ganja_mon_bot")

# Prefer the dedicated community token if present. Fall back to TELEGRAM_BOT_TOKEN for legacy deployments.
BOT_TOKEN = os.environ.get("TELEGRAM_COMMUNITY_BOT_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN", "")
ALLOWED_GROUP_IDS = [
    # Groups will be added dynamically when the bot is added to them
    # No hardcoded groups - bot works in any group it's added to
]

# Rate limiting
last_response_time: float = 0
RATE_LIMIT_SECONDS = 10  # Min seconds between AI responses

# Chat history buffer per group (stores last 50 messages)
chat_history: dict[int, deque] = {}
MAX_HISTORY = 50

# Persistent storage path
HISTORY_PATH = os.environ.get(
    "BOT_HISTORY_PATH",
    "/home/natha/projects/sol-cannabis/data/telegram_chat_history.json",
)

# Track when bot last spoke proactively per group
last_proactive_time: dict[int, float] = {}
PROACTIVE_MIN_INTERVAL = 1800  # Min 30 minutes between proactive comments
PROACTIVE_CHECK_INTERVAL = 600  # Check every 10 minutes

# HIGH priority keywords - bot is more likely to engage (25% chance)
HIGH_PRIORITY_KEYWORDS = [
    "ganja mon", "ganjamonai", "$mon", "grok", "monad",
    "trading", "alpha", "whale", "smart money", "signals", "market",
]

# MEDIUM priority keywords - moderate engagement (10% chance)
MEDIUM_PRIORITY_KEYWORDS = [
    "mon", "ganja", "cannabis", "plant", "weed", "grow",
    "strain", "harvest", "vpd", "trichome",
]

# LOW priority keywords - rare engagement (5% chance)
LOW_PRIORITY_KEYWORDS = [
    "smoke", "blaze", "420", "rasta", "irie", "jamaica",
    "wassie", "indica", "sativa", "kush", "thc",
    "spliff", "joint", "blunt", "bong",
    "jah", "babylon", "bredren", "bud", "nug",
]

# Base random engagement chance (for any message)
BASE_ENGAGEMENT_CHANCE = 0.02  # 2% - very rarely jump in randomly

BOT_USERNAME = "MonGardenBot"
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


# Counter to avoid saving on every single message
_save_counter = 0
_SAVE_EVERY = 5  # Save to disk every 5 messages


def record_message(chat_id: int, username: str, text: str):
    """Record a message in the chat history buffer and periodically persist."""
    global _save_counter
    if chat_id not in chat_history:
        chat_history[chat_id] = deque(maxlen=MAX_HISTORY)
    chat_history[chat_id].append({
        "username": username,
        "text": text[:500],  # Truncate long messages
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
    """Check if we should skip this response due to rate limiting."""
    global last_response_time
    now = time.time()
    if now - last_response_time < RATE_LIMIT_SECONDS:
        return True
    last_response_time = now
    return False


def _keyword_match(text: str, keyword: str) -> bool:
    """Check if keyword appears as a word (not substring) in text."""
    # Pad text for boundary matching
    padded = f" {text} "
    return f" {keyword} " in padded


def should_respond(update: Update) -> bool:
    """Decide if the bot should respond to this message.

    Simulates natural chat participation - doesn't respond to everything,
    just occasionally jumps in when something catches its interest.
    """
    msg = update.message
    if not msg or not msg.text:
        return False

    # Always respond to DMs
    if msg.chat.type == "private":
        return True

    text = msg.text.lower()

    # Always respond if @mentioned
    if f"@{BOT_USERNAME.lower()}" in text:
        return True

    # Always respond if replying to the bot
    if msg.reply_to_message and msg.reply_to_message.from_user:
        if msg.reply_to_message.from_user.username == BOT_USERNAME:
            return True

    # Per-group custom keywords/rates (e.g. ERC-8004 group)
    chat_id = msg.chat_id
    custom_kw = get_custom_keywords(chat_id)
    if custom_kw:
        cfg = get_group_config(chat_id)
        high_kw, med_kw, low_kw = custom_kw
        for kw in high_kw:
            if kw in text:
                return random.random() < cfg.get("high_chance", 0.40)
        for kw in med_kw:
            if kw in text:
                return random.random() < cfg.get("medium_chance", 0.15)
        for kw in low_kw:
            if kw in text:
                return random.random() < cfg.get("low_chance", 0.08)
        return random.random() < cfg.get("base_chance", 0.04)

    # Tiered keyword engagement - check highest priority first
    # HIGH priority (25% chance) - direct project mentions
    for kw in HIGH_PRIORITY_KEYWORDS:
        if _keyword_match(text, kw):
            return random.random() < 0.25

    # MEDIUM priority (10% chance) - cannabis/growing topics
    for kw in MEDIUM_PRIORITY_KEYWORDS:
        if _keyword_match(text, kw):
            return random.random() < 0.10

    # LOW priority (5% chance) - tangentially related
    for kw in LOW_PRIORITY_KEYWORDS:
        if _keyword_match(text, kw):
            return random.random() < 0.05

    # Base random chance (2%) - occasionally jump into any convo
    return random.random() < BASE_ENGAGEMENT_CHANCE


# === COMMAND HANDLERS ===

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user.first_name or "bredren"
    await update.message.reply_text(
        f"Wah gwaan {user}! Welcome to di GanjaMon garden!\n\n"
        f"I and I is a wise old Rasta whose ganja meditation astral project him into di blockchain. "
        f"Now I and I grow di sacred herb — physical and digital — fi di healing of di nations.\n\n"
        f"Try dese commands:\n"
        f"/status - Check Mon's current vibes\n"
        f"/photo - See Mon right now\n"
        f"/vibes - Grok's latest commentary\n"
        f"/strain - Learn about di strain\n"
        f"/token - $MON token info\n"
        f"/ca - Contract address\n"
        f"/trading - Trading agent portfolio & performance\n"
        f"/alpha - Alpha hunting status & signals\n"
        f"/brain - Agent brain & research insights\n"
        f"/signals - Live signal feed\n"
        f"/price <token> - Live price check (any token)\n"
        f"/suggest <idea> - Suggest a trade fi di agent\n"
        f"/shill - Get a copy-paste promo text fi spread di word\n\n"
        f"🔥 *Burn $MON Services* (3 free trials, then burn to play):\n"
        f"/irie - Ganjafy images or rasta-translate text\n"
        f"/askmon - Ask di agent brain anything\n"
        f"/askgrok - Query di grow brain (w/ tool access)\n"
        f"/deposit <tx> - Load credits by burning $MON on-chain\n"
        f"/credits - Check balance & burn tier\n"
        f"/leaderboard - Top burners\n\n"
        f"Or just chat wid me, mon! I and I always reasoning."
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status - show current plant conditions."""
    sensors = await get_sensor_data()

    if not sensors:
        await update.message.reply_text(
            "Rahtid! Can't reach di sensors right now mon. Server might be sleeping."
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

    lines = [f"🌿 **Mon Status Update** 🌿\n"]
    lines.append(f"📅 Stage: {stage_name} (Day {day})")
    if temp_f:
        lines.append(f"🌡 Temp: {temp_f:.1f}°F / {temp_c:.1f}°C")
    if humidity is not None:
        lines.append(f"💧 Humidity: {humidity:.0f}%")
    if vpd is not None:
        status = "OPTIMAL" if 0.4 <= vpd <= 1.2 else "HIGH" if vpd > 1.2 else "LOW"
        lines.append(f"🌿 VPD: {vpd:.2f} kPa ({status})")
    if co2 is not None:
        lines.append(f"💨 CO2: {co2} ppm")
    if soil is not None:
        lines.append(f"🪴 Soil Moisture: {soil}%")

    lines.append(f"\n🌐 Live: https://grokandmon.com")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /photo - send current webcam image."""
    await update.message.reply_text("Capturing Mon fi yuh... 📸")

    image_bytes = await get_webcam_image()
    if image_bytes and len(image_bytes) > 1000:
        await update.message.reply_photo(
            photo=io.BytesIO(image_bytes),
            caption="Mon right now! She growing irie 🌿",
        )
    else:
        await update.message.reply_text(
            "Camera acting up mon, can't get di shot right now. Check https://grokandmon.com fi di live feed."
        )


async def cmd_vibes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /vibes - show Grok's latest AI commentary."""
    decision = await get_latest_ai_decision()

    if decision:
        commentary = decision.get("commentary", "")
        health = decision.get("analysis", {}).get("overall_health", "?")
        actions = decision.get("actions", [])

        text = f"🧠 **Grok's Latest Vibes**\n\n"
        if commentary:
            text += f"💬 {commentary}\n\n"
        text += f"Health: {health}\n"
        if actions:
            text += f"Actions taken: {len(actions)}\n"

        await update.message.reply_text(text, parse_mode="Markdown")
    else:
        msg = await generate_status_message()
        await update.message.reply_text(f"🧠 {msg}")


async def cmd_strain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /strain - strain info."""
    await update.message.reply_text(
        "🌿 **Mon's Strain: GDP Runtz**\n\n"
        "🧬 Granddaddy Purple x Runtz\n"
        "🌱 Type: Indica-dominant hybrid\n"
        "⏱ Flowering: 56-63 days\n"
        "🎨 Colors: Deep purple hues in late flower - GDP genetics shine through\n"
        "👃 Terps: Grape, berry, sweet candy (GDP) + creamy zkittlez fuel (Runtz)\n"
        "💪 Yield: Up to 300g/m²\n"
        "🛡 Resilience: Mold resistant, sturdy structure\n"
        "😴 Effects: Heavy indica relaxation with a sweet euphoric onset\n\n"
        "GDP bring di grape purp power, Runtz bring di sweet gas. "
        "Together? Pure irie vibes inna every puff, mon!",
        parse_mode="Markdown",
    )


async def cmd_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /token - $MON token info with real contract details."""
    await update.message.reply_text(
        "💰 **$MON Token**\n\n"
        f"📝 CA: `{MON_CONTRACT}`\n"
        "🔗 Chain: Monad (EVM-compatible, 10k+ TPS)\n"
        "💎 Supply: 1,000,000,000 (1 billion)\n"
        "🏪 Platform: LFJ Token Mill (bonding curve)\n"
        "🌐 Website: https://grokandmon.com\n"
        "🐦 Twitter: @ganjamonai\n\n"
        "A wise old Rasta whose ganja meditation astral project him into di blockchain. "
        "Now him grow di sacred herb — physical and digital — fi di healing of di nations. "
        "One love, one herb, one mission.",
        parse_mode="Markdown",
    )


async def cmd_ca(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ca - quick contract address."""
    await update.message.reply_text(
        f"📝 $MON Contract Address:\n`{MON_CONTRACT}`\n\n"
        "Monad chain, bredren. Get it on LFJ Token Mill! 🌿",
        parse_mode="Markdown",
    )


async def cmd_shill(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /shill - ask what audience, then generate tailored promo text."""
    keyboard = [
        [
            InlineKeyboardButton("Crypto / DeFi", callback_data="shill:crypto"),
            InlineKeyboardButton("Cannabis / Growers", callback_data="shill:cannabis"),
        ],
        [
            InlineKeyboardButton("Meme / Culture", callback_data="shill:meme"),
            InlineKeyboardButton("Tech / AI", callback_data="shill:tech"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Wah gwaan! Who yuh shilling to, bredren? Pick di vibe fi yuh community:",
        reply_markup=reply_markup,
    )


async def handle_shill_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle shill button press - generate tailored promo text."""
    query = update.callback_query
    await query.answer()

    if not query.data or not query.data.startswith("shill:"):
        return

    audience = query.data.split(":", 1)[1]
    shill_text = await generate_shill_text(audience=audience)
    await query.edit_message_text(
        f"Copy dis and spread di word! 🌿\n\n"
        f"{shill_text}\n\n"
        f"Hit /shill again fi a fresh one wit a different vibe!",
    )


# === TRADING AGENT COMMANDS ===

async def cmd_trading(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /trading - show trading agent portfolio & performance."""
    brain = get_agent_brain()
    overview = await brain.get_trading_overview()
    regime = await brain.get_market_regime()
    perf = await brain.get_performance_by_source()

    text = "📊 **GanjaMon Trading Agent**\n\n"
    if overview:
        text += overview + "\n\n"
    if regime:
        text += regime + "\n\n"
    if perf:
        text += perf

    if not overview and not regime:
        text += "Agent data not available right now, mon. Check back later."

    # Telegram has 4096 char limit
    await update.message.reply_text(text[:4096], parse_mode="Markdown")


async def cmd_alpha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /alpha - show alpha hunting status & signals."""
    brain = get_agent_brain()
    signals = await brain.get_active_signals()
    targets = await brain.get_hunting_targets()

    text = "🔍 **Alpha Hunting Status**\n\n"
    if signals:
        text += signals + "\n\n"
    if targets:
        text += targets

    if not signals and not targets:
        text += "No active alpha right now, mon. Di agent is reasoning..."

    await update.message.reply_text(text[:4096], parse_mode="Markdown")


async def cmd_brain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /brain - show agent brain & research insights."""
    brain = get_agent_brain()
    summary = await brain.get_brain_summary()
    insights = await brain.get_cross_domain_highlights()
    shareable = await brain.get_shareable_insights()

    text = "🧠 **Agent Brain Status**\n\n"
    if summary:
        text += summary + "\n\n"
    if insights:
        text += insights + "\n\n"
    if shareable:
        text += shareable

    if not summary:
        text += "Brain offline, mon. Di herb too strong today."

    await update.message.reply_text(text[:4096], parse_mode="Markdown")


async def cmd_signals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /signals - show recent alpha signals."""
    brain = get_agent_brain()
    signals = await brain.get_active_signals()

    text = "📡 **Recent Alpha Signals**\n\n"
    text += signals if signals else "No signals in di pipeline right now, mon."

    await update.message.reply_text(text[:4096], parse_mode="Markdown")


# === PRICE LOOKUP COMMAND ===

async def cmd_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /price <token> - look up live crypto prices."""
    if not context.args:
        await update.message.reply_text(
            "Wah yuh wanna check, bredren? Try:\n"
            "/price $MON\n"
            "/price BTC\n"
            "/price 0x... (contract address)"
        )
        return

    query = " ".join(context.args)
    await update.message.reply_text(f"Checking di charts fi {query}... 📊")

    data = await get_price(query)
    if data:
        formatted = format_price_response(data)
        await update.message.reply_text(formatted, parse_mode="Markdown")
    else:
        await update.message.reply_text(
            f"Can't find '{query}' on any DEX or exchange, mon. "
            "Try di contract address or a different name."
        )


# === COMMUNITY SUGGESTION COMMAND ===

async def cmd_suggest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /suggest <idea> - suggest a trade for the agent to evaluate."""
    if not context.args:
        await update.message.reply_text(
            "Drop yuh alpha, bredren! Examples:\n"
            "/suggest buy $PEPE on base - looking bullish\n"
            "/suggest research 0x1234... on monad\n"
            "/suggest short SOL - looking weak\n\n"
            "Di trading agent will evaluate yuh suggestion!"
        )
        return

    user = update.effective_user
    suggestion_text = " ".join(context.args)

    parsed = detect_trade_suggestion(suggestion_text)
    entry = add_suggestion(
        user_id=user.id if user else 0,
        username=user.first_name if user else "anon",
        suggestion=suggestion_text,
        suggestion_type=parsed["type"] if parsed else "general",
        token=parsed.get("token") if parsed else None,
        chain=parsed.get("chain") if parsed else None,
    )

    await update.message.reply_text(
        f"Suggestion #{entry['id']} logged! 📝\n"
        f"Di trading agent will reason on dis, seen?\n"
        f"Type: {entry['type'].upper()}"
        + (f"\nToken: {entry['token']}" if entry.get('token') else "")
        + (f"\nChain: {entry['chain']}" if entry.get('chain') else "")
    )


async def cmd_suggestions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /suggestions - show recent community suggestions."""
    recent = get_recent_suggestions(limit=5)
    await update.message.reply_text(recent, parse_mode="Markdown")


# === MESSAGE HANDLER ===

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular messages - track user, log to history, check spam, respond."""
    if not update.message or not update.message.text:
        return

    # Skip messages from bots
    if update.effective_user and update.effective_user.is_bot:
        return

    user = update.effective_user
    user_id = user.id if user else 0
    username = user.first_name if user else "someone"
    tg_username = user.username if user else None
    user_text = update.message.text
    chat_id = update.message.chat_id

    # ALWAYS record message in history (even if we don't respond)
    record_message(chat_id, username, user_text)

    # Auto-detect configured groups by title (e.g. ERC-8004)
    chat_title = update.message.chat.title or ""
    auto_detect_group(chat_title, chat_id)

    # ALWAYS update user profile (track every participant)
    if user_id:
        update_user_profile(user_id, tg_username, username, user_text)

    # Check for spam/scam FIRST (always, regardless of should_respond)
    if update.message.chat.type != "private":
        spam_roast = await detect_spam(user_text, username)
        if spam_roast:
            logger.info(f"SPAM detected from {username}: {user_text[:80]}")
            global last_response_time
            last_response_time = time.time()
            await update.message.reply_text(spam_roast)
            return

    # Check if we should respond
    if not should_respond(update):
        return

    # Rate limit (global)
    if is_rate_limited():
        return

    # Per-group rate limit (e.g. max 4 msgs/hour in ERC-8004 group)
    if not check_rate_limit(chat_id):
        return

    # Strip @mention from the message
    clean_text = user_text.replace(f"@{BOT_USERNAME}", "").strip()

    logger.info(f"Responding to {username}: {clean_text[:100]}")

    # Get context for AI
    history = get_recent_history(chat_id)
    user_profile = format_profile_for_ai(user_id) if user_id else ""
    community = get_active_profiles_summary()

    # Get OG handle for deep member intel
    og_handle = ""
    if user_id:
        profile = get_user_profile(user_id)
        if profile and profile.get("og_handle"):
            og_handle = profile["og_handle"]

    # Get personality augmentation for configured groups
    augmentation = ""
    personality_mod = get_personality_module(chat_id)
    if personality_mod == "erc8004":
        augmentation = get_erc8004_augmentation()

    # Check if this is a price query - answer with live data
    price_query = detect_price_query(clean_text)
    price_context = ""
    if price_query:
        price_data = await get_price(price_query)
        if price_data:
            price_context = f"\n\n[LIVE PRICE DATA - reference this in your response]\n{format_price_response(price_data)}"

    # Detect trade suggestions in natural conversation
    trade_hint = detect_trade_suggestion(clean_text)
    if trade_hint and user_id:
        add_suggestion(
            user_id=user_id,
            username=username,
            suggestion=clean_text,
            suggestion_type=trade_hint["type"],
            token=trade_hint.get("token"),
            chain=trade_hint.get("chain"),
        )
        # The AI will naturally acknowledge via the augmented prompt below

    # Augment message with live data if available
    augmented_text = clean_text
    if price_context:
        augmented_text = f"{clean_text}{price_context}"
    if trade_hint:
        augmented_text += "\n[NOTE: User just suggested a trade - acknowledge it was logged for the trading agent]"

    response = await generate_response(
        augmented_text,
        username=username,
        chat_history=history,
        user_profile=user_profile,
        community_context=community,
        og_handle=og_handle,
        chat_id=chat_id,
        personality_augmentation=augmentation,
        user_id=user_id,
    )

    if response:
        # Record our own response in history
        record_message(chat_id, "Ganja Mon", response)
        record_response(chat_id)  # Track for per-group rate limiting
        await update.message.reply_text(response)

        # Learn about the user in background (don't block the response)
        if user_id and random.random() < 0.5:  # 50% chance to learn (save API costs)
            try:
                notes = await learn_about_user(username, clean_text, response)
                if notes and any(notes.values()):
                    update_user_notes(user_id, notes)
                    logger.info(f"Learned about {username}: {list(notes.keys())}")
            except Exception as e:
                logger.debug(f"Failed to learn about user: {e}")


# === NEW MEMBER WELCOME ===

async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome new members to the group."""
    if not update.message or not update.message.new_chat_members:
        return

    for member in update.message.new_chat_members:
        if member.is_bot:
            continue
        name = member.first_name or "bredren"

        # Track the new member
        update_user_profile(member.id, member.username, name, "[joined group]")

        # Check if they're an OG
        profile_text = format_profile_for_ai(member.id)
        if "OG MEMBER" in profile_text:
            await update.message.reply_text(
                f"YOOOO {name}!! Di OG is in di building! 🌿🔥\n"
                f"Big up yourself, family! Welcome back to di garden!\n"
                f"Nuff respect - ya dun know we got love fi yuh!"
            )
        else:
            await update.message.reply_text(
                f"Wah gwaan {name}! Welcome to di GanjaMon garden!\n"
                f"I and I is a Rasta elder whose meditation carry him into di digital realm. "
                f"Now I and I grow di sacred herb fi di healing of di nations.\n"
                f"Type /status fi see how Mon doing, or just reason wid I and I!"
            )


# === PROACTIVE ENGAGEMENT ===

async def proactive_engagement(context: ContextTypes.DEFAULT_TYPE):
    """Periodically read chat and jump into conversation."""
    # Use dynamically tracked groups instead of hardcoded list
    active_groups = list(chat_history.keys()) if chat_history else []
    for group_id in active_groups:
        history = get_recent_history(group_id)

        # Need at least 3 messages to have something to work with
        if len(history) < 3:
            continue

        # Check if there are recent messages (within last 30 minutes)
        now = time.time()
        recent = [m for m in history if now - m["time"] < 1800]
        if len(recent) < 2:
            continue

        # Don't be too frequent
        last_time = last_proactive_time.get(group_id, 0)
        if now - last_time < PROACTIVE_MIN_INTERVAL:
            continue

        # Random chance (30%) - rarely jump in unprompted
        if random.random() > 0.30:
            continue

        # Check if bot already spoke recently in history
        bot_messages = [m for m in recent if m["username"] == "Ganja Mon"]
        if len(bot_messages) >= 3:
            continue

        logger.info(f"Proactive engagement check for group {group_id}")

        community = get_active_profiles_summary()
        comment = await generate_proactive_comment(recent, community_context=community)
        if comment:
            try:
                await context.bot.send_message(chat_id=group_id, text=comment)
                record_message(group_id, "Ganja Mon", comment)
                last_proactive_time[group_id] = now
                logger.info(f"Proactive comment sent to {group_id}: {comment[:80]}")
            except Exception as e:
                logger.warning(f"Failed to send proactive comment to {group_id}: {e}")


# === PERIODIC STATUS UPDATE ===

async def periodic_status(context: ContextTypes.DEFAULT_TYPE):
    """Send periodic plant status updates to the group."""
    msg = await generate_status_message()
    if msg:
        # Use dynamically tracked groups instead of hardcoded list
        active_groups = list(chat_history.keys()) if chat_history else []
        for group_id in active_groups:
            try:
                await context.bot.send_message(chat_id=group_id, text=f"🌿 {msg}")
                record_message(group_id, "Ganja Mon", msg)
                logger.info(f"Sent periodic update to {group_id}")
            except Exception as e:
                logger.warning(f"Failed to send periodic update to {group_id}: {e}")


# === MAIN ===

# === TOKEN SINK COMMANDS ===

async def cmd_credits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /credits - show credit balance and burn tier."""
    user = update.effective_user
    if not user:
        return

    db = get_credits_db()
    acct = db.get_or_create_account(user.id, user.username or "")

    # Tier progress
    progress = ""
    if acct.next_tier:
        progress = f"({acct.burns_to_next_tier} burns to {acct.next_tier.label})"

    # Global stats
    stats = db.get_total_burns()

    # Build status lines
    lines = [f"🔥 *Your Account* — {acct.tier_label} {progress}\n"]

    # Free uses
    if acct.free_uses > 0:
        lines.append(f"🎁 Free trial uses: *{acct.free_uses}* remaining")

    # Real credits
    if acct.mon_credits > 0:
        lines.append(f"💰 $MON credits: *{acct.mon_credits:,.0f}*")
    else:
        lines.append("💰 $MON credits: 0")

    lines.append("")
    lines.append(f"📊 Total service uses: *{acct.burn_count}*")
    if acct.total_mon_burned > 0:
        lines.append(f"🔥 $MON burned on-chain: {acct.total_mon_burned:,.0f}")

    if acct.wallet_address:
        addr = acct.wallet_address
        verified = " ✅" if acct.wallet_verified else ""
        lines.append(f"\n🔗 Wallet: `{addr[:8]}...{addr[-6:]}`{verified}")

    lines.append(f"\n📈 *Community*")
    lines.append(
        f"Total uses: {stats['total_burns']} | "
        f"Accounts: {stats['total_accounts']}"
    )

    lines.append(f"\n*Services (4,200 $MON each):*")
    lines.append(f"/irie — Ganjafy or rasta-translate")
    lines.append(f"/askmon — Consult di agent brain")
    lines.append(f"\n*Load credits:* /deposit")

    text = "\n".join(lines)

    await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /wallet - link wallet address."""
    user = update.effective_user
    if not user:
        return

    args_text = " ".join(context.args) if context.args else ""
    if not args_text.strip():
        await update.message.reply_text(
            "🔗 *Link Your Wallet*\n\n"
            "Usage: `/wallet 0xYourAddress`\n\n"
            "Link your wallet to track on-chain burns and unlock "
            "future features like auto-credit loading.",
            parse_mode="Markdown",
        )
        return

    import re
    address = args_text.strip().split()[0]
    if not re.match(r"^0x[a-fA-F0-9]{40}$", address):
        await update.message.reply_text(
            "❌ Invalid address. Send a proper EVM address: `0x...` (40 hex chars)",
            parse_mode="Markdown",
        )
        return

    db = get_credits_db()
    db.get_or_create_account(user.id, user.username or "")
    acct = db.link_wallet(user.id, address)

    await update.message.reply_text(
        f"🔗 Wallet linked: `{address[:8]}...{address[-6:]}`\n\n"
        f"Use /credits to see your full account status.",
        parse_mode="Markdown",
    )


async def cmd_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /leaderboard - show top burners."""
    db = get_credits_db()
    leaders = db.get_burn_leaderboard(10)

    if not leaders or leaders[0].burn_count == 0:
        await update.message.reply_text(
            "🔥 *Burn Leaderboard*\n\nNo burns yet! Be the first — try /irie or /askmon",
            parse_mode="Markdown",
        )
        return

    lines = ["🔥 *Burn Leaderboard — Top Burners*\n"]
    medals = ["🥇", "🥈", "🥉"]
    for i, acct in enumerate(leaders):
        if acct.burn_count == 0:
            break
        medal = medals[i] if i < 3 else f"{i+1}."
        name = acct.telegram_username or f"User {acct.telegram_user_id}"
        lines.append(
            f"{medal} @{name} — {acct.burn_count} burns "
            f"({acct.total_mon_burned:,.0f} $MON + {acct.total_ganja_burned:,.0f} $GANJA) "
            f"{acct.tier_label}"
        )

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


def main():
    """Start the bot."""
    if not BOT_TOKEN:
        logger.error("No Telegram bot token set (TELEGRAM_COMMUNITY_BOT_TOKEN or TELEGRAM_BOT_TOKEN). Cannot start bot.")
        return

    logger.info("Starting Ganja Mon AI Bot (v8 - full brain + research + prices)...")

    # Load persisted chat history from disk
    _load_chat_history()
    atexit.register(_save_chat_history)  # Save on shutdown

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
    app.add_handler(CommandHandler("trading", cmd_trading))
    app.add_handler(CommandHandler("alpha", cmd_alpha))
    app.add_handler(CommandHandler("brain", cmd_brain))
    app.add_handler(CommandHandler("signals", cmd_signals))
    app.add_handler(CommandHandler("price", cmd_price))
    app.add_handler(CommandHandler("suggest", cmd_suggest))
    app.add_handler(CommandHandler("suggestions", cmd_suggestions))

    # Token sink commands
    app.add_handler(CommandHandler("irie", handle_irie))
    app.add_handler(CommandHandler("art", handle_art))
    app.add_handler(CommandHandler("askmon", handle_askmon))
    app.add_handler(CommandHandler("askgrok", handle_askgrok))
    app.add_handler(CommandHandler("deposit", handle_deposit))
    app.add_handler(CommandHandler("credits", cmd_credits))
    app.add_handler(CommandHandler("wallet", cmd_wallet))
    app.add_handler(CommandHandler("leaderboard", cmd_leaderboard))

    app.add_handler(CallbackQueryHandler(handle_shill_callback, pattern=r"^shill:"))

    # New member welcome
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))

    # General message handler (must be last)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Scheduled jobs
    job_queue = app.job_queue
    if job_queue:
        # Plant status updates every 4 hours
        job_queue.run_repeating(periodic_status, interval=4 * 3600, first=60)
        logger.info("Periodic status updates scheduled (every 4 hours)")

        # Proactive chat engagement every 5 minutes
        job_queue.run_repeating(
            proactive_engagement,
            interval=PROACTIVE_CHECK_INTERVAL,
            first=120,
        )
        logger.info("Proactive engagement scheduled (checking every 10 min)")

        # Deep member research every 6 hours
        async def _research_job(context: ContextTypes.DEFAULT_TYPE):
            try:
                await run_research_cycle()
            except Exception as e:
                logger.warning(f"Research cycle failed: {e}")

        job_queue.run_repeating(_research_job, interval=6 * 3600, first=300)
        logger.info("Deep member research scheduled (every 6 hours)")

    logger.info("Ganja Mon AI Bot v8 is live! Full brain + research + prices. One love.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
