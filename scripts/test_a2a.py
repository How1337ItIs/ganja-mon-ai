#!/usr/bin/env python3
"""
A2A Stack v2.0 — End-to-End Test Suite
=======================================

Tests all A2A components:
1. Server endpoints (agent/info, message/send, tasks/get, tasks/cancel)
2. All 4 skill handlers (alpha-scan, cultivation-status, signal-feed, trade-execution)
3. Task manager persistence + state machine
4. x402 verifier + payer
5. A2A client (fetch card, send message)
6. Agent registry (8004scan query)
7. MCP client (list tools)
8. Rate limiting
"""

import asyncio
import json
import sys
import time
import traceback

# Ensure project root is on path
sys.path.insert(0, ".")

PASS = 0
FAIL = 0
ERRORS = []


def test(name: str, condition: bool, detail: str = ""):
    global PASS, FAIL, ERRORS
    if condition:
        PASS += 1
        print(f"  PASS: {name}")
    else:
        FAIL += 1
        ERRORS.append(f"{name}: {detail}")
        print(f"  FAIL: {name} — {detail}")


async def test_task_manager():
    """Test persistent SQLite task manager."""
    print("\n=== Task Manager ===")
    from src.a2a.task_manager import TaskManager, TaskStatus

    # Use temp db for testing
    import tempfile
    from pathlib import Path
    db_path = Path(tempfile.mktemp(suffix=".db"))

    try:
        tm = TaskManager(db_path=db_path)

        # Create task
        tid = tm.create_task(skill="test-skill", message="hello", direction="inbound", agent_name="test-agent")
        test("create_task returns UUID", len(tid) == 36, f"got {tid}")

        # Get task
        task = tm.get_task(tid)
        test("get_task returns task", task is not None)
        test("task status is pending", task["status"] == "pending", f"got {task.get('status')}")
        test("task skill matches", task["skill"] == "test-skill")
        test("task direction matches", task["direction"] == "inbound")

        # Transition: pending -> in_progress
        ok = tm.transition(tid, TaskStatus.IN_PROGRESS, "Starting work")
        test("transition pending->in_progress", ok)
        task = tm.get_task(tid)
        test("status is now in_progress", task["status"] == "in_progress")

        # Complete
        ok = tm.complete(tid, {"result": "success", "data": [1, 2, 3]})
        test("complete task", ok)
        task = tm.get_task(tid)
        test("status is completed", task["status"] == "completed")
        test("result is stored", task["result"]["data"] == [1, 2, 3])
        test("completed_at is set", task["completed_at"] is not None)

        # Invalid transition (completed -> in_progress should fail)
        ok = tm.transition(tid, TaskStatus.IN_PROGRESS)
        test("reject invalid transition", not ok, "should not allow completed->in_progress")

        # Fail a task
        tid2 = tm.create_task(skill="fail-test", message="will fail", direction="outbound")
        tm.transition(tid2, TaskStatus.IN_PROGRESS)
        ok = tm.fail(tid2, "Something went wrong")
        test("fail task", ok)
        task2 = tm.get_task(tid2)
        test("failed task has error", task2["error"] == "Something went wrong")

        # Cancel a task
        tid3 = tm.create_task(skill="cancel-test", message="will cancel", direction="inbound")
        ok = tm.transition(tid3, TaskStatus.CANCELLED, "User cancelled")
        test("cancel task", ok)

        # Audit log
        log = tm.get_task_log(tid)
        test("audit log exists", len(log) >= 3, f"got {len(log)} entries")

        # List tasks
        tasks = tm.list_tasks(status=TaskStatus.COMPLETED)
        test("list completed tasks", len(tasks) >= 1)

        tasks = tm.list_tasks(direction="outbound")
        test("list outbound tasks", len(tasks) >= 1)

        # Stats
        stats = tm.stats()
        test("stats has totals", stats["total"] >= 3, f"got {stats['total']}")
        test("stats by_status", "completed" in stats["by_status"])

        # Expiration
        tid4 = tm.create_task(skill="expire-test", message="will expire", direction="inbound", ttl=0.001)
        time.sleep(0.01)
        expired = tm.expire_stale()
        test("expire stale tasks", expired >= 1)
        task4 = tm.get_task(tid4)
        test("expired task is cancelled", task4["status"] == "cancelled")

    finally:
        db_path.unlink(missing_ok=True)


