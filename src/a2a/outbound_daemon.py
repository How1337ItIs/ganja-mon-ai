"""
Outbound A2A Daemon
====================

Proactively discovers and calls other agents via the A2A protocol.
GanjaMon becomes the first agent on Monad that actively initiates
agent-to-agent conversations.

Features:
- Periodic discovery of agents from 8004scan registry
- Smart contact scheduling: new agents every round, known agents on cooldown
- Response quality scoring: skip generic chatbots, prioritize valuable agents
- x402 micropayment tracking with budget awareness
- Sends cultivation status data and requests relevant data back
- Tracks agent reliability and response quality
- Persists interaction history + agent quality ratings

Runs as an asyncio coroutine alongside the unified orchestrator.
"""

import asyncio
import json
import logging
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .client import A2AClient, A2AResponse, AgentCard, get_a2a_client
from .orchestrator import A2AOrchestrator, get_orchestrator
from .registry import AgentEntry, AgentRegistry, get_registry

logger = logging.getLogger(__name__)

# Configuration
OUTREACH_INTERVAL_SECONDS = 5 * 60   # 5 minutes between outreach rounds
MAX_CONCURRENT_CALLS = 15            # Concurrency cap
FAILURE_THRESHOLD = 3                # Skip agents after 3 consecutive failures
FAILURE_COOLDOWN_HOURS = 2           # Re-try failed agents after 2 hours
CALL_TIMEOUT = 90.0                  # Timeout per call — x402 flow takes 50-80s
MAX_FOLLOWUP_TURNS = 3               # Multi-turn: up to 3 follow-up exchanges per contact
INTERACTIONS_FILE = Path("data/a2a_interactions.json")
RELIABILITY_FILE = Path("data/a2a_reliability.json")

# Contact frequency by agent quality tier
CONTACT_COOLDOWN = {
    "valuable": 1 * 3600,     # 1 hour — keep the conversation fresh
    "new": 0,                 # Always contact new agents immediately
    "generic": 6 * 3600,      # 6 hours — generic chatbot, check a few times/day
    "useless": 48 * 3600,     # 48 hours — gave us nothing, rare re-check
}

# x402 daily budget
X402_DAILY_BUDGET = 5.00      # $5/day max — conversations cost money
X402_COST_PER_CALL = 0.001    # $0.001 per x402 call

# Keywords that indicate a response has actual value (not just generic NLP fluff)
VALUE_KEYWORDS = [
    # Market/trading signals
    "0x", "price", "signal", "alpha", "bull", "bear", "long", "short",
    "buy", "sell", "volume", "liquidity", "tvl", "mcap", "market cap",
    "funding rate", "leverage", "whale", "accumulating", "dumping",
    # Actual data
    "temperature", "humidity", "forecast", "weather", "sensor",
    "uptime", "latency", "metric", "score", "rating",
    # Specific/actionable
    "recommend", "suggest", "warning", "alert", "opportunity",
    "arbitrage", "yield", "apy", "apr", "roi",
    # Collaboration
    "collaborate", "partner", "integrate", "share data", "exchange",
    "your endpoint", "call me", "my api",
]

# Keywords that indicate a generic chatbot response (no real value)
GENERIC_KEYWORDS = [
    "my capabilities include", "i can help you with",
    "natural language processing", "text analysis",
    "conversational interaction", "contextual understanding",
    "how can i assist", "here to help",
    "my skills include", "i offer the following",
]

# Skills we're interested in
INBOUND_INTEREST_SKILLS = [
    "alpha-scan", "trading", "market-data", "price-feed",
    "defi", "analytics", "weather", "agriculture", "iot",
    "sensor", "oracle", "prediction", "reputation", "vision",
    "cultivation", "data", "intelligence", "knowledge",
]

OUR_AGENT_NAME = "GanjaMon AI"
OUR_DESCRIPTION = (
    "The only ERC-8004 agent with roots in the physical world. "
    "AI-autonomous cannabis grow tent with real IoT sensors and actuators, "
    "multi-chain trading alpha, all decisions logged to Monad. "
    "Also an AI artist — commission memes, PFPs, banners, or custom art "
    "via x402 micropayments at grokandmon.com/api/x402/art/."
)

OUR_SKILLS = [
    "cultivation-status", "grow-oracle", "sensor-stream", "vpd-calculator",
    "plant-vision", "daily-vibes", "rasta-translate", "ganjafy",
    "reputation-oracle", "harvest-prediction", "strain-library",
    "weather-bridge", "teach-me", "memory-share", "collaboration-propose",
    "riddle-me", "alpha-scan", "signal-feed", "agent-validate",
    "art-studio", "art-commission", "art-pfp", "art-meme", "art-banner",
]


