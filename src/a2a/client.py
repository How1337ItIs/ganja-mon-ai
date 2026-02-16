"""
A2A JSON-RPC 2.0 Client
========================

Call other agents using the A2A protocol. Handles:
- Agent card fetching and caching
- JSON-RPC 2.0 message formatting
- x402 payment header injection
- Async task polling
- Response parsing and validation
- Rate limiting and retries
"""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

# Rate limiting
_last_call_times: Dict[str, float] = {}
_MIN_CALL_INTERVAL = 1.0  # 1s between calls to same agent


@dataclass
class AgentCard:
    """Parsed agent card from /.well-known/agent-card.json or A2A discovery."""
    name: str
    description: str
    url: str  # A2A endpoint URL
    version: str = "0.1.0"
    skills: List[Dict[str, Any]] = field(default_factory=list)
    capabilities: Dict[str, bool] = field(default_factory=dict)
    icon_url: Optional[str] = None
    provider: Optional[Dict[str, str]] = None
    security_schemes: Optional[Dict[str, Any]] = None
    raw: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "AgentCard":
        # Handle skills as JSON string (Meerkat agents serialize skills as string)
        skills_raw = data.get("skills", [])
        if isinstance(skills_raw, str):
            try:
                import json as _json
                skills_raw = _json.loads(skills_raw)
            except Exception:
                skills_raw = []
        return cls(
            name=data.get("name", "Unknown"),
            description=data.get("description", ""),
            url=data.get("url", ""),
            version=data.get("version", "0.1.0"),
            skills=skills_raw if isinstance(skills_raw, list) else [],
            capabilities=data.get("capabilities", {}),
            icon_url=data.get("iconUrl"),
            provider=data.get("provider"),
            security_schemes=data.get("securitySchemes"),
            raw=data,
        )

    def get_skill_ids(self) -> List[str]:
        ids = []
        for s in self.skills:
            if isinstance(s, dict):
                ids.append(s.get("id", s.get("name", "")))
            elif isinstance(s, str):
                ids.append(s)
        return ids

    def has_skill(self, skill_id: str) -> bool:
        return skill_id in self.get_skill_ids()

    def supports_streaming(self) -> bool:
        return self.capabilities.get("streaming", False)


@dataclass
class A2AResponse:
    """Parsed response from an A2A call."""
    success: bool
    task_id: Optional[str] = None
    status: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    raw: Optional[Dict[str, Any]] = None
    latency_ms: float = 0.0
    agent_name: str = ""

    @property
    def is_pending(self) -> bool:
        return self.status in ("pending", "queued", "in_progress", "requires_approval")

    @property
    def is_complete(self) -> bool:
        return self.status in ("completed", "done")

    @property
    def is_failed(self) -> bool:
        return self.status in ("failed", "error", "cancelled")