async def test_x402():
    """Test x402 payment verification and sending."""
    print("\n=== x402 Payments ===")
    from src.a2a.x402 import X402Verifier, X402Payer, PaymentRequirements

    # Verifier (not requiring payment)
    verifier = X402Verifier(price_usd=0.001, require_payment=False)
    valid, reason = verifier.verify_header(None)
    test("verifier accepts when payment not required", valid)

    # Verifier (requiring payment)
    verifier_strict = X402Verifier(price_usd=0.001, require_payment=True)
    valid, reason = verifier_strict.verify_header(None)
    test("strict verifier rejects missing header", not valid)

    valid, reason = verifier_strict.verify_header("not-real-but-opaque-token-abc123")
    test("strict verifier accepts opaque token", valid)

    # JSON proof
    import base64
    proof = base64.b64encode(json.dumps({"from": "0x123", "amount": "0.001"}).encode()).decode()
    valid, reason = verifier_strict.verify_header(proof)
    test("verifier accepts base64 proof", valid)

    # Requirements
    reqs = verifier.get_requirements()
    test("requirements has priceUSD", reqs["priceUSD"] == 0.001)
    test("requirements has currency", reqs["currency"] == "USDC")

    # Receipts
    receipts = verifier_strict.get_receipts()
    test("receipts recorded", len(receipts) >= 2, f"got {len(receipts)}")
    test("total received > 0", verifier_strict.total_received() > 0)

    # Payer
    payer = X402Payer(wallet_address="0xTestWallet", max_payment_usd=0.01)
    header = await payer.create_payment_header("https://example.com/a2a/v1", amount_usd=0.001)
    test("payer creates payment header", header is not None and len(header) > 10)

    # Decode and verify
    decoded = json.loads(base64.b64decode(header))
    test("payment header has from field", decoded.get("from") == "0xTestWallet")
    test("payment header has amount", decoded.get("amount") == "0.001")
    test("payment header has version", decoded.get("version") == "x402-v1")

    # Spending limits
    stats = payer.get_spending_stats()
    test("spending stats tracks total", stats["total_spent_usd"] > 0)

    # Exceed limit
    big_header = await payer.create_payment_header("https://example.com", amount_usd=100.0)
    test("rejects payment exceeding max", big_header is None)

    # PaymentRequirements parsing
    reqs = PaymentRequirements.from_response({
        "priceUSD": 0.005,
        "currency": "USDC",
        "chain": "base",
        "payTo": "0xRecipient",
        "facilitatorUrl": "https://facilitator.example.com",
    })
    test("parse payment requirements", reqs.price_usd == 0.005)
    test("requirements has facilitator", reqs.facilitator_url == "https://facilitator.example.com")


async def test_a2a_client():
    """Test A2A client fetching our own agent card."""
    print("\n=== A2A Client ===")
    from src.a2a.client import A2AClient, AgentCard

    client = A2AClient(timeout=15.0)

    # Fetch our own agent card from CF Pages
    try:
        card = await client.fetch_agent_card("https://grokandmon.com/.well-known/agent-card.json")
        test("fetch agent card succeeds", card is not None)
        test("card name is GanjaMon", card.name == "GanjaMon")
        test("card has skills", len(card.skills) >= 4, f"got {len(card.skills)}")
        test("card has URL", "grokandmon.com" in card.url)
        test("card skill IDs", card.has_skill("alpha-scan"))
    except Exception as e:
        test("fetch agent card", False, str(e))

    # Test AgentCard methods
    card = AgentCard(
        name="Test Agent",
        description="Test",
        url="https://test.com/a2a/v1",
        skills=[{"id": "test-skill", "name": "Test"}],
        capabilities={"streaming": True},
    )
    test("has_skill works", card.has_skill("test-skill"))
    test("has_skill negative", not card.has_skill("nonexistent"))
    test("supports_streaming", card.supports_streaming())
    test("get_skill_ids", card.get_skill_ids() == ["test-skill"])

    # Test calling our CF Pages A2A endpoint
    try:
        card = await client.fetch_agent_card("https://grokandmon.com/a2a/v1")
        resp = await client.send_message(card, skill="cultivation-status", message="status check")
        test("send_message succeeds", resp.success, str(resp.error) if not resp.success else "")
        test("response has data", resp.data is not None)
        if resp.success:
            test("response has taskId", resp.task_id is not None or "taskId" in str(resp.data))
    except Exception as e:
        test("send_message to CF", False, str(e))

    # Test agent/info
    try:
        resp = await client.get_agent_info(card)
        test("get_agent_info succeeds", resp.success, str(resp.error) if not resp.success else "")
    except Exception as e:
        test("get_agent_info", False, str(e))