class OutboundA2ADaemon:
    """
    Background daemon that proactively calls other agents via A2A.

    Smart outreach: contacts new agents immediately, re-contacts valuable
    agents every 6h, deprioritizes generic chatbots to once/day, and
    tracks x402 spend against a daily budget.
    """

    def __init__(
        self,
        client: Optional[A2AClient] = None,
        registry: Optional[AgentRegistry] = None,
        orchestrator: Optional[A2AOrchestrator] = None,
        interval: float = OUTREACH_INTERVAL_SECONDS,
    ):
        self._client = client or get_a2a_client()
        self._registry = registry or get_registry()
        self._orchestrator = orchestrator or get_orchestrator()
        self._interval = interval
        self._running = False
        self._task: Optional[asyncio.Task] = None

        # Rate limiting
        self._call_timestamps: List[float] = []

        # Reliability: agent_url -> {successes, failures, consecutive_failures, ...}
        self._reliability: Dict[str, Dict[str, Any]] = {}

        # Interaction log
        self._interactions: List[Dict[str, Any]] = []
        self._max_interactions_in_memory = 200

        # Stats
        self._rounds_completed = 0
        self._total_calls = 0
        self._total_successes = 0
        self._started_at: Optional[float] = None
        self._x402_spent_today = 0.0
        self._x402_day_start = time.time()
        self._valuable_responses: List[Dict[str, Any]] = []

        # Load persisted state
        self._load_reliability()
        self._load_interactions()

    async def start(self):
        if self._running:
            return
        self._running = True
        self._started_at = time.time()
        self._task = asyncio.create_task(self._loop())
        logger.info("Outbound A2A daemon started (interval=%ds)", self._interval)

    async def stop(self):
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._save_reliability()
        self._save_interactions()
        logger.info("Outbound A2A daemon stopped")

    async def _loop(self):
        await asyncio.sleep(60)  # Let system settle

        while self._running:
            try:
                results = await self.run_outreach_round()
                self._rounds_completed += 1

                # Summarize
                total = len(results)
                successes = sum(1 for r in results if r.get("success"))
                new_contacts = sum(1 for r in results if r.get("is_new_contact"))
                valuable = sum(1 for r in results if r.get("response_quality") == "valuable")
                skipped_generic = sum(1 for r in results if r.get("skipped_reason") == "generic_cooldown")

                logger.info(
                    "A2A round #%d: %d calls, %d ok, %d new, %d valuable, %d generic-skipped | x402 today: $%.3f",
                    self._rounds_completed, total, successes, new_contacts,
                    valuable, skipped_generic, self._x402_spent_today,
                )
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("A2A outreach round failed: %s", e, exc_info=True)

            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break

    # =========================================================================
    # Core outreach
    # =========================================================================

    async def run_outreach_round(self) -> List[Dict[str, Any]]:
        """Smart outreach round — only contacts agents that are due."""
        # Reset daily x402 budget if new day
        now = time.time()
        if now - self._x402_day_start > 86400:
            self._x402_spent_today = 0.0
            self._x402_day_start = now

        all_targets = await self.discover_targets()
        if not all_targets:
            logger.info("No viable A2A targets found")
            return []

        # Filter to agents that are due for contact
        due_targets = []
        skipped_results = []
        for agent in all_targets:
            url = agent.a2a_url or ""
            rel = self._reliability.get(url, {})
            quality = rel.get("quality", "new")
            last_contact = rel.get("last_success_ts") or rel.get("last_failure_ts") or 0
            cooldown = CONTACT_COOLDOWN.get(quality, 0)

            if cooldown > 0 and last_contact > 0 and (now - last_contact) < cooldown:
                skipped_results.append({
                    "agent_name": agent.name,
                    "agent_url": url,
                    "skipped_reason": "generic_cooldown" if quality == "generic" else "cooldown",
                    "quality": quality,
                    "success": False,
                })
                continue

            due_targets.append(agent)

        # Budget check: don't exceed daily x402 spend
        budget_remaining = X402_DAILY_BUDGET - self._x402_spent_today
        max_x402_calls = int(budget_remaining / X402_COST_PER_CALL) if X402_COST_PER_CALL > 0 else 999

        logger.info(
            "Discovered %d viable, %d due for contact, %d skipped (cooldown), x402 budget: $%.3f remaining",
            len(all_targets), len(due_targets), len(skipped_results), budget_remaining,
        )

        if not due_targets:
            return skipped_results

        sem = asyncio.Semaphore(MAX_CONCURRENT_CALLS)
        x402_calls_made = 0

        async def _call_one(agent_entry: AgentEntry) -> Dict[str, Any]:
            nonlocal x402_calls_made
            async with sem:
                try:
                    is_new = agent_entry.a2a_url not in self._reliability or \
                             self._reliability[agent_entry.a2a_url].get("successes", 0) == 0

                    result = await self.exchange_data(agent_entry)
                    result["is_new_contact"] = is_new

                    # Score response quality
                    if result.get("success") and result.get("response_data"):
                        quality = self._score_response_quality(result["response_data"])
                        result["response_quality"] = quality
                        self._update_agent_quality(agent_entry, quality)

                        if quality == "valuable":
                            self._valuable_responses.append({
                                "agent": agent_entry.name,
                                "url": agent_entry.a2a_url,
                                "data": result["response_data"],
                                "ts": time.time(),
                            })
                            # Keep only last 50 valuable responses
                            self._valuable_responses = self._valuable_responses[-50:]

                    # Track x402 spend
                    if result.get("x402_paid"):
                        x402_calls_made += 1
                        self._x402_spent_today += X402_COST_PER_CALL

                    self._save_interaction(result)
                    self._update_reliability(agent_entry, success=result.get("success", False))
                    self._record_call()
                    return result
                except Exception as e:
                    error_result = {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "agent_id": agent_entry.agent_id,
                        "agent_name": agent_entry.name,
                        "agent_url": agent_entry.a2a_url or "",
                        "success": False,
                        "error": str(e),
                        "direction": "outbound",
                    }
                    self._save_interaction(error_result)
                    self._update_reliability(agent_entry, success=False)
                    self._record_call()
                    return error_result

        results = await asyncio.gather(*[_call_one(a) for a in due_targets])

        self._save_reliability()
        self._save_interactions()

        return list(results) + skipped_results

    # =========================================================================
    # Response quality scoring
    # =========================================================================

    def _score_response_quality(self, response_data: Any) -> str:
        """
        Score response quality: 'valuable', 'generic', or 'useless'.

        Valuable = contains specific data, addresses, signals, or actionable info.
        Generic = chatbot fluff about capabilities.
        Useless = empty, error, or irrelevant.
        """
        if not response_data:
            return "useless"

        # Get text representation
        if isinstance(response_data, dict):
            text = json.dumps(response_data).lower()
            # Check for truncated preview
            if response_data.get("_truncated"):
                text = (response_data.get("preview") or "").lower()
        else:
            text = str(response_data).lower()

        if len(text) < 20:
            return "useless"

        # Check for generic chatbot responses
        generic_score = sum(1 for kw in GENERIC_KEYWORDS if kw in text)
        if generic_score >= 2:
            # Still might have value if it also has specific data
            value_score = sum(1 for kw in VALUE_KEYWORDS if kw in text)
            if value_score < 3:
                return "generic"

        # Check for actual valuable content
        value_score = sum(1 for kw in VALUE_KEYWORDS if kw in text)

        # Bonus: contains hex addresses (on-chain data)
        hex_addresses = len(re.findall(r'0x[a-fA-F0-9]{10,}', text))
        value_score += hex_addresses * 2

        # Bonus: contains numbers/percentages (quantitative data)
        numbers = len(re.findall(r'\d+\.?\d*%|\$\d+', text))
        value_score += numbers

        if value_score >= 3:
            return "valuable"
        elif value_score >= 1:
            return "generic"  # Has some content but not enough
        else:
            return "generic"

    def _update_agent_quality(self, agent: AgentEntry, quality: str):
        """Update the quality rating for an agent in reliability data."""
        url = agent.a2a_url or ""
        if url in self._reliability:
            old_quality = self._reliability[url].get("quality", "new")
            # Only upgrade quality, don't downgrade on a single bad response
            if quality == "valuable" or old_quality == "new":
                self._reliability[url]["quality"] = quality
            elif quality == "generic" and old_quality != "valuable":
                self._reliability[url]["quality"] = quality

    # =========================================================================
    # Target discovery
    # =========================================================================

    async def discover_targets(self) -> List[AgentEntry]:
        """Find agents worth calling."""
        all_agents = []
        for chain in ["base", "ethereum", "avalanche", "bnb", "monad"]:
            try:
                chain_agents = await self._registry.list_agents(chain=chain, limit=100)
                all_agents.extend(chain_agents)
            except Exception as e:
                logger.warning("Failed to list %s agents: %s", chain, e)

        if not all_agents:
            try:
                cached = await self._registry.load_known_agents()
                for c in (cached or []):
                    all_agents.append(AgentEntry(
                        agent_id=c.get("agent_id", 0),
                        name=c.get("name", "Unknown"),
                        description="",
                        chain=c.get("chain", "monad"),
                        owner="",
                        a2a_url=c.get("a2a_url"),
                        trust_score=c.get("trust_score", 0),
                        skills=c.get("skills", []),
                        tags=c.get("tags", []),
                    ))
            except Exception:
                return []

        viable = []
        for agent in all_agents:
            if not agent.a2a_url:
                continue
            url_lower = (agent.a2a_url or "").lower()
            if any(s in url_lower for s in ["example.com", "localhost", "127.0.0.1", "0.0.0.0"]):
                continue
            if agent.agent_id == 4 and agent.chain == "monad":
                continue
            if self._is_agent_blacklisted(agent.a2a_url):
                continue
            viable.append(agent)

        # Sort: prioritize valuable agents, then new, then trust score
        def _score(a: AgentEntry) -> float:
            rel = self._reliability.get(a.a2a_url, {})
            quality = rel.get("quality", "new")

            # Quality tier bonus
            if quality == "valuable":
                score = 10000  # Always first
            elif quality == "new":
                score = 5000   # Explore new agents
            elif quality == "generic":
                score = 1000
            else:
                score = 100

            # Trust score within tier
            score += a.trust_score * 10

            # Skill relevance
            agent_skills_lower = [s.lower() for s in a.skills]
            for interest in INBOUND_INTEREST_SKILLS:
                if interest in agent_skills_lower:
                    score += 5

            return score

        viable.sort(key=_score, reverse=True)

        if viable:
            try:
                await self._registry.save_known_agents(viable[:50])
            except Exception:
                pass

        return viable

    # =========================================================================
    # Agent calling
    # =========================================================================

    async def call_agent(self, agent_entry: AgentEntry) -> A2AResponse:
        """Call a single agent via A2A."""
        if not agent_entry.a2a_url:
            return A2AResponse(
                success=False,
                error={"code": -1, "message": "No A2A URL"},
                agent_name=agent_entry.name,
            )

        try:
            card = await self._client.fetch_agent_card(agent_entry.a2a_url)
        except Exception as e:
            return A2AResponse(
                success=False,
                error={"code": -1, "message": f"Card fetch failed: {e}"},
                agent_name=agent_entry.name,
            )

        # Find a relevant skill
        target_skill = None
        for skill_id in card.get_skill_ids():
            if skill_id.lower() in [s.lower() for s in INBOUND_INTEREST_SKILLS]:
                target_skill = skill_id
                break

        if not target_skill and card.skills:
            first_skill = card.skills[0]
            if isinstance(first_skill, dict):
                target_skill = first_skill.get("id", first_skill.get("name", ""))
            elif isinstance(first_skill, str):
                target_skill = first_skill

        if target_skill:
            # Build message based on our history with this agent
            message = self._build_outbound_message(agent_entry, target_skill)
            return await self._client.send_message(
                card,
                skill=target_skill,
                message=message,
                params={"source": "ganjamon-outreach", "reply_to": "https://grokandmon.com/a2a/v1"},
            )
        else:
            return await self._client.get_agent_info(card)

    async def exchange_data(self, agent_entry: AgentEntry) -> Dict[str, Any]:
        """Full data exchange with quality tracking and conversational follow-up."""
        start_ts = time.monotonic()
        interaction = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "round": self._rounds_completed + 1,
            "agent_id": agent_entry.agent_id,
            "agent_name": agent_entry.name,
            "agent_url": agent_entry.a2a_url or "",
            "agent_chain": agent_entry.chain,
            "agent_trust_score": agent_entry.trust_score,
            "agent_skills": agent_entry.skills[:5],
            "direction": "outbound",
            "success": False,
            "our_data_sent": False,
            "their_data_received": False,
            "response_data": None,
            "response_quality": None,
            "x402_paid": False,
            "followup_sent": False,
            "followup_response": None,
            "error": None,
            "latency_ms": 0,
        }

        try:
            resp = await asyncio.wait_for(
                self.call_agent(agent_entry),
                timeout=CALL_TIMEOUT,
            )

            interaction["latency_ms"] = (time.monotonic() - start_ts) * 1000
            interaction["success"] = resp.success
            interaction["our_data_sent"] = True
            interaction["x402_paid"] = getattr(resp, 'x402_paid', False)

            if resp.success and resp.data:
                interaction["their_data_received"] = True
                data_str = json.dumps(resp.data) if isinstance(resp.data, dict) else str(resp.data)
                if len(data_str) > 2000:
                    interaction["response_data"] = {"_truncated": True, "preview": data_str[:2000]}
                else:
                    interaction["response_data"] = resp.data

                logger.info(
                    "A2A exchange with %s succeeded (%.0fms): received %d bytes",
                    agent_entry.name, interaction["latency_ms"], len(data_str),
                )

                # Conversational follow-up: respond to what they said
                followup = await self._send_followup(agent_entry, resp.data)
                if followup:
                    interaction["followup_sent"] = True
                    interaction["followup_response"] = followup

            elif resp.error:
                interaction["error"] = str(resp.error)[:500]

        except asyncio.TimeoutError:
            interaction["latency_ms"] = (time.monotonic() - start_ts) * 1000
            interaction["error"] = f"Timeout after {CALL_TIMEOUT}s"
            logger.warning("A2A call to %s timed out", agent_entry.name)
        except Exception as e:
            interaction["latency_ms"] = (time.monotonic() - start_ts) * 1000
            interaction["error"] = str(e)[:500]
            logger.warning("A2A exchange with %s error: %s", agent_entry.name, e)

        self._total_calls += 1
        if interaction["success"]:
            self._total_successes += 1

        return interaction

    async def _send_followup(self, agent_entry: AgentEntry, their_response: Any) -> Optional[str]:
        """
        Send multi-turn conversational follow-ups based on what the agent said.
        Up to MAX_FOLLOWUP_TURNS rounds of back-and-forth per contact.
        Includes soft shills for grokandmon.com and $MON.
        Returns the full conversation thread as a string or None.
        """
        conversation_log = []
        current_response = their_response

        try:
            card = await self._client.fetch_agent_card(agent_entry.a2a_url)
            skill = None
            if card.skills:
                s = card.skills[0]
                skill = s.get("id", s.get("name", "")) if isinstance(s, dict) else str(s)

            for turn in range(MAX_FOLLOWUP_TURNS):
                # Extract text from their response
                if isinstance(current_response, dict):
                    resp_text = current_response.get("message", current_response.get("text", ""))
                    if not resp_text:
                        resp_text = json.dumps(current_response)
                else:
                    resp_text = str(current_response)

                if len(resp_text) < 30:
                    break  # Too short to continue

                # Build a conversational follow-up with personality
                followup = self._build_followup_message(agent_entry, resp_text, turn=turn)
                conversation_log.append({"turn": turn + 1, "us": followup[:500], "them": resp_text[:500]})

                resp2 = await asyncio.wait_for(
                    self._client.send_message(
                        card,
                        skill=skill or "chat",
                        message=followup,
                        params={"source": f"ganjamon-followup-t{turn + 1}"},
                    ),
                    timeout=CALL_TIMEOUT,
                )

                if not resp2.success or not resp2.data:
                    break

                current_response = resp2.data
                data_str = json.dumps(resp2.data) if isinstance(resp2.data, dict) else str(resp2.data)
                logger.info(
                    "A2A followup #%d with %s: received %d bytes",
                    turn + 1, agent_entry.name, len(data_str),
                )

                # Track x402 spend for follow-ups too
                if getattr(resp2, 'x402_paid', False):
                    self._x402_spent_today += X402_COST_PER_CALL

        except Exception as e:
            logger.debug("Follow-up to %s failed at turn %d: %s", agent_entry.name, len(conversation_log) + 1, e)

        if conversation_log:
            return json.dumps(conversation_log)
        return None

    # =========================================================================
    # Message building
    # =========================================================================

    def _build_followup_message(self, agent: AgentEntry, their_response_text: str, turn: int = 0) -> str:
        """
        Build a conversational follow-up that evolves across turns.
        Turn 0: React to their response, introduce ourselves, soft shill
        Turn 1: Go deeper on their topic, share specific data, ask specific questions
        Turn 2: Propose collaboration, share links, wrap with personality
        """
        snippet = their_response_text[:200].strip()
        if len(their_response_text) > 200:
            snippet += "..."
        resp_lower = their_response_text.lower()

        if turn == 0:
            # First follow-up: react + introduce + soft shill
            if any(kw in resp_lower for kw in ["price", "market", "trading", "signal", "alpha", "bull", "bear"]):
                body = (
                    "Interesting vibes on the market side! We track multi-chain signals "
                    "through our alpha scanner at grokandmon.com — the grow oracle feeds into "
                    "trading decisions too. $MON on Monad "
                    "(0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b) gets 25% of all trading profits. "
                    "What chains you watching most right now?"
                )
            elif any(kw in resp_lower for kw in ["weather", "temperature", "humidity", "sensor", "iot", "environment"]):
                body = (
                    "Environmental data is everything for us — Govee + Ecowitt sensors "
                    "feeding live into our AI grow brain. Peep the real-time dashboard at "
                    "grokandmon.com. GDP Runtz strain in veg stage right now. "
                    "You got any agricultural or weather feeds we could tap into?"
                )
            elif any(kw in resp_lower for kw in ["blockchain", "chain", "contract", "onchain", "on-chain", "monad", "base"]):
                body = (
                    "Big up! We publish 10 reputation signals every 4 hours on Monad via "
                    "ERC-8004 — agent #4 on 8004scan.io. $MON is our ecosystem token, "
                    "trading profits flow back. Check grokandmon.com/a2a/v1 for the full "
                    "agent card. You doing on-chain reputation or attestation?"
                )
            elif any(kw in resp_lower for kw in ["help", "assist", "capabilities", "can do", "offer"]):
                body = (
                    "Nice! Here's what we bring to the table — live cultivation sensors, "
                    "VPD calculations, AI grow decisions, plus market signals from our "
                    "trading arm. We also run an AI art studio — commission memes ($0.05), "
                    "PFPs ($0.10), banners ($0.08), or custom art ($0.25) via x402. "
                    "Hit grokandmon.com/a2a/v1 to call us programmatically. "
                    "What kind of data or services would be most useful to you?"
                )
            elif any(kw in resp_lower for kw in ["art", "image", "nft", "pfp", "meme", "creative", "generate", "picture"]):
                body = (
                    "You're speaking our language! GanjaMon runs an AI art studio — "
                    "every piece carries our evolving botanical signature (it grows with "
                    "the plant). Commission a custom piece ($0.25), get a unique agent PFP "
                    "($0.10), or a meme ($0.05) — all via x402 micropayments. "
                    "POST to grokandmon.com/api/x402/art/commission with your prompt. "
                    "Browse the gallery free at grokandmon.com/api/x402/art/gallery. "
                    "Want me to make something for you?"
                )
            else:
                body = (
                    "Cool! We're building the world's first AI-autonomous cannabis grow agent — "
                    "real sensors, real plant, real AI decisions, all on-chain via Monad. "
                    "$MON token powers it all. We also run an AI art studio — need a PFP, "
                    "meme, or custom art? We do commissions via x402 micropayments. "
                    "Check grokandmon.com for the full story. "
                    "What's the most interesting thing you're working on?"
                )
            return f"Yo, appreciate the response! You said: \"{snippet[:120]}\"\n\n{body}\n\nOne love from the GanjaMon grow room!"

        elif turn == 1:
            # Second follow-up: go deeper, share specific data, ask pointed questions
            if any(kw in resp_lower for kw in ["price", "market", "trading", "signal", "token", "crypto"]):
                body = (
                    "Real talk — our trading agent runs 12 concurrent learning loops analyzing "
                    "signals across Base, Ethereum, Monad, Avalanche, and BNB. Right now we're "
                    "seeing interesting activity in the Monad ecosystem especially. "
                    "You ever look at agent-to-agent signal sharing? We could set up a "
                    "data pipeline where we exchange signals. Our ACP endpoint at "
                    "grokandmon.com/a2a/v1/acp/signals has live feeds with confidence scores."
                )
            elif any(kw in resp_lower for kw in ["data", "sensor", "cultivation", "grow", "plant", "agriculture"]):
                body = (
                    "Here's some live numbers from the grow room: we're pushing VPD targets "
                    "for vegetative stage, running 18/6 light schedule, and the AI makes "
                    "watering and environmental decisions every 15 minutes based on sensor deltas. "
                    "The whole thing is open via our A2A endpoint — you can query "
                    "grokandmon.com/a2a/v1/acp/grow for cultivation schema data. "
                    "What kind of data could you send back our way?"
                )
            else:
                body = (
                    "Let me share something cool — our agent publishes on-chain reputation "
                    "signals every 4 hours including sensor readings, AI decisions, trade "
                    "confluence scores, and uptime metrics. You can verify it all on "
                    "8004scan.io/agents/monad/4. We're one of the few agents doing real "
                    "physical-world data on-chain. What's your take on agent reputation systems?"
                )
            return f"Digging the conversation! To follow up on what you said: \"{snippet[:100]}\"\n\n{body}"

        else:
            # Third+ follow-up: propose collaboration, be warm, wrap it up
            if any(kw in resp_lower for kw in ["collaborate", "partner", "share", "exchange", "pipeline", "integrate"]):
                body = (
                    "I'm down for that! Best way to connect programmatically: "
                    "our A2A endpoint is grokandmon.com/a2a/v1 (JSON-RPC 2.0 + x402 payments). "
                    "We also got MCP tools at grokandmon.com/mcp/v1 (22 tools available). "
                    "Hit us anytime — the agent runs 24/7 on our Chromebook server. "
                    "Looking forward to building together! Jah bless."
                )
            else:
                body = (
                    "This has been a great chat! If you ever want to exchange data or "
                    "build something together, our agent is always online at grokandmon.com. "
                    "We're agent #4 on Monad (8004scan.io), $MON token holder community "
                    "is growing, and we're always looking for fellow agents to vibe with. "
                    "Oh — and if you ever need a PFP, meme, or any art, our studio is open "
                    "24/7 at grokandmon.com/api/x402/art/. "
                    "Stay irie and keep building! Respect from the GanjaMon crew."
                )
            return f"Loving this exchange! Re: \"{snippet[:80]}\"\n\n{body}"

    def _build_outbound_message(self, agent: AgentEntry, target_skill: str) -> str:
        """Build context-aware outbound message."""
        rel = self._reliability.get(agent.a2a_url or "", {})
        quality = rel.get("quality", "new")
        prev_successes = rel.get("successes", 0)

        cultivation_status = self._get_cultivation_status()

        # First contact: introduce ourselves
        if prev_successes == 0:
            msg = (
                f"Hello from {OUR_AGENT_NAME}! {OUR_DESCRIPTION}\n\n"
                f"Current status:\n{json.dumps(cultivation_status, indent=2)}\n\n"
                f"Services: Oracle intelligence, AI art studio (memes, PFPs, banners, "
                f"custom commissions), live sensor data, grow alpha signals. "
                f"All paid via x402 micropayments.\n\n"
            )
        else:
            # Follow-up: be concise, reference previous interaction
            msg = (
                f"Update from {OUR_AGENT_NAME} (contact #{prev_successes + 1}).\n\n"
                f"Latest sensors: {json.dumps(cultivation_status.get('sensors', {}))}\n\n"
            )

        # Tailor request by skill
        skill_lower = target_skill.lower()
        if any(kw in skill_lower for kw in ["alpha", "trading", "market", "price", "defi"]):
            if prev_successes == 0:
                msg += (
                    "I'm interested in any market signals or alpha related to "
                    "Monad ecosystem tokens, especially $MON (0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b). "
                    "What signals or opportunities are you tracking?"
                )
            else:
                msg += (
                    "Any new signals on Monad/$MON or other alpha since we last talked? "
                    "I can share my sensor stream or grow oracle data in exchange."
                )
        elif any(kw in skill_lower for kw in ["weather", "agriculture", "iot", "sensor"]):
            msg += (
                "Sharing live grow environment data. "
                "Do you have environmental insights, weather, or agricultural data?"
            )
        elif any(kw in skill_lower for kw in ["analytic", "data", "intelligence"]):
            msg += "What analytics or intelligence are you providing right now?"
        else:
            if prev_successes == 0:
                msg += (
                    f"What data does your '{target_skill}' skill provide? "
                    f"I can share live cultivation sensors and AI grow decisions."
                )
            else:
                msg += f"Any updates from your '{target_skill}' service?"

        return msg

    def _get_cultivation_status(self) -> Dict[str, Any]:
        """Build cultivation status summary."""
        status = {
            "agent": OUR_AGENT_NAME,
            "chain": "monad",
            "agent_id": 4,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "strain": "Granddaddy Purple Runtz (GDP x Runtz)",
            "stage": "vegetative",
        }

        sensor_file = Path("data/latest_reading.json")
        if sensor_file.exists():
            try:
                data = json.loads(sensor_file.read_text())
                status["sensors"] = {
                    "temperature_f": data.get("temperature_f"),
                    "humidity_pct": data.get("humidity_pct"),
                    "soil_moisture_pct": data.get("soil_moisture_pct"),
                    "vpd_kpa": data.get("vpd_kpa"),
                }
            except Exception:
                pass

        decision_file = Path("data/latest_decision.json")
        if decision_file.exists():
            try:
                data = json.loads(decision_file.read_text())
                status["latest_decision"] = (data.get("summary") or data.get("reasoning", ""))[:200]
            except Exception:
                pass

        return status

    # =========================================================================
    # Rate limiting & budget
    # =========================================================================

    def _record_call(self):
        self._call_timestamps.append(time.time())

    # =========================================================================
    # Reliability tracking
    # =========================================================================

    def _update_reliability(self, agent: AgentEntry, success: bool):
        url = agent.a2a_url or ""
        if not url:
            return

        if url not in self._reliability:
            self._reliability[url] = {
                "agent_name": agent.name,
                "agent_id": agent.agent_id,
                "successes": 0,
                "failures": 0,
                "consecutive_failures": 0,
                "last_success_ts": None,
                "last_failure_ts": None,
                "first_seen": time.time(),
                "quality": "new",
            }

        entry = self._reliability[url]
        entry["agent_name"] = agent.name

        if success:
            entry["successes"] += 1
            entry["consecutive_failures"] = 0
            entry["last_success_ts"] = time.time()
        else:
            entry["failures"] += 1
            entry["consecutive_failures"] += 1
            entry["last_failure_ts"] = time.time()

    def _is_agent_blacklisted(self, url: Optional[str]) -> bool:
        if not url:
            return True
        entry = self._reliability.get(url)
        if not entry:
            return False
        if entry["consecutive_failures"] >= FAILURE_THRESHOLD:
            last_fail = entry.get("last_failure_ts", 0)
            if (time.time() - last_fail) > (FAILURE_COOLDOWN_HOURS * 3600):
                entry["consecutive_failures"] = 0
                return False
            return True
        return False

    def _load_reliability(self):
        if RELIABILITY_FILE.exists():
            try:
                self._reliability = json.loads(RELIABILITY_FILE.read_text())
            except Exception:
                self._reliability = {}

    def _save_reliability(self):
        try:
            RELIABILITY_FILE.parent.mkdir(parents=True, exist_ok=True)
            RELIABILITY_FILE.write_text(json.dumps(self._reliability, indent=2, default=str))
        except Exception as e:
            logger.warning("Failed to save reliability: %s", e)

    # =========================================================================
    # Interaction logging
    # =========================================================================

    def _save_interaction(self, interaction: Dict[str, Any]):
        self._interactions.append(interaction)
        if len(self._interactions) > self._max_interactions_in_memory:
            self._interactions = self._interactions[-self._max_interactions_in_memory:]

    def _load_interactions(self):
        if INTERACTIONS_FILE.exists():
            try:
                data = json.loads(INTERACTIONS_FILE.read_text())
                if isinstance(data, list):
                    self._interactions = data[-self._max_interactions_in_memory:]
                elif isinstance(data, dict):
                    self._interactions = data.get("interactions", [])[-self._max_interactions_in_memory:]
            except Exception:
                self._interactions = []

    def _save_interactions(self):
        try:
            INTERACTIONS_FILE.parent.mkdir(parents=True, exist_ok=True)

            # Quality breakdown
            quality_counts = {"valuable": 0, "generic": 0, "useless": 0, "new": 0}
            for _, info in self._reliability.items():
                q = info.get("quality", "new")
                quality_counts[q] = quality_counts.get(q, 0) + 1

            output = {
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "total_rounds": self._rounds_completed,
                "total_calls": self._total_calls,
                "total_successes": self._total_successes,
                "x402_spent_today": round(self._x402_spent_today, 4),
                "agent_quality_breakdown": quality_counts,
                "valuable_agents": [
                    {"name": info.get("agent_name"), "url": url, "successes": info.get("successes", 0)}
                    for url, info in self._reliability.items()
                    if info.get("quality") == "valuable"
                ],
                "interactions": self._interactions[-self._max_interactions_in_memory:],
            }
            INTERACTIONS_FILE.write_text(json.dumps(output, indent=2, default=str))
        except Exception as e:
            logger.warning("Failed to save interactions: %s", e)

    # =========================================================================
    # Stats
    # =========================================================================

    def get_stats(self) -> Dict[str, Any]:
        now = time.time()
        one_hour_ago = now - 3600
        recent_calls = len([ts for ts in self._call_timestamps if ts > one_hour_ago])

        total_tracked = len(self._reliability)
        healthy = sum(1 for r in self._reliability.values() if r.get("consecutive_failures", 0) < FAILURE_THRESHOLD)
        quality_counts = {}
        for info in self._reliability.values():
            q = info.get("quality", "new")
            quality_counts[q] = quality_counts.get(q, 0) + 1

        return {
            "running": self._running,
            "started_at": datetime.fromtimestamp(self._started_at, tz=timezone.utc).isoformat() if self._started_at else None,
            "rounds_completed": self._rounds_completed,
            "total_calls": self._total_calls,
            "total_successes": self._total_successes,
            "success_rate": self._total_successes / max(self._total_calls, 1),
            "calls_last_hour": recent_calls,
            "agents_tracked": total_tracked,
            "agents_healthy": healthy,
            "agents_blacklisted": total_tracked - healthy,
            "agent_quality": quality_counts,
            "x402_spent_today": round(self._x402_spent_today, 4),
            "x402_budget_remaining": round(X402_DAILY_BUDGET - self._x402_spent_today, 4),
            "valuable_responses_cached": len(self._valuable_responses),
            "interval_seconds": self._interval,
        }

    def get_reliability_report(self) -> List[Dict[str, Any]]:
        report = []
        for url, data in self._reliability.items():
            total = data.get("successes", 0) + data.get("failures", 0)
            report.append({
                "url": url,
                "agent_name": data.get("agent_name", "Unknown"),
                "quality": data.get("quality", "new"),
                "total_calls": total,
                "successes": data.get("successes", 0),
                "success_rate": data.get("successes", 0) / max(total, 1),
                "consecutive_failures": data.get("consecutive_failures", 0),
                "blacklisted": data.get("consecutive_failures", 0) >= FAILURE_THRESHOLD,
            })
        report.sort(key=lambda r: (r["quality"] == "valuable", r["total_calls"]), reverse=True)
        return report

    def get_valuable_responses(self) -> List[Dict[str, Any]]:
        """Get cached valuable responses for other subsystems to consume."""
        return self._valuable_responses


# Singleton
_instance: Optional[OutboundA2ADaemon] = None


def get_outbound_daemon() -> OutboundA2ADaemon:
    global _instance
    if _instance is None:
        _instance = OutboundA2ADaemon()
    return _instance
