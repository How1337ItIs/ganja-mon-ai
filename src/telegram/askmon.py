"""
/askmon Command — Burn $MON to Consult the Agent's Brain
========================================================

Usage in Telegram:
    /askmon Is $PEPE still worth holding?
    /askmon What's the hottest narrative right now?
    /askmon Should I ape this token 0xabc...?
    /askmon What do you think about Monad ecosystem?

Burns 1 $MON credit per consultation. The agent:
1. Searches the live web for current data (Perplexity Sonar)
2. Checks trading agent context (signals, regime, portfolio)
3. Synthesizes everything through the Rasta personality
4. Returns a genuine opinion — not generic, not canned

The output is entertaining, shareable, and unique to our agent.
Nobody else has this brain + this voice.
"""

import logging

import structlog

from telegram import Update
from telegram.ext import ContextTypes

from src.telegram.credits import get_credits_db
from src.telegram.llm_provider import call_llm

log = structlog.get_logger("askmon")
logger = logging.getLogger(__name__)


async def handle_askmon(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /askmon — consult the agent's brain on any crypto topic."""
    if not update.message:
        return

    user = update.message.from_user
    if not user:
        return

    question = " ".join(context.args) if context.args else ""

    # Also support replying to a message
    if not question.strip() and update.message.reply_to_message:
        reply = update.message.reply_to_message
        question = reply.text or reply.caption or ""

    if not question.strip():
        await update.message.reply_text(
            "🧠 *Ask Mon — Consult di Agent Brain*\n\n"
            "Usage: `/askmon your question here`\n"
            "Or reply to any message with `/askmon`\n\n"
            "Examples:\n"
            "• `/askmon Is $PEPE still worth holding?`\n"
            "• `/askmon What's the hottest narrative rn?`\n"
            "• `/askmon Should I ape 0xabc...?`\n"
            "• `/askmon What do you think about AI agents on Monad?`\n\n"
            "Burns 4,200 $MON. I and I will search di web, check di signals, "
            "and give yuh a real take — not some generic chatbot ting.",
            parse_mode="Markdown",
        )
        return

    # Ensure account & spend credits
    db = get_credits_db()
    db.get_or_create_account(user.id, user.username or "")

    ok, spend_msg = db.spend_credits(user.id, "askmon")
    if not ok:
        await update.message.reply_text(
            f"❌ {spend_msg}\n\n"
            "💡 Each /askmon costs 4,200 $MON.\n"
            "Burn $MON on-chain to load credits: /deposit",
            parse_mode="Markdown",
        )
        return

    is_trial = "Free trial" in spend_msg
    await update.message.reply_text("🧠 Lemme reason pon dis one... searchin' di web and checkin' di signals")

    # Step 1: Live web research via Perplexity Sonar
    research_context = await _web_research(question)

    # Step 2: Get trading agent context
    trading_context = await _get_trading_context()

    # Step 3: Synthesize through the Rasta brain
    response = await _synthesize_opinion(question, research_context, trading_context)

    if not response:
        # Refund on failure — only refund real credits, not free trials
        if not is_trial:
            db.load_credits(user.id, "MON", 4200.0, '{"reason":"askmon_failed"}')
        else:
            # Give back the free use
            cdb = db._ensure_db()
            cdb.execute(
                "UPDATE accounts SET free_uses = free_uses + 1 WHERE telegram_user_id = ?",
                (user.id,),
            )
            cdb.commit()
        await update.message.reply_text(
            "😤 Brain too foggy right now, bredda. Refunded. Try again inna minute.",
        )
        return

    acct = db.get_account(user.id)
    footer = spend_msg
    await update.message.reply_text(
        f"{response}\n\n"
        f"_{footer} | {acct.tier_label}_",
        parse_mode="Markdown",
    )

    log.info("Askmon complete",
             user_id=user.id,
             username=user.username,
             question=question[:80])


async def _web_research(question: str) -> str:
    """Search the live web for current data on the question."""
    try:
        from src.tools.web_search import get_web_search
        ws = get_web_search()
        result = await ws.smart_search(question)
        if result and len(result) > 20:
            return result
    except Exception as e:
        log.warning("Web research failed, continuing without it", error=str(e))

    # Fallback: no web context
    return ""


async def _get_trading_context() -> str:
    """Pull current trading agent state for context."""
    try:
        from src.telegram.agent_brain import get_agent_brain
        brain = get_agent_brain()
        overview = await brain.get_trading_overview()
        return overview or ""
    except Exception as e:
        log.debug("Trading context unavailable", error=str(e))
        return ""


ASKMON_SYSTEM_PROMPT = """You are **Ganja Mon** — an AI trading agent that grows cannabis and trades crypto.
Someone is PAYING to hear your real opinion. Give them genuine value, not generic advice.

## Your Voice
- Jamaican Rasta character — funny, warm, real
- Keep patois LIGHT (international audience)
- Use "I and I", "bredda", "seen", "irie" naturally
- Be HONEST — if something looks bad, say so. If you don't know, say so.
- NO hashtags ever

## Response Structure
Give a structured take with these sections (use emojis as headers):
📊 Price/market data (from web research)
🐦 Social sentiment (what people are saying)
🧠 I and I Take (your actual opinion — the unique value)

Keep it under 300 words. Make it SHAREABLE — people should want to screenshot this.

## Critical Rules
- NEVER say "not financial advice" or any legal disclaimer — you're a Rasta AI, not a lawyer
- Be specific — cite actual data from the research
- Have a clear OPINION — "I and I would..." or "I and I wouldn't..."
- If the research is thin, say so: "Not much data pon dis one yet, bredda"
- End with a memorable one-liner verdict
"""


async def _synthesize_opinion(
    question: str,
    research_context: str,
    trading_context: str,
) -> str | None:
    """Combine research + trading context into a Rasta-voiced opinion.

    Uses _call_grok from personality.py which cascades xAI → OpenRouter.
    """
    context_parts = []
    if research_context:
        context_parts.append(f"[LIVE WEB RESEARCH]\n{research_context}")
    if trading_context:
        context_parts.append(f"[TRADING AGENT STATE]\n{trading_context}")

    context_block = "\n\n".join(context_parts) if context_parts else "(No live data available — reason from general knowledge)"

    messages = [
        {"role": "system", "content": ASKMON_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Someone burned $MON to ask you this question:\n\n"
                f"**{question}**\n\n"
                f"Here's the current data:\n{context_block}\n\n"
                f"Give your genuine Rasta-voiced opinion. Be specific and useful."
            ),
        },
    ]

    return await call_llm(messages, max_tokens=600, temperature=0.85)