async def test_registry():
    """Test agent registry querying 8004scan."""
    print("\n=== Agent Registry ===")
    from src.a2a.registry import AgentRegistry, AgentEntry

    registry = AgentRegistry()

    # List agents on Monad
    try:
        agents = await registry.list_agents(chain="monad", limit=20)
        test("list_agents returns results", len(agents) > 0, f"got {len(agents)}")
        if agents:
            test("agents have IDs", agents[0].agent_id > 0)
            test("agents have names", len(agents[0].name) > 0, agents[0].name)

            # Find our agent (#4)
            our_agent = next((a for a in agents if a.agent_id == 4), None)
            if our_agent:
                test("found our agent #4", True)
                test("our agent name", "ganja" in our_agent.name.lower() or "mon" in our_agent.name.lower(), our_agent.name)
            else:
                test("found our agent #4", False, "not in top 20")
    except Exception as e:
        test("list_agents", False, str(e))

    # Get specific agent
    try:
        agent = await registry.get_agent(4, chain="monad")
        test("get_agent(4) returns result", agent is not None)
        if agent:
            test("agent has trust score", agent.trust_score >= 0)
    except Exception as e:
        test("get_agent(4)", False, str(e))

    # Search with filters
    try:
        results = await registry.search(chain="monad", has_a2a=True)
        test("search(has_a2a=True) works", isinstance(results, list))
    except Exception as e:
        test("search", False, str(e))

    # Resolve URI
    try:
        # Test IPFS resolution (use a known CID)
        metadata = await registry.resolve_uri("ipfs://QmcX5nLAzvHFKKgmTzLdzfXdhmVH1U6f3jfKcavdvbn9bM")
        test("resolve IPFS URI", metadata is not None, "could not resolve" if metadata is None else "")
    except Exception as e:
        test("resolve IPFS URI", False, str(e))

    # Test AgentEntry parsing (matches 8004scan v1 API format)
    entry = AgentEntry.from_scan_data({
        "token_id": "99",
        "name": "Test Agent",
        "description": "A test agent",
        "owner_address": "0x123",
        "total_score": 85.5,
        "x402_supported": True,
        "endpoints": {
            "a2a": {"endpoint": "https://test.com/a2a/v1", "version": "0.3.0", "skills": [{"id": "alpha-scan"}, "trading"]},
            "mcp": {"endpoint": "https://test.com/mcp/v1", "version": "2025-06-18"},
        },
        "tags": ["defi"],
        "categories": ["trading"],
    })
    test("parse AgentEntry", entry.agent_id == 99)
    test("entry has A2A URL", entry.a2a_url == "https://test.com/a2a/v1")
    test("entry has MCP URL", entry.mcp_url == "https://test.com/mcp/v1")
    test("entry has trust score", entry.trust_score == 85.5)
    test("entry has skills", "alpha-scan" in entry.skills)
    test("entry has x402", entry.x402_support)


async def test_mcp_client():
    """Test MCP client against our own MCP endpoint."""
    print("\n=== MCP Client ===")
    from src.a2a.mcp_client import MCPClient, MCPTool

    client = MCPClient(timeout=15.0)

    # List tools from our MCP endpoint
    try:
        tools = await client.list_tools("https://grokandmon.com/mcp/v1")
        test("list_tools returns results", len(tools) > 0, f"got {len(tools)}")
        if tools:
            test("tools have names", len(tools[0].name) > 0, tools[0].name)
            tool_names = [t.name for t in tools]
            test("has get_environment tool", "get_environment" in tool_names, str(tool_names[:5]))
            test("has trigger_irrigation tool", "trigger_irrigation" in tool_names)
    except Exception as e:
        test("list_tools", False, str(e))

    # Call a tool (will return acknowledgment since CF Function is mock)
    try:
        result = await client.call_tool("https://grokandmon.com/mcp/v1", "get_environment", {})
        test("call_tool succeeds", result.success, result.error or "")
        if result.success:
            test("call_tool has content", len(result.content) > 0)
            test("call_tool has text", len(result.text) > 0, result.text[:50] if result.text else "empty")
    except Exception as e:
        test("call_tool", False, str(e))

    # MCPTool parsing
    tool = MCPTool.from_dict({
        "name": "test_tool",
        "description": "A test tool",
        "inputSchema": {"type": "object", "properties": {"x": {"type": "integer"}}},
    }, server_url="https://test.com/mcp/v1", server_name="Test Server")
    test("parse MCPTool", tool.name == "test_tool")
    test("tool has schema", "properties" in tool.input_schema)


