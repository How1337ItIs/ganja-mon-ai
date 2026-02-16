"""
A2A (Agent-to-Agent) Protocol Stack
====================================

Full two-way A2A implementation:
- Client: Call other agents via JSON-RPC 2.0
- Registry: Discover agents via 8004scan + agent card fetching
- TaskManager: Persistent SQLite-backed task state machine
- X402: Payment verification (receiving) + payment sending (client)
- Orchestrator: Multi-agent parallel calls + response aggregation
- MCPClient: Call external MCP tool servers
"""

from .client import A2AClient, AgentCard
from .registry import AgentRegistry
from .task_manager import TaskManager, TaskStatus
from .x402 import X402Verifier, X402Payer
from .orchestrator import A2AOrchestrator
from .mcp_client import MCPClient
from .outbound_daemon import OutboundA2ADaemon
from .validator import AgentValidator, ValidationReport, CheckResult

__all__ = [
    "A2AClient",
    "AgentCard",
    "AgentRegistry",
    "TaskManager",
    "TaskStatus",
    "X402Verifier",
    "X402Payer",
    "A2AOrchestrator",
    "MCPClient",
    "OutboundA2ADaemon",
    "AgentValidator",
    "ValidationReport",
    "CheckResult",
]
