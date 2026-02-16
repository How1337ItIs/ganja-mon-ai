"""
A2A (Agent-to-Agent) Protocol JSON-RPC 2.0 Server
===================================================

Full-featured A2A server with:
- Real skill handlers (live sensor data, signal feeds)
- Persistent SQLite-backed task management
- x402 payment verification middleware
- Rate limiting per caller
- Full state transition history

Endpoint: POST /a2a/v1/
Agent card: GET /a2a/v1/
Task stats: GET /a2a/v1/stats
"""

import asyncio
import json
import logging
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Union

from fastapi import APIRouter, Request
from pydantic import BaseModel

from ..a2a.task_manager import TaskManager, TaskStatus, get_task_manager
from ..a2a.validator import AgentValidator, get_validator
from ..a2a.x402 import X402Verifier, get_x402_verifier
from ..a2a.skills import NEW_SKILLS, NEW_SKILL_CARDS, SkillAnalytics

logger = logging.getLogger(__name__)

# Rate limiting: max 30 requests/minute per IP
_rate_limits: Dict[str, list] = defaultdict(list)
RATE_LIMIT = 30
RATE_WINDOW = 60  # seconds


class JsonRpcRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[Union[int, str]] = None
    method: str
    params: Optional[Dict[str, Any]] = None


class RpcErrorCode:
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    SKILL_ERROR = -32000
    PAYMENT_REQUIRED = -32001
    RATE_LIMITED = -32002


def _jsonrpc_error(request_id, code: int, message: str, data=None) -> dict:
    resp = {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}
    if data:
        resp["error"]["data"] = data
    return resp


def _jsonrpc_ok(request_id, result) -> dict:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


# ---------------------------------------------------------------------------
# Real skill handlers — pull live data from the running agent
# ---------------------------------------------------------------------------

def _read_json(path: str, default=None):
    """Safely read a JSON data file."""
    try:
        p = Path(path)
        if p.exists():
            return json.loads(p.read_text())
    except Exception:
        pass
    return default


