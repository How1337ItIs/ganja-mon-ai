"""
Multi-Agent Orchestrator
========================

Coordinate parallel A2A calls to multiple agents:
- Fan-out: Send same query to multiple agents simultaneously
- Collect: Aggregate responses with timeout
- Consensus: Score/rank responses for multi-agent agreement
- Pipeline: Chain agent calls (output of one feeds next)

Uses asyncio.Semaphore for concurrency control and
asyncio.gather for parallel execution.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .client import A2AClient, A2AResponse, AgentCard, get_a2a_client
from .registry import AgentEntry, AgentRegistry, get_registry
from .task_manager import TaskManager, TaskStatus, get_task_manager

logger = logging.getLogger(__name__)

MAX_CONCURRENT = 5  # Max parallel A2A calls


@dataclass
class OrchestratorResult:
    """Result from a multi-agent orchestration."""
    responses: List[A2AResponse] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    total_latency_ms: float = 0.0
    agent_count: int = 0
    success_count: int = 0
    consensus: Optional[Dict[str, Any]] = None

    @property
    def success_rate(self) -> float:
        return self.success_count / max(self.agent_count, 1)

    def best_response(self) -> Optional[A2AResponse]:
        """Return the response with lowest latency among successful ones."""
        successful = [r for r in self.responses if r.success]
        if not successful:
            return None
        return min(successful, key=lambda r: r.latency_ms)

    def all_data(self) -> List[Dict[str, Any]]:
        """Collect all response data into a flat list."""
        return [r.data for r in self.responses if r.success and r.data]


class A2AOrchestrator:
    """
    Multi-agent orchestration engine.

    Usage:
        orch = A2AOrchestrator()

        # Fan-out to multiple agents
        result = await orch.fan_out(
            skill="alpha-scan",
            message="Find BTC signals",
            chain="monad",
            min_trust=50.0,
        )

        # Call specific agents
        result = await orch.call_agents(
            agents=[card1, card2, card3],
            skill="alpha-scan",
            message="Find BTC signals",
        )

        # Pipeline (chain calls)
        result = await orch.pipeline([
            ("research-agent", "alpha-scan", "Find signals"),
            ("analysis-agent", "analyze", "{prev_result}"),
        ])
    """

    def __init__(
        self,
        client: Optional[A2AClient] = None,
        registry: Optional[AgentRegistry] = None,
        task_manager: Optional[TaskManager] = None,
        max_concurrent: int = MAX_CONCURRENT,
    ):
        self._client = client or get_a2a_client()
        self._registry = registry or get_registry()
        self._tm = task_manager or get_task_manager()
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._call_count = 0

    async def fan_out(
        self,
        skill: str,
        message: str,
        chain: str = "monad",
        min_trust: float = 0.0,
        max_agents: int = 5,
        timeout: float = 30.0,
        params: Optional[Dict[str, Any]] = None,
    ) -> OrchestratorResult:
        """
        Discover agents with a skill and call them all in parallel.

        1. Search registry for agents with the skill
        2. Fetch their agent cards
        3. Call them all simultaneously
        4. Aggregate responses
        """
        # Discover agents
        agents = await self._registry.search(
            chain=chain,
            skills=[skill],
            has_a2a=True,
            min_trust=min_trust,
        )

        if not agents:
            logger.warning(f"No agents found with skill={skill} on {chain}")
            return OrchestratorResult()

        # Limit to max_agents
        agents = agents[:max_agents]
        logger.info(f"Fan-out: calling {len(agents)} agents with skill={skill}")

        # Fetch cards and call
        cards = []
        for agent in agents:
            try:
                card = await self._registry.get_card(agent)
                if card and card.url:
                    cards.append(card)
            except Exception as e:
                logger.debug(f"Failed to get card for {agent.name}: {e}")

        if not cards:
            return OrchestratorResult()

        return await self.call_agents(cards, skill, message, timeout=timeout, params=params)

    async def call_agents(
        self,
        agents: List[AgentCard],
        skill: str,
        message: str,
        timeout: float = 30.0,
        params: Optional[Dict[str, Any]] = None,
    ) -> OrchestratorResult:
        """
        Call multiple agents in parallel and aggregate results.
        """
        result = OrchestratorResult(agent_count=len(agents))
        start = time.monotonic()

        # Create tasks for parallel execution
        async def _call_one(card: AgentCard) -> A2AResponse:
            async with self._semaphore:
                self._call_count += 1

                # Record outbound task
                task_id = self._tm.create_task(
                    skill=skill,
                    message=message,
                    direction="outbound",
                    agent_name=card.name,
                    agent_url=card.url,
                )

                try:
                    self._tm.transition(task_id, TaskStatus.IN_PROGRESS)
                    resp = await self._client.send_message(card, skill, message, params=params)

                    if resp.success:
                        self._tm.complete(task_id, resp.data)
                    else:
                        self._tm.fail(task_id, str(resp.error))

                    return resp
                except Exception as e:
                    self._tm.fail(task_id, str(e))
                    return A2AResponse(
                        success=False,
                        error={"code": -1, "message": str(e)},
                        agent_name=card.name,
                    )

        # Execute all calls with timeout
        try:
            responses = await asyncio.wait_for(
                asyncio.gather(*[_call_one(card) for card in agents], return_exceptions=True),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            logger.warning(f"Fan-out timed out after {timeout}s")
            responses = []

        # Process results
        for resp in responses:
            if isinstance(resp, Exception):
                result.errors.append({"error": str(resp)})
            elif isinstance(resp, A2AResponse):
                result.responses.append(resp)
                if resp.success:
                    result.success_count += 1
                else:
                    result.errors.append(resp.error or {"error": "unknown"})

        result.total_latency_ms = (time.monotonic() - start) * 1000
        logger.info(
            f"Fan-out complete: {result.success_count}/{result.agent_count} succeeded "
            f"in {result.total_latency_ms:.0f}ms"
        )

        return result

    async def call_one(
        self,
        agent_url: str,
        skill: str,
        message: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> A2AResponse:
        """
        Call a single agent by URL. Fetches card automatically.
        """
        try:
            card = await self._client.fetch_agent_card(agent_url)
        except Exception as e:
            return A2AResponse(
                success=False,
                error={"code": -1, "message": f"Failed to fetch agent card: {e}"},
            )

        # Record outbound task
        task_id = self._tm.create_task(
            skill=skill,
            message=message,
            direction="outbound",
            agent_name=card.name,
            agent_url=card.url,
        )

        self._tm.transition(task_id, TaskStatus.IN_PROGRESS)
        resp = await self._client.send_message(card, skill, message, params=params)

        if resp.success:
            self._tm.complete(task_id, resp.data)
        else:
            self._tm.fail(task_id, str(resp.error))

        return resp

    async def pipeline(
        self,
        steps: List[Dict[str, Any]],
        initial_context: str = "",
    ) -> OrchestratorResult:
        """
        Execute a pipeline of agent calls where each step can use previous results.

        Each step dict:
            {
                "agent_url": "https://...",  # Or "agent_card": AgentCard
                "skill": "skill-id",
                "message": "message (use {prev} for previous result)",
            }
        """
        result = OrchestratorResult(agent_count=len(steps))
        prev_data = initial_context

        for i, step in enumerate(steps):
            agent_url = step.get("agent_url", "")
            card = step.get("agent_card")
            skill = step["skill"]
            message = step.get("message", "").replace("{prev}", str(prev_data))

            if not card and agent_url:
                try:
                    card = await self._client.fetch_agent_card(agent_url)
                except Exception as e:
                    result.errors.append({"step": i, "error": f"Card fetch failed: {e}"})
                    break

            if not card:
                result.errors.append({"step": i, "error": "No agent card available"})
                break

            resp = await self._client.send_message(card, skill, message)
            result.responses.append(resp)

            if resp.success:
                result.success_count += 1
                prev_data = str(resp.data)
            else:
                result.errors.append({"step": i, "error": resp.error})
                break  # Pipeline stops on first failure

        return result

    async def consensus(
        self,
        agents: List[AgentCard],
        skill: str,
        message: str,
        scorer: Optional[Callable] = None,
    ) -> OrchestratorResult:
        """
        Call multiple agents and score responses for consensus.

        Default scorer counts agreement on key fields.
        Custom scorer receives list of A2AResponses and returns consensus dict.
        """
        result = await self.call_agents(agents, skill, message)

        if not result.responses:
            return result

        if scorer:
            result.consensus = scorer(result.responses)
        else:
            result.consensus = self._default_consensus(result.responses)

        return result

    def _default_consensus(self, responses: List[A2AResponse]) -> Dict[str, Any]:
        """
        Default consensus: count successful responses and find common fields.
        """
        successful = [r for r in responses if r.success and r.data]
        if not successful:
            return {"agreement": 0, "agents": 0}

        # Find fields that appear in all responses
        if all(isinstance(r.data, dict) for r in successful):
            common_keys = set(successful[0].data.keys())
            for r in successful[1:]:
                common_keys &= set(r.data.keys())

            return {
                "agreement": len(successful) / len(responses),
                "agents": len(successful),
                "common_fields": list(common_keys),
                "responses_summary": [
                    {"agent": r.agent_name, "latency_ms": r.latency_ms}
                    for r in successful
                ],
            }

        return {
            "agreement": len(successful) / len(responses),
            "agents": len(successful),
        }

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_calls": self._call_count,
            "task_stats": self._tm.stats(),
        }


# Singleton
_instance: Optional[A2AOrchestrator] = None


def get_orchestrator() -> A2AOrchestrator:
    global _instance
    if _instance is None:
        _instance = A2AOrchestrator()
    return _instance