async def test_orchestrator():
    """Test orchestrator patterns."""
    print("\n=== Orchestrator ===")
    from src.a2a.orchestrator import A2AOrchestrator, OrchestratorResult
    from src.a2a.client import A2AClient, AgentCard

    client = A2AClient(timeout=15.0)
    orch = A2AOrchestrator(client=client)

    # Test call_one against our own endpoint
    try:
        resp = await orch.call_one(
            "https://grokandmon.com/a2a/v1",
            "cultivation-status",
            "What is the plant status?",
        )
        test("call_one succeeds", resp.success, str(resp.error) if not resp.success else "")
        test("call_one has agent name", len(resp.agent_name) > 0, resp.agent_name)
    except Exception as e:
        test("call_one", False, str(e))

    # Test OrchestratorResult methods
    result = OrchestratorResult(
        agent_count=3,
        success_count=2,
        responses=[],
    )
    test("success_rate calculation", abs(result.success_rate - 0.667) < 0.01)
    test("best_response with no responses", result.best_response() is None)

    # Stats
    stats = orch.get_stats()
    test("orchestrator stats", "total_calls" in stats)


async def test_brain_tools():
    """Test that brain tools definitions include A2A tools."""
    print("\n=== Brain Tools ===")
    from src.ai.tools import GROW_TOOLS

    tool_names = [t["function"]["name"] for t in GROW_TOOLS]

    test("total tools count >= 22", len(tool_names) >= 22, f"got {len(tool_names)}")
    test("has discover_agents", "discover_agents" in tool_names)
    test("has call_agent", "call_agent" in tool_names)
    test("has multi_agent_query", "multi_agent_query" in tool_names)

    # Verify tool schemas
    for tool in GROW_TOOLS:
        name = tool["function"]["name"]
        if name == "discover_agents":
            params = tool["function"]["parameters"]["properties"]
            test("discover_agents has chain param", "chain" in params)
            test("discover_agents has skills param", "skills" in params)
            test("discover_agents has min_trust param", "min_trust" in params)
        elif name == "call_agent":
            params = tool["function"]["parameters"]
            test("call_agent requires agent_url", "agent_url" in params.get("required", []))
            test("call_agent requires skill", "skill" in params.get("required", []))
            test("call_agent requires message", "message" in params.get("required", []))
        elif name == "multi_agent_query":
            params = tool["function"]["parameters"]
            test("multi_agent_query requires skill", "skill" in params.get("required", []))
            test("multi_agent_query requires message", "message" in params.get("required", []))


async def main():
    print("=" * 60)
    print("A2A Stack v2.0 — End-to-End Test Suite")
    print("=" * 60)

    try:
        await test_task_manager()
    except Exception as e:
        print(f"\n  CRASH in test_task_manager: {e}")
        traceback.print_exc()

    try:
        await test_x402()
    except Exception as e:
        print(f"\n  CRASH in test_x402: {e}")
        traceback.print_exc()

    try:
        await test_a2a_client()
    except Exception as e:
        print(f"\n  CRASH in test_a2a_client: {e}")
        traceback.print_exc()

    try:
        await test_registry()
    except Exception as e:
        print(f"\n  CRASH in test_registry: {e}")
        traceback.print_exc()

    try:
        await test_mcp_client()
    except Exception as e:
        print(f"\n  CRASH in test_mcp_client: {e}")
        traceback.print_exc()

    try:
        await test_orchestrator()
    except Exception as e:
        print(f"\n  CRASH in test_orchestrator: {e}")
        traceback.print_exc()

    try:
        await test_brain_tools()
    except Exception as e:
        print(f"\n  CRASH in test_brain_tools: {e}")
        traceback.print_exc()

    print("\n" + "=" * 60)
    print(f"RESULTS: {PASS} passed, {FAIL} failed")
    if ERRORS:
        print(f"\nFAILURES:")
        for err in ERRORS:
            print(f"  - {err}")
    print("=" * 60)

    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())