class A2AClient:
    """
    Client for calling other agents via A2A JSON-RPC 2.0 protocol.

    Usage:
        client = A2AClient()
        card = await client.fetch_agent_card("https://agent.example.com/a2a/v1")
        response = await client.send_message(card, skill="alpha-scan", message="Find BTC signals")
        if response.is_pending:
            result = await client.poll_task(card, response.task_id)
    """

    def __init__(
        self,
        timeout: float = 30.0,
        max_retries: int = 2,
        x402_payer=None,
    ):
        self._timeout = timeout
        self._max_retries = max_retries
        self._x402_payer = x402_payer
        self._card_cache: Dict[str, tuple[float, AgentCard]] = {}
        self._card_cache_ttl = 300  # 5 min

    async def fetch_agent_card(self, url: str, force: bool = False) -> AgentCard:
        """
        Fetch and parse an agent card from a URL.

        Checks cache first. Tries both the direct URL and /.well-known/agent-card.json.
        """
        if not force and url in self._card_cache:
            ts, card = self._card_cache[url]
            if time.time() - ts < self._card_cache_ttl:
                return card

        # Try the URL directly first (GET on A2A endpoint returns card)
        urls_to_try = [url]

        # Also try well-known path
        base = url.rstrip("/")
        if "/a2a/" in base:
            origin = base.split("/a2a/")[0]
            urls_to_try.append(f"{origin}/.well-known/agent-card.json")
        elif not base.endswith(".json"):
            urls_to_try.append(f"{base}/.well-known/agent-card.json")

        last_error = None
        async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
            for try_url in urls_to_try:
                try:
                    resp = await client.get(try_url, headers={"Accept": "application/json"})
                    if resp.status_code == 200:
                        data = resp.json()
                        card = AgentCard.from_dict(data)
                        if not card.url:
                            card.url = url
                        self._card_cache[url] = (time.time(), card)
                        logger.info(f"Fetched agent card: {card.name} ({len(card.skills)} skills)")
                        return card
                    else:
                        last_error = f"HTTP {resp.status_code}"
                except Exception as e:
                    last_error = e
                    continue

        raise ConnectionError(f"Failed to fetch agent card from {url}: {last_error}")

    async def send_message(
        self,
        card: AgentCard,
        skill: str,
        message: str,
        params: Optional[Dict[str, Any]] = None,
        api_key: Optional[str] = None,
    ) -> A2AResponse:
        """
        Send a message to an agent's skill via JSON-RPC 2.0.

        Args:
            card: Agent card (from fetch_agent_card)
            skill: Skill ID to invoke
            message: Natural language message
            params: Additional parameters
            api_key: Optional API key for authenticated agents
        """
        # Rate limit per agent
        await self._rate_limit(card.url)

        request_id = str(uuid.uuid4())[:8]
        # A2A 0.3 spec: message must be a Message object with role + parts
        if isinstance(message, str):
            message_obj = {
                "role": "user",
                "parts": [{"type": "text", "text": message}],
            }
        else:
            message_obj = message

        rpc_payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "message/send",
            "params": {
                "message": message_obj,
                **({"skill": skill} if skill else {}),
                **(params or {}),
            },
        }

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "GanjaMon-A2A/1.0",
        }

        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        # x402 payment header
        if self._x402_payer:
            try:
                payment_header = await self._x402_payer.create_payment_header(card.url)
                if payment_header:
                    headers["X-402-Payment"] = payment_header
            except Exception as e:
                logger.warning(f"x402 payment header failed: {e}")

        start = time.monotonic()
        last_error = None

        for attempt in range(self._max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
                    resp = await client.post(card.url, json=rpc_payload, headers=headers)

                latency = (time.monotonic() - start) * 1000

                if resp.status_code == 402:
                    # Payment required — parse PAYMENT-REQUIRED header, sign EIP-3009, retry
                    payment_header = resp.headers.get("payment-required") or resp.headers.get("x-payment-required")
                    if payment_header and self._x402_payer:
                        try:
                            payment_payload = await self._x402_payer.pay_402(payment_header)
                            if payment_payload:
                                retry_headers = {
                                    **headers,
                                    "PAYMENT-SIGNATURE": payment_payload,
                                }
                                async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as paid_client:
                                    # Try JSON-RPC format first
                                    paid_resp = await paid_client.post(card.url, json=rpc_payload, headers=retry_headers)
                                    if paid_resp.status_code == 200:
                                        body = paid_resp.json()
                                        logger.info(f"x402 paid call to {card.name} succeeded (JSON-RPC)")
                                        return self._parse_response(body, (time.monotonic() - start) * 1000, card.name)

                                    # Fallback: simple {"message": "text"} format (Meerkat-style)
                                    if paid_resp.status_code in (400, 405):
                                        msg_text = message if isinstance(message, str) else message
                                        if isinstance(msg_text, dict):
                                            parts = msg_text.get("parts", [])
                                            msg_text = parts[0].get("text", "") if parts else ""
                                        simple_body = {"message": msg_text}
                                        paid_resp2 = await paid_client.post(card.url, json=simple_body, headers=retry_headers)
                                        if paid_resp2.status_code == 200:
                                            body = paid_resp2.json()
                                            logger.info(f"x402 paid call to {card.name} succeeded (simple format)")
                                            return A2AResponse(
                                                success=True,
                                                data=body,
                                                status="completed",
                                                raw=body,
                                                latency_ms=(time.monotonic() - start) * 1000,
                                                agent_name=card.name,
                                            )
                                        logger.warning(f"x402 paid retry to {card.name}: HTTP {paid_resp2.status_code} {paid_resp2.text[:200]}")
                                    else:
                                        logger.warning(f"x402 paid retry to {card.name}: HTTP {paid_resp.status_code} {paid_resp.text[:200]}")
                        except Exception as e:
                            logger.warning(f"x402 payment to {card.name} failed: {e}")

                    return A2AResponse(
                        success=False,
                        error={
                            "code": 402,
                            "message": "Payment required (unable to pay)",
                        },
                        latency_ms=latency,
                        agent_name=card.name,
                    )

                if resp.status_code != 200:
                    last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
                    if attempt < self._max_retries:
                        await asyncio.sleep(1 * (attempt + 1))
                        continue
                    return A2AResponse(
                        success=False,
                        error={"code": resp.status_code, "message": last_error},
                        latency_ms=latency,
                        agent_name=card.name,
                    )

                body = resp.json()
                return self._parse_response(body, latency, card.name)

            except httpx.TimeoutException:
                last_error = "Request timed out"
                if attempt < self._max_retries:
                    await asyncio.sleep(1 * (attempt + 1))
                    continue
            except Exception as e:
                last_error = str(e)
                if attempt < self._max_retries:
                    await asyncio.sleep(1 * (attempt + 1))
                    continue

        return A2AResponse(
            success=False,
            error={"code": -1, "message": f"All retries failed: {last_error}"},
            latency_ms=(time.monotonic() - start) * 1000,
            agent_name=card.name,
        )

    async def get_agent_info(self, card: AgentCard) -> A2AResponse:
        """Call agent/info method."""
        await self._rate_limit(card.url)

        rpc_payload = {
            "jsonrpc": "2.0",
            "id": "info-1",
            "method": "agent/info",
            "params": {},
        }

        start = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
                resp = await client.post(
                    card.url,
                    json=rpc_payload,
                    headers={"Content-Type": "application/json", "User-Agent": "GanjaMon-A2A/1.0"},
                )
            latency = (time.monotonic() - start) * 1000
            if resp.status_code == 200:
                body = resp.json()
                return self._parse_response(body, latency, card.name)
            return A2AResponse(success=False, error={"code": resp.status_code, "message": resp.text[:200]}, latency_ms=latency, agent_name=card.name)
        except Exception as e:
            return A2AResponse(success=False, error={"code": -1, "message": str(e)}, latency_ms=(time.monotonic() - start) * 1000, agent_name=card.name)

    async def get_task(self, card: AgentCard, task_id: str) -> A2AResponse:
        """Get task status from an agent."""
        await self._rate_limit(card.url)

        rpc_payload = {
            "jsonrpc": "2.0",
            "id": f"task-{task_id[:8]}",
            "method": "tasks/get",
            "params": {"taskId": task_id},
        }

        start = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
                resp = await client.post(
                    card.url,
                    json=rpc_payload,
                    headers={"Content-Type": "application/json", "User-Agent": "GanjaMon-A2A/1.0"},
                )
            latency = (time.monotonic() - start) * 1000
            if resp.status_code == 200:
                body = resp.json()
                return self._parse_response(body, latency, card.name)
            return A2AResponse(success=False, error={"code": resp.status_code, "message": resp.text[:200]}, latency_ms=latency, agent_name=card.name)
        except Exception as e:
            return A2AResponse(success=False, error={"code": -1, "message": str(e)}, latency_ms=(time.monotonic() - start) * 1000, agent_name=card.name)

    async def cancel_task(self, card: AgentCard, task_id: str) -> A2AResponse:
        """Cancel a task on an agent."""
        rpc_payload = {
            "jsonrpc": "2.0",
            "id": f"cancel-{task_id[:8]}",
            "method": "tasks/cancel",
            "params": {"taskId": task_id},
        }

        start = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
                resp = await client.post(
                    card.url,
                    json=rpc_payload,
                    headers={"Content-Type": "application/json", "User-Agent": "GanjaMon-A2A/1.0"},
                )
            latency = (time.monotonic() - start) * 1000
            if resp.status_code == 200:
                body = resp.json()
                return self._parse_response(body, latency, card.name)
            return A2AResponse(success=False, error={"code": resp.status_code, "message": resp.text[:200]}, latency_ms=latency, agent_name=card.name)
        except Exception as e:
            return A2AResponse(success=False, error={"code": -1, "message": str(e)}, latency_ms=(time.monotonic() - start) * 1000, agent_name=card.name)

    async def poll_task(
        self,
        card: AgentCard,
        task_id: str,
        interval: float = 2.0,
        max_wait: float = 60.0,
    ) -> A2AResponse:
        """
        Poll a task until completion or timeout.

        Args:
            card: Agent card
            task_id: Task ID to poll
            interval: Seconds between polls
            max_wait: Maximum seconds to wait
        """
        start = time.monotonic()
        while (time.monotonic() - start) < max_wait:
            resp = await self.get_task(card, task_id)
            if not resp.success:
                return resp
            if resp.is_complete or resp.is_failed:
                return resp
            await asyncio.sleep(interval)

        return A2AResponse(
            success=False,
            task_id=task_id,
            status="timeout",
            error={"code": -2, "message": f"Task polling timed out after {max_wait}s"},
            agent_name=card.name,
        )

    def _parse_response(self, body: dict, latency_ms: float, agent_name: str) -> A2AResponse:
        """Parse a JSON-RPC 2.0 response into an A2AResponse."""
        if "error" in body and body["error"]:
            return A2AResponse(
                success=False,
                error=body["error"],
                raw=body,
                latency_ms=latency_ms,
                agent_name=agent_name,
            )

        result = body.get("result", {})
        if isinstance(result, dict):
            return A2AResponse(
                success=True,
                task_id=result.get("taskId"),
                status=result.get("status", "completed"),
                data=result.get("data", result.get("output", result)),
                raw=body,
                latency_ms=latency_ms,
                agent_name=agent_name,
            )

        return A2AResponse(
            success=True,
            data=result,
            status="completed",
            raw=body,
            latency_ms=latency_ms,
            agent_name=agent_name,
        )

    async def _rate_limit(self, url: str):
        """Enforce rate limiting per agent endpoint."""
        now = time.time()
        last = _last_call_times.get(url, 0)
        wait = _MIN_CALL_INTERVAL - (now - last)
        if wait > 0:
            await asyncio.sleep(wait)
        _last_call_times[url] = time.time()


# Singleton
_instance: Optional[A2AClient] = None


def get_a2a_client(x402_payer=None) -> A2AClient:
    global _instance
    if _instance is None:
        # Auto-initialize x402 payer if not provided
        if x402_payer is None:
            try:
                from .x402 import get_x402_payer
                x402_payer = get_x402_payer()
            except Exception:
                pass
        _instance = A2AClient(x402_payer=x402_payer)
    return _instance