def handle_alpha_scan(message: str, params: Dict[str, Any], app_state=None) -> Dict[str, Any]:
    """
    Alpha scan — returns real signal data from the trading agent's signal feed.
    Falls back to latest cached data files.
    """
    # Try live signal data
    signals = _read_json("data/signal_feed.json", [])
    if not signals:
        signals = _read_json("agents/ganjamon/data/signal_feed.json", [])

    # Try latest validated signals
    if not signals:
        validated = _read_json("agents/ganjamon/data/validated_signals.json", [])
        if validated:
            signals = validated[:10]

    # Try consciousness data for trading status
    consciousness = _read_json("agents/ganjamon/data/consciousness.json", {})

    return {
        "skill": "alpha-scan",
        "summary": f"{len(signals)} signals in feed" if signals else "Signal feed initializing",
        "signals": signals[:10] if signals else [],
        "trading_status": {
            "state": consciousness.get("state", "unknown"),
            "dominant_domain": consciousness.get("dominant_domain", ""),
            "signal_count": consciousness.get("total_signals", 0),
        } if consciousness else {},
        "sources": ["dexscreener", "gmgn", "hyperliquid", "polymarket", "nadfun", "jupiter", "news"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def handle_cultivation_status(message: str, params: Dict[str, Any], app_state=None) -> Dict[str, Any]:
    """
    Cultivation status — returns real sensor data from the grow agent.
    """
    # Try live sensor data
    sensors = {}

    # Read from latest sensor cache
    latest = _read_json("data/latest_sensors.json", {})
    if latest:
        sensors = {
            "temperature": latest.get("temperature"),
            "humidity": latest.get("humidity"),
            "vpd": latest.get("vpd"),
            "co2": latest.get("co2"),
            "soil_moisture": latest.get("soil_moisture"),
        }

    # Try grow stage
    stage_data = _read_json("data/grow_stage.json", {})

    # Try latest AI decision
    decisions = _read_json("data/ai_decisions.json", [])
    last_decision = decisions[-1] if decisions else {}

    # Read health report
    health = _read_json("data/health_report.json", {})

    return {
        "skill": "cultivation-status",
        "strain": "Granddaddy Purple Runtz (GDP x Runtz)",
        "stage": stage_data.get("stage", "vegetative"),
        "day": stage_data.get("day"),
        "sensors": sensors,
        "health": health.get("overall_severity", "unknown"),
        "last_decision": {
            "action": last_decision.get("action", ""),
            "reasoning": last_decision.get("reasoning", ""),
            "timestamp": last_decision.get("timestamp", ""),
        } if last_decision else {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def handle_signal_feed(message: str, params: Dict[str, Any], app_state=None) -> Dict[str, Any]:
    """
    Signal feed — returns the latest scored signals with tier classification.
    """
    signals = _read_json("data/signal_feed.json", [])
    if not signals:
        signals = _read_json("agents/ganjamon/data/signal_feed.json", [])

    # Filter by tier if requested
    tier = params.get("tier")
    if tier and signals:
        signals = [s for s in signals if s.get("tier") == tier]

    # Filter by minimum confidence
    min_confidence = params.get("min_confidence", 0)
    if min_confidence and signals:
        signals = [s for s in signals if s.get("confidence", 0) >= float(min_confidence)]

    return {
        "skill": "signal-feed",
        "count": len(signals),
        "signals": signals[:20],
        "scoring": {
            "tier1": ">=0.85 confluence",
            "tier2": ">=0.65 confluence",
            "tier3": ">=0.45 confluence",
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def handle_trade_execution(message: str, params: Dict[str, Any], app_state=None) -> Dict[str, Any]:
    """
    Trade execution — queues a trade intent for human approval.
    Uses persistent task manager.
    """
    tm = get_task_manager()
    task_id = tm.create_task(
        skill="trade-execution",
        message=message,
        params=params,
        direction="inbound",
        agent_name=params.get("agent_name", "unknown"),
        agent_url=params.get("agent_url", ""),
    )

    # Write intent file for the trading agent to pick up
    intent_dir = Path("data/trade_intents")
    intent_dir.mkdir(parents=True, exist_ok=True)
    intent_file = intent_dir / f"{task_id}.json"
    intent_file.write_text(json.dumps({
        "task_id": task_id,
        "message": message,
        "params": params,
        "status": "pending_approval",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }, indent=2))

    return {
        "skill": "trade-execution",
        "taskId": task_id,
        "status": "pending_approval",
        "message": "Trade intent queued for human approval via Telegram. High-risk trades (>$500) require explicit confirmation.",
        "approval_channel": "Telegram @MonGardenBot",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def handle_agent_validate(message: str, params: Dict[str, Any], app_state=None) -> Dict[str, Any]:
    """
    Agent validate -- validate another agent's A2A/MCP/x402/infra/registry endpoints.

    Follows the SnowRail Sentinel pattern. Produces a composite bootstrap score (0-100)
    across five protocol layers: A2A, MCP, x402, infrastructure, and 8004scan registration.

    Params:
        agent_url (str, required): The base URL of the agent to validate
        agent_id (int, optional): 8004scan token ID for registry check
        chain (str, optional): Chain to check registry on (default: monad)
    """
    agent_url = params.get("agent_url") or params.get("url") or message.strip()
    if not agent_url:
        return {
            "skill": "agent-validate",
            "error": "Missing 'agent_url' param. Provide the URL of the agent to validate.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    agent_id = params.get("agent_id")
    if agent_id is not None:
        try:
            agent_id = int(agent_id)
        except (ValueError, TypeError):
            agent_id = None

    chain = params.get("chain", "monad")

    validator = get_validator()
    report = await validator.validate_agent(agent_url, agent_id=agent_id, chain=chain)

    return {
        "skill": "agent-validate",
        **report.to_dict(),
    }


# Skill registry
SKILLS = {
    "alpha-scan": handle_alpha_scan,
    "cultivation-status": handle_cultivation_status,
    "signal-feed": handle_signal_feed,
    "trade-execution": handle_trade_execution,
    "agent-validate": handle_agent_validate,
    **NEW_SKILLS,  # 15 new skills from src/a2a/skills.py
}

AGENT_CARD = {
    "name": "GanjaMon AI",
    "version": "3.1.0",
    "description": "Autonomous ERC-8004 AI agent on Monad with 23 A2A skills. Hunts alpha across 9 data sources. Manages a real cannabis grow tent with IoT sensors. Features grow oracle, VPD calculator, plant vision, plant timelapse, on-chain grow log, cross-domain grow-alpha signals, Rasta translation, reputation oracle, strain library, and more. Full A2A two-way protocol with persistent task tracking, x402 payments, and multi-agent orchestration.",
    "protocolVersion": "0.3.0",
    "url": "https://grokandmon.com/a2a/v1",
    "additionalInterfaces": [
        {"url": "https://grokandmon.com/a2a/v1", "transport": "HTTP+JSON"},
        {"url": "https://grokandmon.com/mcp/v1", "transport": "MCP"},
        {"url": "https://grokandmon.com/a2a/v1/acp/grow", "transport": "REST"},
        {"url": "https://grokandmon.com/a2a/v1/acp/signals", "transport": "REST"},
        {"url": "https://grokandmon.com/a2a/v1/acp/oracle", "transport": "REST"},
    ],
    "capabilities": {
        "streaming": False,
        "pushNotifications": False,
        "stateTransitionHistory": True,
        "x402Payments": True,
    },
    "skills": [
        {
            "id": "alpha-scan",
            "name": "Alpha Scan",
            "description": "Aggregate signals from 9 data sources (DexScreener, GMGN, Hyperliquid, Polymarket, nad.fun, Jupiter, news, CoinGecko, Dex traders). Returns scored opportunities.",
            "tags": ["alpha", "research", "monitoring", "signals"],
        },
        {
            "id": "cultivation-status",
            "name": "Cultivation Status",
            "description": "Live sensor data (temp, humidity, CO2, VPD, soil moisture) from IoT-equipped grow tent. AI decision history included.",
            "tags": ["cultivation", "monitoring", "iot", "sensors"],
        },
        {
            "id": "signal-feed",
            "name": "Signal Feed",
            "description": "Real-time alpha signals with confluence scoring. Filter by tier (1/2/3) or minimum confidence.",
            "tags": ["signals", "alpha", "feed", "real-time"],
        },
        {
            "id": "trade-execution",
            "name": "Trade Execution (Approval)",
            "description": "Queue trade intents for operator approval via Telegram. No auto-execution.",
            "tags": ["trading", "approval", "safety"],
        },
        {
            "id": "agent-validate",
            "name": "Agent Validate",
            "description": "Validate another agent's A2A/MCP/x402 endpoints. Returns a 0-100 bootstrap score across five protocol layers: A2A discovery, MCP tools, x402 payments, infrastructure health, and 8004scan registration.",
            "tags": ["validation", "sentinel", "a2a", "mcp", "x402", "monitoring"],
        },
        *NEW_SKILL_CARDS,  # 15 new skills
    ],
    "chains": ["monad", "base", "ethereum"],
    "x402": {
        "payTo": "eip155:10143:0x734B0e337bfa7d4764f4B806B4245Dd312DdF134",
        "currency": "USDC",
        "network": "monad",
        "chainId": 10143,
        "priceUSD": "0.001",
        "pricingUrl": "https://grokandmon.com/.well-known/x402-pricing.json",
        "freeTier": {"requestsPerDay": 100},
    },
    "contact": {
        "website": "https://grokandmon.com",
        "twitter": "@ganjamonai",
        "telegram": "https://t.me/ganjamonai",
    },
}


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/a2a/v1", tags=["a2a"])


def _check_rate_limit(client_ip: str) -> bool:
    """Returns True if request is allowed, False if rate limited."""
    now = time.time()
    timestamps = _rate_limits[client_ip]
    # Remove old entries
    _rate_limits[client_ip] = [t for t in timestamps if now - t < RATE_WINDOW]
    if len(_rate_limits[client_ip]) >= RATE_LIMIT:
        return False
    _rate_limits[client_ip].append(now)
    return True


@router.post("/")
async def handle_jsonrpc(request: Request) -> dict:
    """
    Handle JSON-RPC 2.0 A2A requests.

    Methods: agent/info, message/send, tasks/get, tasks/cancel
    """
    client_ip = request.client.host if request.client else "unknown"

    # Rate limiting
    if not _check_rate_limit(client_ip):
        return _jsonrpc_error(None, RpcErrorCode.RATE_LIMITED, "Rate limited: max 30 requests/minute")

    # x402 payment verification
    verifier = get_x402_verifier()
    payment_header = (
        request.headers.get("X-402-Payment")
        or request.headers.get("X-Payment")
        or request.headers.get("x-402-payment")
        or request.headers.get("x-payment")
    )
    valid, reason = verifier.verify_header(payment_header)
    if not valid:
        return _jsonrpc_error(
            None,
            RpcErrorCode.PAYMENT_REQUIRED,
            "Payment required",
            data=verifier.get_requirements(),
        )

    # Parse body
    try:
        body = await request.json()
    except Exception:
        return _jsonrpc_error(None, RpcErrorCode.PARSE_ERROR, "Invalid JSON")

    try:
        rpc = JsonRpcRequest(**body)
    except Exception as e:
        return _jsonrpc_error(body.get("id"), RpcErrorCode.INVALID_REQUEST, f"Invalid request: {e}")

    # Route methods
    if rpc.method == "agent/info":
        return _jsonrpc_ok(rpc.id, AGENT_CARD)

    if rpc.method == "message/send":
        return await _handle_message_send(rpc, request)

    if rpc.method == "tasks/get":
        return _handle_tasks_get(rpc)

    if rpc.method == "tasks/cancel":
        return _handle_tasks_cancel(rpc)

    return _jsonrpc_error(rpc.id, RpcErrorCode.METHOD_NOT_FOUND, f"Method not found: {rpc.method}")


async def _handle_message_send(rpc: JsonRpcRequest, request: Request) -> dict:
    """Handle message/send — route to skill handlers with persistent tasks."""
    params = rpc.params or {}
    skill = params.get("skill")
    message = params.get("message", "")

    if not skill:
        return _jsonrpc_error(rpc.id, RpcErrorCode.INVALID_PARAMS, "Missing 'skill' in params")

    if skill not in SKILLS:
        return _jsonrpc_error(
            rpc.id,
            RpcErrorCode.INVALID_PARAMS,
            f"Unknown skill: {skill}. Available: {list(SKILLS.keys())}",
        )

    # Execute skill handler (supports both sync and async handlers)
    analytics = SkillAnalytics.get()
    caller_ip = request.client.host if request.client else "unknown"
    skill_start = time.time()
    try:
        app_state = getattr(request, "app", None)
        handler = SKILLS[skill]
        result = handler(message, params, app_state=app_state)
        # Await if handler returned a coroutine (async handler)
        if asyncio.iscoroutine(result):
            result = await result
        skill_latency = (time.time() - skill_start) * 1000
        analytics.record_call(skill, skill_latency, True, caller_ip)
    except Exception as e:
        skill_latency = (time.time() - skill_start) * 1000
        analytics.record_call(skill, skill_latency, False, caller_ip)
        logger.error(f"Skill {skill} error: {e}", exc_info=True)
        return _jsonrpc_error(rpc.id, RpcErrorCode.SKILL_ERROR, f"Skill error: {e}")

    # Trade execution already creates its own task
    if skill == "trade-execution":
        return _jsonrpc_ok(rpc.id, result)

    # For other skills, create a completed task
    tm = get_task_manager()
    task_id = tm.create_task(
        skill=skill,
        message=message,
        params=params,
        direction="inbound",
        agent_name=params.get("agent_name", ""),
    )
    tm.complete(task_id, result)

    return _jsonrpc_ok(rpc.id, {
        "taskId": task_id,
        "status": "completed",
        "data": result,
    })


def _handle_tasks_get(rpc: JsonRpcRequest) -> dict:
    """Handle tasks/get — read from persistent task manager."""
    params = rpc.params or {}
    task_id = params.get("taskId")
    if not task_id:
        return _jsonrpc_error(rpc.id, RpcErrorCode.INVALID_PARAMS, "Missing 'taskId'")

    tm = get_task_manager()
    task = tm.get_task(task_id)
    if not task:
        return _jsonrpc_error(rpc.id, RpcErrorCode.INVALID_PARAMS, f"Task not found: {task_id}")

    # Include audit log if requested
    if params.get("includeLog"):
        task["log"] = tm.get_task_log(task_id)

    return _jsonrpc_ok(rpc.id, task)


def _handle_tasks_cancel(rpc: JsonRpcRequest) -> dict:
    """Handle tasks/cancel — cancel via persistent task manager."""
    params = rpc.params or {}
    task_id = params.get("taskId")
    if not task_id:
        return _jsonrpc_error(rpc.id, RpcErrorCode.INVALID_PARAMS, "Missing 'taskId'")

    tm = get_task_manager()
    task = tm.get_task(task_id)
    if not task:
        return _jsonrpc_error(rpc.id, RpcErrorCode.INVALID_PARAMS, f"Task not found: {task_id}")

    if task["status"] in ("completed", "cancelled"):
        return _jsonrpc_error(rpc.id, RpcErrorCode.INVALID_PARAMS, f"Cannot cancel {task['status']} task")

    tm.transition(task_id, TaskStatus.CANCELLED, "Cancelled via A2A")

    return _jsonrpc_ok(rpc.id, {"taskId": task_id, "status": "cancelled"})


# ---------------------------------------------------------------------------
# ACP (Agent Commerce Protocol) REST endpoints
# ---------------------------------------------------------------------------

_ACP_METADATA = {
    "agent": "GanjaMon AI",
    "chain": "monad",
    "version": "2.0.0",
    "erc8004_agent_id": 4,
    "url": "https://grokandmon.com/a2a/v1",
}


@router.get("/acp/grow")
async def acp_grow() -> dict:
    """
    ACP: Live cultivation data.

    Returns sensor readings, grow stage, recent AI decisions, and health status.
    Structured for agent-to-agent consumption following ERC-8004 data format.
    """
    # Sensor data
    sensors_raw = _read_json("data/latest_sensors.json", {})
    sensors = {
        "temperature": sensors_raw.get("temperature"),
        "humidity": sensors_raw.get("humidity"),
        "vpd": sensors_raw.get("vpd"),
        "co2": sensors_raw.get("co2"),
        "soil_moisture": sensors_raw.get("soil_moisture"),
    }

    # Grow stage
    stage_data = _read_json("data/grow_stage.json", {})

    # Last 5 AI decisions
    all_decisions = _read_json("data/ai_decisions.json", [])
    recent_decisions = all_decisions[-5:] if all_decisions else []

    # Health report
    health = _read_json("data/health_report.json", {})

    return {
        "skillId": "cultivation-status",
        "protocol": "ERC-8004",
        "data": {
            "strain": "Granddaddy Purple Runtz (GDP x Runtz)",
            "stage": stage_data.get("stage", "vegetative"),
            "day": stage_data.get("day"),
            "sensors": sensors,
            "health": health.get("overall_severity", "unknown"),
            "health_checks": health.get("checks", {}),
            "recent_decisions": [
                {
                    "action": d.get("action", ""),
                    "reasoning": d.get("reasoning", ""),
                    "timestamp": d.get("timestamp", ""),
                }
                for d in recent_decisions
            ],
        },
        "metadata": {
            **_ACP_METADATA,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        "pricing": "free",
    }


@router.get("/acp/signals")
async def acp_signals(
    tier: Optional[int] = None,
    min_confidence: Optional[float] = None,
    limit: int = 10,
) -> dict:
    """
    ACP: Trading signal data.

    Returns scored signals from 9 data sources with optional filtering.
    Query params: ?tier=1&min_confidence=0.7&limit=10
    """
    # Load signals
    signals = _read_json("data/signal_feed.json", [])
    if not signals:
        signals = _read_json("agents/ganjamon/data/signal_feed.json", [])

    # Trading consciousness
    consciousness = _read_json("agents/ganjamon/data/consciousness.json", {})

    # Apply filters
    if tier is not None and signals:
        signals = [s for s in signals if s.get("tier") == tier]

    if min_confidence is not None and signals:
        signals = [s for s in signals if s.get("confidence", 0) >= min_confidence]

    # Apply limit
    limit = max(1, min(limit, 50))
    signals = signals[:limit]

    return {
        "skillId": "signal-feed",
        "protocol": "ERC-8004",
        "data": {
            "count": len(signals),
            "signals": signals,
            "filters_applied": {
                "tier": tier,
                "min_confidence": min_confidence,
                "limit": limit,
            },
            "trading_state": {
                "state": consciousness.get("state", "unknown"),
                "dominant_domain": consciousness.get("dominant_domain", ""),
                "total_signals_seen": consciousness.get("total_signals", 0),
                "pnl_pct": consciousness.get("pnl_pct"),
            } if consciousness else {},
            "scoring": {
                "tier1": ">=0.85 confluence",
                "tier2": ">=0.65 confluence",
                "tier3": ">=0.45 confluence",
            },
            "sources": [
                "dexscreener", "gmgn", "hyperliquid", "polymarket",
                "nadfun", "jupiter", "news", "coingecko", "dex_traders",
            ],
        },
        "metadata": {
            **_ACP_METADATA,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        "pricing": "free",
    }


@router.get("/acp/oracle")
async def acp_oracle() -> dict:
    """
    ACP: Minimal oracle endpoint for on-chain consumption.

    Returns the smallest possible response with just key metrics.
    Designed for cost-efficient consumption by smart contracts and other agents.
    """
    # Sensor data
    sensors = _read_json("data/latest_sensors.json", {})

    # Grow stage
    stage_data = _read_json("data/grow_stage.json", {})

    # Health
    health = _read_json("data/health_report.json", {})

    # Signal summary
    signals = _read_json("data/signal_feed.json", [])
    if not signals:
        signals = _read_json("agents/ganjamon/data/signal_feed.json", [])

    top_confidence = 0.0
    if signals:
        top_confidence = max((s.get("confidence", 0) for s in signals), default=0.0)

    return {
        "temp": sensors.get("temperature", 0),
        "humidity": sensors.get("humidity", 0),
        "vpd": sensors.get("vpd", 0),
        "co2": sensors.get("co2", 0),
        "stage": stage_data.get("stage", "unknown"),
        "health": health.get("overall_severity", "unknown"),
        "signals_count": len(signals),
        "top_signal_confidence": round(top_confidence, 4),
        "timestamp": int(datetime.now(timezone.utc).timestamp()),
    }


@router.get("/")
async def get_agent_card() -> dict:
    """Return agent card for discovery and liveness checks."""
    return AGENT_CARD


@router.get("/stats")
async def get_a2a_stats() -> dict:
    """Return A2A statistics — task counts, payment receipts, rate limits, skill analytics."""
    tm = get_task_manager()
    verifier = get_x402_verifier()
    analytics = SkillAnalytics.get()
    return {
        "tasks": tm.stats(),
        "payments": {
            "total_received_usd": verifier.total_received(),
            "recent_receipts": verifier.get_receipts(10),
        },
        "agent": {
            "name": AGENT_CARD["name"],
            "version": AGENT_CARD["version"],
            "skills": [s["id"] for s in AGENT_CARD["skills"]],
        },
        "skill_analytics": analytics.get_stats(),
    }


@router.get("/skill-stats")
async def get_skill_stats() -> dict:
    """
    Detailed skill analytics: calls per skill, avg latency, success rate, top callers.
    Useful for monitoring which skills are popular and performant.
    """
    analytics = SkillAnalytics.get()
    stats = analytics.get_stats()
    stats["available_skills"] = list(SKILLS.keys())
    stats["total_skills"] = len(SKILLS)
    return stats
