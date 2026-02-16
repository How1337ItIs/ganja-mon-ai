"""
/askgrok Command — Query the Agentic Brain (with Tool Access)
=============================================================

Unlike /askmon (which costs credits and uses a separate Grok call),
/askgrok routes through GrokBrain.interactive_query() — the agent
can read sensors, check history, control devices, and reason with
its full 39-tool arsenal.

Usage in Telegram:
    /askgrok How is Mon doing right now?
    /askgrok What's the current VPD and should I adjust anything?
    /askgrok Take a photo of Mon and tell me how she looks
    /askgrok What actions have you taken in the last 24 hours?
"""

import logging
import os
import time
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

# Rate limit: one query per user per 60 seconds
_user_last_query: dict[int, float] = {}
QUERY_COOLDOWN = 60  # seconds

# Admin user IDs that bypass cooldown
ADMIN_IDS = set()
_admin_env = os.environ.get("TELEGRAM_ADMIN_IDS", "")
if _admin_env:
    for _id in _admin_env.split(","):
        try:
            ADMIN_IDS.add(int(_id.strip()))
        except ValueError:
            pass


async def handle_askgrok(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /askgrok — query the agentic brain with full tool access."""
    if not update.message:
        return

    user = update.effective_user
    user_id = user.id if user else 0
    username = user.first_name if user else "bredren"

    # Extract question from command args or replied message
    question = " ".join(context.args) if context.args else ""
    if not question and update.message.reply_to_message:
        question = update.message.reply_to_message.text or ""

    if not question.strip():
        await update.message.reply_text(
            "Wah yuh wanna know, bredren? Ask mi anyting about Mon!\n\n"
            "Usage: `/askgrok your question here`\n"
            "Or reply to any message with `/askgrok`\n\n"
            "Examples:\n"
            "• `/askgrok How is Mon doing right now?`\n"
            "• `/askgrok What's the VPD and should I adjust it?`\n"
            "• `/askgrok What did you do in the last 24 hours?`\n"
            "• `/askgrok Take a photo and analyze the plant`\n\n"
            "I and I will use mi full brain — sensors, history, "
            "and all 39 tools at mi disposal! 🧠",
            parse_mode="Markdown",
        )
        return

    # Rate limiting (skip for admins)
    now = time.time()
    if user_id not in ADMIN_IDS:
        last_query = _user_last_query.get(user_id, 0)
        if now - last_query < QUERY_COOLDOWN:
            remaining = int(QUERY_COOLDOWN - (now - last_query))
            await update.message.reply_text(
                f"Easy nuh, bredren! Wait {remaining}s before asking again. "
                f"I and I need time fi reason. 🧘"
            )
            return

    _user_last_query[user_id] = now

    # Show typing indicator
    await update.message.reply_text(
        "🧠 Reasoning... I and I consulting di full brain, sensors, and tools. "
        "Give mi a moment, seen? ⏳"
    )

    try:
        # Get orchestrator instance
        orchestrator = _get_orchestrator()
        if not orchestrator:
            # Fallback: create a standalone brain
            result = await _standalone_query(question, username)
        else:
            # Use the orchestrator bridge (has full sensor/device access)
            result = await orchestrator.handle_interactive_query(
                query=question,
                user_context=f"Question from Telegram user @{username} (id: {user_id})",
            )

        output = result.get("output_text", "Mi brain is foggy right now, try again later mon.")
        actions = result.get("actions_taken", [])
        tool_rounds = result.get("tool_rounds", 0)

        # Format response
        response_parts = [output]

        if actions:
            action_summary = []
            for a in actions[:5]:  # Show max 5 actions
                status = "✅" if a.get("success") else "❌"
                action_summary.append(f"{status} `{a.get('tool', '?')}`: {a.get('message', '')[:60]}")
            response_parts.append("\n🔧 *Actions taken:*\n" + "\n".join(action_summary))

        if tool_rounds > 0:
            response_parts.append(f"\n_({tool_rounds} reasoning rounds, {result.get('total_tool_calls', 0)} tool calls)_")

        full_response = "\n".join(response_parts)

        # Telegram message limit
        if len(full_response) > 4096:
            full_response = full_response[:4090] + "\n..."

        await update.message.reply_text(full_response, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"askgrok failed for {username}: {e}", exc_info=True)
        await update.message.reply_text(
            f"Rahtid! Di brain glitched: {str(e)[:100]}\n"
            "Try again inna likkle bit, mon. 🔧"
        )


def _get_orchestrator():
    """Try to get the running orchestrator instance."""
    try:
        # The orchestrator is stored as a module-level reference
        # when started via run.py
        from src import _orchestrator_instance
        return _orchestrator_instance
    except (ImportError, AttributeError):
        pass

    # Alternative: check if there's a global reference
    try:
        import src.orchestrator as orch_mod
        if hasattr(orch_mod, '_global_orchestrator'):
            return orch_mod._global_orchestrator
    except Exception:
        pass

    return None


async def _standalone_query(question: str, username: str) -> dict:
    """Fallback: create a standalone GrokBrain and query it directly.

    Used when the orchestrator isn't running in the same process
    (e.g., Telegram bot is a separate subprocess).
    """
    import os
    from src.ai import GrokBrain, ToolExecutor

    api_key = os.environ.get("XAI_API_KEY", "")
    if not api_key:
        return {
            "output_text": "No API key configured, mon. Can't reason without di brain.",
            "actions_taken": [],
            "tool_rounds": 0,
        }

    brain = GrokBrain(
        api_key=api_key,
        plant_name="Mon",
    )

    # Create tool executor (limited — no hardware access in standalone mode)
    executor = ToolExecutor(None, None, None)
    brain.tool_executor = executor

    result = await brain.interactive_query(
        query=question,
        context=f"Question from Telegram user @{username}. "
                f"NOTE: Running in standalone mode — hardware control is unavailable.",
        growth_stage="vegetative",
        current_day=1,
    )

    return {
        "output_text": result.output_text,
        "actions_taken": result.actions_taken or [],
        "tool_rounds": result.tool_rounds,
        "total_tool_calls": result.total_tool_calls,
        "tokens_used": result.tokens_used,
        "trigger": result.trigger,
    }
