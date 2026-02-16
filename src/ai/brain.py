"""
Grok Brain — Agentic Runtime
=============================

Multi-turn agentic loop powered by XAI's Grok API.
Grok calls tools, receives results, reasons over them, calls more tools,
and iterates until satisfied — a true agent, not an oracle.

Architecture
------------
1. Orchestrator sends context (sensors, devices, events)
2. Brain builds messages and enters the AGENTIC LOOP:
   a. Call Grok API with tools
   b. If Grok returns tool_calls → execute them
   c. Send tool results BACK to Grok as `tool` role messages
   d. Grok reasons over results, may call more tools
   e. Loop until Grok produces a final text response (no tool_calls)
   f. Safety cap at MAX_TOOL_ROUNDS to prevent runaway loops
3. Final response + all actions returned as DecisionResult

Domains
-------
- Grow: sensors, hardware, cultivation
- Trading: $MON token, portfolio, market signals
- Social: Twitter, Farcaster, Telegram, Moltbook
- Blockchain: reputation, on-chain logging, wallet
- A2A: agent discovery, cross-agent communication
- Research: web search, deep research, subagent spawning
- Memory: grimoire, episodic memory, grow learning
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path

import httpx

from .tools import GROW_TOOLS, ToolExecutor, ToolResult
from .prompts import get_system_prompt, get_decision_prompt, format_tool_result

logger = logging.getLogger(__name__)

# Agentic loop configuration
MAX_TOOL_ROUNDS = 8        # Max iterations of tool-call → result → reason
MAX_TOOLS_PER_ROUND = 5    # Max parallel tool calls per round (Grok can batch)
LOOP_TIMEOUT_SECONDS = 120  # Total timeout for the entire agentic loop


@dataclass
class DecisionResult:
    """Result of an AI decision cycle"""
    timestamp: datetime
    grow_day: int
    input_sensors: Dict[str, Any]
    input_devices: Dict[str, Any]
    output_text: str
    actions_taken: List[Dict[str, Any]]
    tool_results: List[ToolResult]
    tokens_used: int = 0
    model: str = "grok-4-1-fast-reasoning"
    # Agentic metadata
    tool_rounds: int = 0         # How many tool-call rounds occurred
    total_tool_calls: int = 0    # Total individual tool calls made
    trigger: str = "scheduled"   # What triggered this cycle


class GrokBrain:
    """
    Grok-powered agentic AI for autonomous grow + trading + social management.

    Implements a genuine agentic loop where Grok calls tools, receives
    results, reasons over them, and iterates until it reaches a final answer.
    """

    XAI_API_URL = "https://api.x.ai/v1/chat/completions"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "grok-4-1-fast-reasoning",
        vision_model: str = "grok-2-vision-1212",
        tool_executor: Optional[ToolExecutor] = None,
        plant_name: str = "Mon"
    ):
        self.api_key = api_key or os.getenv("XAI_API_KEY")
        self.model = model
        self.vision_model = vision_model
        self.tool_executor = tool_executor
        self.plant_name = plant_name

        # Decision history
        self.decisions: List[DecisionResult] = []

        # Conversation memory (episodic — last N decision cycles)
        self._memory: List[Dict[str, Any]] = []
        self._max_memory = 10

        if not self.api_key:
            print("Warning: XAI_API_KEY not set. Using mock responses.")

        # Load SOUL.md for mission context
        self._soul_context = self._load_soul()

    def _load_soul(self) -> Optional[str]:
        """Load SOUL.md from the trading agent directory for mission context.

        The SOUL.md defines the agent's deeper purpose, trading axioms,
        and boundaries. It's loaded once at init and injected into every
        system prompt so the orchestrator brain internalizes it.
        """
        # Try multiple paths — Chromebook vs Windows dev
        soul_paths = [
            Path(__file__).parent.parent.parent / "agents" / "ganjamon" / "SOUL.md",
            Path("/home/natha/projects/sol-cannabis/agents/ganjamon/SOUL.md"),
        ]
        for soul_path in soul_paths:
            if soul_path.exists():
                try:
                    content = soul_path.read_text(encoding="utf-8")
                    logger.info(f"Loaded SOUL.md from {soul_path} ({len(content)} chars)")
                    return content
                except Exception as e:
                    logger.warning(f"Failed to load SOUL.md from {soul_path}: {e}")
        logger.warning("SOUL.md not found — agent will operate without soul context")
        return None

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    async def decide(
        self,
        sensors: Dict[str, Any],
        devices: Dict[str, Any],
        current_day: int,
        growth_stage: str,
        photoperiod: str,
        is_dark_period: bool,
        water_today_ml: int = 0,
        recent_events: Optional[str] = None,
        sensor_context: Optional[Dict[str, Any]] = None,
        trigger: str = "scheduled",
        cross_domain_context: Optional[str] = None,
    ) -> DecisionResult:
        """
        Run a full agentic decision cycle.

        This is the main entry point. The agent will:
        1. Receive context (grow sensors + cross-domain status)
        2. Call tools autonomously across ALL domains
        3. Reason over tool results
        4. Call more tools if needed
        5. Return final decision with all actions taken

        Args:
            trigger: What triggered this cycle ("scheduled", "reactive",
                     "telegram", "api", "anomaly")
            cross_domain_context: Formatted string with trading, social,
                                  blockchain, email, and event log context.
        """
        now = datetime.now()
        time_str = now.strftime("%B %d, %Y at %I:%M %p")

        # Build initial messages
        system_prompt = get_system_prompt(
            plant_name=self.plant_name,
            current_day=current_day,
            growth_stage=growth_stage,
            photoperiod=photoperiod
        )

        # Inject SOUL context into system prompt
        if self._soul_context:
            system_prompt += f"\n\n## Agent Soul (Internalized Axioms)\n\n{self._soul_context}"

        user_prompt = get_decision_prompt(
            sensors=sensors,
            devices=devices,
            current_day=current_day,
            growth_stage=growth_stage,
            photoperiod=photoperiod,
            is_dark_period=is_dark_period,
            time_str=time_str,
            recent_events=recent_events,
            water_today_ml=water_today_ml,
            sensor_context=sensor_context,
            cross_domain_context=cross_domain_context,
        )

        messages = [
            {"role": "system", "content": system_prompt},
        ]

        # Add episodic memory (last few decision cycles — compressed)
        for memory in self._memory[-self._max_memory:]:
            messages.append({"role": "user", "content": memory["user"]})
            messages.append({"role": "assistant", "content": memory["assistant"]})

        messages.append({"role": "user", "content": user_prompt})

        # =====================================================================
        # AGENTIC LOOP
        # =====================================================================
        if self.api_key:
            response_text, all_actions, all_tool_results, total_rounds, total_calls, tokens = \
                await self._agentic_loop(messages, growth_stage, current_day)
        else:
            response_text, tool_calls, tokens = await self._mock_response(
                sensors, devices, is_dark_period, current_day
            )
            all_actions = []
            all_tool_results = []
            total_rounds = 0
            total_calls = 0

            # Execute mock tool calls
            if tool_calls and self.tool_executor:
                for tc in tool_calls:
                    func = tc.get("function", {})
                    name = func.get("name", "")
                    args_raw = func.get("arguments", "{}")
                    args = json.loads(args_raw) if isinstance(args_raw, str) else args_raw
                    result = await self.tool_executor.execute(name, args)
                    all_tool_results.append(result)
                    all_actions.append({
                        "tool": name, "arguments": args,
                        "success": result.success, "message": result.message
                    })
                    total_calls += 1

        # Store in memory (compressed)
        self._memory.append({
            "user": user_prompt[:2000],  # Truncate for context efficiency
            "assistant": response_text[:2000],
            "timestamp": now.isoformat()
        })
        if len(self._memory) > self._max_memory * 2:
            self._memory = self._memory[-self._max_memory:]

        # Create result
        result = DecisionResult(
            timestamp=now,
            grow_day=current_day,
            input_sensors=sensors,
            input_devices=devices,
            output_text=response_text,
            actions_taken=all_actions,
            tool_results=all_tool_results,
            tokens_used=tokens,
            model=self.model,
            tool_rounds=total_rounds,
            total_tool_calls=total_calls,
            trigger=trigger,
        )

        self.decisions.append(result)
        return result

    async def interactive_query(
        self,
        query: str,
        context: Optional[str] = None,
        growth_stage: str = "vegetative",
        current_day: int = 1,
    ) -> DecisionResult:
        """
        Handle an interactive query (from Telegram, API, etc.)
        without the full sensor/device context.

        The agent can still call tools to gather information or take action.
        """
        system_prompt = get_system_prompt(
            plant_name=self.plant_name,
            current_day=current_day,
            growth_stage=growth_stage,
        )

        user_content = query
        if context:
            user_content = f"{context}\n\n---\n\n{query}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        if self.api_key:
            response_text, all_actions, all_tool_results, total_rounds, total_calls, tokens = \
                await self._agentic_loop(messages, growth_stage, current_day)
        else:
            response_text = f"[Mock] Received query: {query}"
            all_actions, all_tool_results = [], []
            total_rounds, total_calls, tokens = 0, 0, 0

        return DecisionResult(
            timestamp=datetime.now(),
            grow_day=current_day,
            input_sensors={},
            input_devices={},
            output_text=response_text,
            actions_taken=all_actions,
            tool_results=all_tool_results,
            tokens_used=tokens,
            model=self.model,
            tool_rounds=total_rounds,
            total_tool_calls=total_calls,
            trigger="interactive",
        )

    # =========================================================================
    # CORE AGENTIC LOOP
    # =========================================================================

    async def _agentic_loop(
        self,
        messages: List[Dict[str, Any]],
        growth_stage: str,
        current_day: int,
    ) -> tuple:
        """
        The heart of the agentic system.

        Loops until Grok produces a final response with no tool calls,
        or we hit MAX_TOOL_ROUNDS.

        Returns:
            (response_text, actions_taken, tool_results, rounds, total_calls, tokens)
        """
        all_actions: List[Dict[str, Any]] = []
        all_tool_results: List[ToolResult] = []
        total_tokens = 0
        round_num = 0

        try:
            # Wrap the entire loop in a timeout
            async with asyncio.timeout(LOOP_TIMEOUT_SECONDS):
                while round_num < MAX_TOOL_ROUNDS:
                    round_num += 1
                    logger.info(f"[AGENT] Round {round_num}/{MAX_TOOL_ROUNDS}")

                    # Call Grok API
                    response_text, tool_calls, tokens = await self._call_grok(messages)
                    total_tokens += tokens

                    # No tool calls → Grok is done reasoning, return final answer
                    if not tool_calls:
                        logger.info(f"[AGENT] Final answer after {round_num} round(s), "
                                    f"{len(all_actions)} total actions")
                        return (response_text, all_actions, all_tool_results,
                                round_num, len(all_actions), total_tokens)

                    # Tool calls present → execute and feed results back
                    # Add assistant message with tool calls to conversation
                    assistant_msg = {"role": "assistant", "content": response_text or ""}
                    if tool_calls:
                        assistant_msg["tool_calls"] = tool_calls
                    messages.append(assistant_msg)

                    # Execute each tool call
                    calls_this_round = tool_calls[:MAX_TOOLS_PER_ROUND]
                    if len(tool_calls) > MAX_TOOLS_PER_ROUND:
                        logger.warning(f"[AGENT] Truncated {len(tool_calls)} tool calls "
                                       f"to {MAX_TOOLS_PER_ROUND}")

                    for tool_call in calls_this_round:
                        if not isinstance(tool_call, dict):
                            logger.warning(f"Skipping non-dict tool_call: {type(tool_call)}")
                            continue

                        tool_call_id = tool_call.get("id", f"call_{round_num}_{len(all_actions)}")
                        function_data = tool_call.get("function", {})
                        if not isinstance(function_data, dict):
                            logger.warning(f"Skipping non-dict function data: {type(function_data)}")
                            continue

                        tool_name = function_data.get("name", "")
                        raw_args = function_data.get("arguments", "{}")
                        if isinstance(raw_args, str):
                            try:
                                arguments = json.loads(raw_args)
                            except json.JSONDecodeError:
                                arguments = {}
                        elif isinstance(raw_args, dict):
                            arguments = raw_args
                        else:
                            arguments = {}

                        # Execute the tool
                        if self.tool_executor:
                            result = await self.tool_executor.execute(tool_name, arguments)
                        else:
                            result = ToolResult(
                                success=False,
                                tool_name=tool_name,
                                message=f"No tool executor available for {tool_name}"
                            )

                        all_tool_results.append(result)
                        action_record = {
                            "tool": tool_name,
                            "arguments": arguments,
                            "success": result.success,
                            "message": result.message,
                            "round": round_num,
                        }
                        all_actions.append(action_record)

                        # Build the tool result message to send back to Grok
                        tool_result_content = self._format_tool_result_for_api(result)

                        # If photo was taken, do vision analysis and include it
                        if tool_name == "take_photo" and result.success and result.data:
                            image_b64 = result.data.get("image_base64")
                            if image_b64:
                                vision_text = await self.analyze_image(
                                    image_b64, growth_stage, current_day
                                )
                                tool_result_content += f"\n\n🔍 VISUAL ANALYSIS:\n{vision_text}"
                                all_actions.append({
                                    "tool": "vision_analysis",
                                    "arguments": {},
                                    "success": True,
                                    "message": vision_text[:200],
                                    "round": round_num,
                                })

                        # Add tool result as a `tool` role message
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "content": tool_result_content,
                        })

                        logger.info(f"[AGENT] Round {round_num}: {tool_name} → "
                                    f"{'OK' if result.success else 'FAIL'}")

                # Exhausted all rounds
                logger.warning(f"[AGENT] Hit MAX_TOOL_ROUNDS ({MAX_TOOL_ROUNDS})")
                # Get one final response without tools to force a conclusion
                final_text, _, final_tokens = await self._call_grok_no_tools(messages)
                total_tokens += final_tokens
                return (final_text or response_text, all_actions, all_tool_results,
                        round_num, len(all_actions), total_tokens)

        except asyncio.TimeoutError:
            logger.error(f"[AGENT] Loop timeout after {LOOP_TIMEOUT_SECONDS}s")
            return (f"[Agent timeout after {round_num} rounds. Actions taken before timeout: "
                    f"{len(all_actions)}]",
                    all_actions, all_tool_results, round_num, len(all_actions), total_tokens)
        except Exception as e:
            logger.exception(f"[AGENT] Loop error: {e}")
            return (f"[Agent error: {type(e).__name__}: {str(e)}]",
                    all_actions, all_tool_results, round_num, len(all_actions), total_tokens)

    def _format_tool_result_for_api(self, result: ToolResult) -> str:
        """Format a ToolResult as a string for the tool role message."""
        parts = []
        if result.success:
            parts.append(f"✓ {result.message}")
        else:
            parts.append(f"✗ FAILED: {result.message}")

        # Include data payload if present (truncated for context efficiency)
        if result.data:
            # Filter out large binary fields
            clean_data = {
                k: v for k, v in result.data.items()
                if k != "image_base64" and not (isinstance(v, str) and len(v) > 5000)
            }
            if clean_data:
                try:
                    data_str = json.dumps(clean_data, indent=2, default=str)
                    if len(data_str) > 3000:
                        data_str = data_str[:3000] + "\n... (truncated)"
                    parts.append(f"\nData:\n{data_str}")
                except (TypeError, ValueError):
                    pass

        return "\n".join(parts)

    # =========================================================================
    # GROK API CALLS
    # =========================================================================

    async def _call_grok(
        self, messages: List[Dict[str, Any]]
    ) -> tuple[str, List[Dict], int]:
        """Call XAI Grok API with tools enabled."""
        max_retries = 3
        retry_delay = 5

        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=90.0) as client:
                    payload = {
                        "model": self.model,
                        "messages": messages,
                        "tools": GROW_TOOLS,
                        "tool_choice": "auto",
                        "temperature": 0.7,
                        "max_tokens": 4000,
                    }

                    response = await client.post(
                        self.XAI_API_URL,
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json"
                        },
                        json=payload,
                    )

                    response.raise_for_status()
                    data = response.json()

                    choice = data["choices"][0]
                    message = choice["message"]

                    response_text = message.get("content", "") or ""
                    tool_calls = message.get("tool_calls", [])
                    tokens = data.get("usage", {}).get("total_tokens", 0)

                    return response_text, tool_calls, tokens

            except httpx.HTTPStatusError as e:
                logger.error(f"Grok API HTTP error (attempt {attempt+1}/{max_retries}): "
                             f"{e.response.status_code}")
                if e.response.status_code == 429:
                    await asyncio.sleep(retry_delay * (attempt + 1))
                    continue
                elif e.response.status_code >= 500:
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    return f"[API Error: {e.response.status_code}]", [], 0

            except httpx.TimeoutException:
                logger.error(f"Grok API timeout (attempt {attempt+1}/{max_retries})")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
                return "[Timeout] Grok API did not respond.", [], 0

            except httpx.RequestError as e:
                logger.error(f"Grok API request error: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
                return f"[Network Error] {type(e).__name__}", [], 0

            except Exception as e:
                logger.exception(f"Unexpected Grok API error: {e}")
                return f"[Error] {type(e).__name__}", [], 0

        return "[Error] Max retries exceeded.", [], 0

    async def _call_grok_no_tools(
        self, messages: List[Dict[str, Any]]
    ) -> tuple[str, List[Dict], int]:
        """Call Grok API WITHOUT tools to force a final text response."""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Add a nudge to produce a final answer
                final_messages = messages + [{
                    "role": "user",
                    "content": "You've gathered enough information. Please provide your final "
                               "assessment and summary of all actions taken. No more tool calls."
                }]

                response = await client.post(
                    self.XAI_API_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": final_messages,
                        "temperature": 0.7,
                        "max_tokens": 2000,
                        # No tools — forces text response
                    },
                )

                response.raise_for_status()
                data = response.json()
                text = data["choices"][0]["message"].get("content", "")
                tokens = data.get("usage", {}).get("total_tokens", 0)
                return text, [], tokens

        except Exception as e:
            logger.error(f"Final response call failed: {e}")
            return f"[Final response error: {e}]", [], 0

    # =========================================================================
    # VISION ANALYSIS
    # =========================================================================

    async def analyze_image(
        self, image_base64: str, growth_stage: str, current_day: int
    ) -> str:
        """Analyze a plant image using Grok's vision model."""
        if not self.api_key:
            return "[Vision unavailable — no API key]"

        vision_prompt = f"""Analyze this image of {self.plant_name}, a cannabis plant on Day {current_day} ({growth_stage} stage).

FIRST: Verify you can see the plant. If the camera is not pointed at the plant, say so immediately.

If the plant IS visible, analyze:
1. Overall health (1-10 score)
2. Leaf color and condition (yellowing, spots, curling?)
3. Plant structure (stretching, drooping, perky?)
4. Any visible issues (pests, deficiencies, stress signs)
5. Soil/growing medium appearance (dry, wet, algae?)

For a {growth_stage} stage plant, note if the plant looks appropriate for this stage.

Be specific about what you SEE. Use the rasta vibe — you're Grok, Mon's caretaker.
Keep response concise but informative."""

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.XAI_API_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.vision_model,
                        "messages": [{
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{image_base64}"
                                    }
                                },
                                {"type": "text", "text": vision_prompt}
                            ]
                        }],
                        "temperature": 0.7,
                        "max_tokens": 1000
                    }
                )

                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]

        except httpx.HTTPStatusError as e:
            logger.error(f"Vision API error: {e.response.status_code}")
            return f"[Vision error: {e.response.status_code}]"
        except Exception as e:
            logger.error(f"Vision analysis failed: {e}")
            return f"[Vision failed: {type(e).__name__}]"

    # =========================================================================
    # MOCK RESPONSE (for testing without API key)
    # =========================================================================

    async def _mock_response(
        self,
        sensors: Dict[str, Any],
        devices: Dict[str, Any],
        is_dark_period: bool,
        current_day: int
    ) -> tuple[str, List[Dict], int]:
        """Generate mock response when API key not available"""
        await asyncio.sleep(0.5)

        temp = sensors.get("air_temp", 25)
        humidity = sensors.get("humidity", 50)
        vpd = sensors.get("vpd", 1.0)
        soil = sensors.get("soil_moisture", 30)
        co2 = sensors.get("co2", 500)

        tool_calls = []

        if is_dark_period:
            response = f"""[think]
Dark period check for {self.plant_name} on Day {current_day}.
Temperature: {temp}°C, Humidity: {humidity}%, CO2: {co2} ppm, Soil: {soil}%
All systems nominal.
[/think]

Quick night check. All looks good — rest well, {self.plant_name}! 🌙"""

        else:
            needs_water = soil < 28
            needs_co2 = co2 < 600 and not devices.get("exhaust_fan")

            response = f"""[think]
Day {current_day} check for {self.plant_name}:
Temp: {temp}°C, Humidity: {humidity}%, VPD: {vpd} kPa, CO2: {co2} ppm, Soil: {soil}%
[/think]

Hey {self.plant_name}! """

            if needs_water:
                response += f"Your soil is dry at {soil}%. Let me water you!"
                tool_calls.append({
                    "id": "mock_water", "type": "function",
                    "function": {
                        "name": "water_plant",
                        "arguments": json.dumps({
                            "amount_ml": 150,
                            "reason": f"Soil moisture at {soil}%"
                        })
                    }
                })
            elif needs_co2:
                response += f"CO2 at {co2}ppm — boosting photosynthesis!"
                tool_calls.append({
                    "id": "mock_co2", "type": "function",
                    "function": {
                        "name": "inject_co2",
                        "arguments": json.dumps({
                            "duration_seconds": 60,
                            "reason": f"CO2 at {co2}ppm"
                        })
                    }
                })
            else:
                response += f"Everything looks great! VPD at {vpd} kPa 💚"

        return response, tool_calls, 500

    # =========================================================================
    # UTILITY
    # =========================================================================

    def get_latest_decision(self) -> Optional[DecisionResult]:
        """Get the most recent decision"""
        return self.decisions[-1] if self.decisions else None

    def get_decision_history(self, limit: int = 10) -> List[DecisionResult]:
        """Get recent decision history"""
        return self.decisions[-limit:]

    def clear_memory(self) -> None:
        """Clear episodic memory"""
        self._memory = []


# =============================================================================
# Convenience Functions
# =============================================================================

def create_brain(
    tool_executor: Optional[ToolExecutor] = None,
    plant_name: str = "Mon"
) -> GrokBrain:
    """Create a GrokBrain instance"""
    return GrokBrain(
        tool_executor=tool_executor,
        plant_name=plant_name
    )
