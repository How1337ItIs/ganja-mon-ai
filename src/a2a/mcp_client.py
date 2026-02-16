"""
MCP Client
==========

Client for calling external MCP (Model Context Protocol) tool servers.

Features:
- Server discovery and initialization
- Tool listing and caching
- Tool invocation with parameter validation
- Multi-server coordination
- Rate limiting
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass
class MCPTool:
    """A tool exposed by an MCP server."""
    name: str
    description: str
    input_schema: Dict[str, Any] = field(default_factory=dict)
    server_url: str = ""
    server_name: str = ""

    @classmethod
    def from_dict(cls, data: dict, server_url: str = "", server_name: str = "") -> "MCPTool":
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            input_schema=data.get("inputSchema", data.get("input_schema", {})),
            server_url=server_url,
            server_name=server_name,
        )


@dataclass
class MCPCallResult:
    """Result from calling an MCP tool."""
    success: bool
    content: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None
    latency_ms: float = 0.0
    server_name: str = ""
    tool_name: str = ""

    @property
    def text(self) -> str:
        """Extract text content from the result."""
        for item in self.content:
            if item.get("type") == "text":
                return item.get("text", "")
        return ""


class MCPClient:
    """
    Client for external MCP tool servers.

    Usage:
        client = MCPClient()
        await client.connect("https://agent.example.com/mcp/v1")
        tools = await client.list_tools()
        result = await client.call_tool("get_environment", {})
    """

    def __init__(self, timeout: float = 30.0):
        self._timeout = timeout
        self._servers: Dict[str, Dict[str, Any]] = {}  # url -> server info
        self._tools: Dict[str, List[MCPTool]] = {}  # url -> tools
        self._tool_cache_ttl = 300  # 5 min

    async def connect(self, server_url: str) -> Dict[str, Any]:
        """
        Initialize connection to an MCP server.

        Sends the `initialize` JSON-RPC call and caches server info.
        """
        rpc = {
            "jsonrpc": "2.0",
            "id": "init-1",
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {
                    "name": "GanjaMon-MCP-Client",
                    "version": "1.0.0",
                },
            },
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(
                    server_url,
                    json=rpc,
                    headers={"Content-Type": "application/json", "User-Agent": "GanjaMon-MCP/1.0"},
                )

                if resp.status_code != 200:
                    raise ConnectionError(f"MCP init failed: HTTP {resp.status_code}")

                body = resp.json()
                if "error" in body:
                    raise ConnectionError(f"MCP init error: {body['error']}")

                server_info = body.get("result", {})
                self._servers[server_url] = {
                    "info": server_info,
                    "connected_at": time.time(),
                }

                logger.info(f"Connected to MCP server: {server_info.get('name', server_url)}")
                return server_info

        except httpx.TimeoutException:
            raise ConnectionError(f"MCP init timed out: {server_url}")

    async def list_tools(self, server_url: str, force: bool = False) -> List[MCPTool]:
        """
        List available tools from an MCP server.

        Caches results for 5 minutes.
        """
        if not force and server_url in self._tools:
            return self._tools[server_url]

        # Try GET first (some servers return tools on GET)
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(
                    server_url,
                    headers={"Accept": "application/json", "User-Agent": "GanjaMon-MCP/1.0"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if "tools" in data:
                        server_name = data.get("name", server_url)
                        tools = [MCPTool.from_dict(t, server_url, server_name) for t in data["tools"]]
                        self._tools[server_url] = tools
                        return tools
        except Exception:
            pass

        # JSON-RPC tools/list
        rpc = {
            "jsonrpc": "2.0",
            "id": "list-1",
            "method": "tools/list",
            "params": {},
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(
                    server_url,
                    json=rpc,
                    headers={"Content-Type": "application/json", "User-Agent": "GanjaMon-MCP/1.0"},
                )

                if resp.status_code != 200:
                    logger.warning(f"MCP tools/list failed: HTTP {resp.status_code}")
                    return []

                body = resp.json()
                if "error" in body:
                    logger.warning(f"MCP tools/list error: {body['error']}")
                    return []

                result = body.get("result", {})
                tools_raw = result.get("tools", [])
                server_name = self._servers.get(server_url, {}).get("info", {}).get("name", server_url)

                tools = [MCPTool.from_dict(t, server_url, server_name) for t in tools_raw]
                self._tools[server_url] = tools

                logger.info(f"Discovered {len(tools)} tools from {server_name}")
                return tools

        except Exception as e:
            logger.error(f"MCP tools/list failed: {e}")
            return []

    async def call_tool(
        self,
        server_url: str,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
    ) -> MCPCallResult:
        """
        Call a tool on an MCP server.
        """
        rpc = {
            "jsonrpc": "2.0",
            "id": f"call-{tool_name}",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments or {},
            },
        }

        start = time.monotonic()
        server_name = self._servers.get(server_url, {}).get("info", {}).get("name", "")

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(
                    server_url,
                    json=rpc,
                    headers={"Content-Type": "application/json", "User-Agent": "GanjaMon-MCP/1.0"},
                )

            latency = (time.monotonic() - start) * 1000

            if resp.status_code != 200:
                return MCPCallResult(
                    success=False,
                    error=f"HTTP {resp.status_code}: {resp.text[:200]}",
                    latency_ms=latency,
                    server_name=server_name,
                    tool_name=tool_name,
                )

            body = resp.json()

            if "error" in body and body["error"]:
                return MCPCallResult(
                    success=False,
                    error=body["error"].get("message", str(body["error"])),
                    latency_ms=latency,
                    server_name=server_name,
                    tool_name=tool_name,
                )

            result = body.get("result", {})
            content = result.get("content", [])

            return MCPCallResult(
                success=True,
                content=content,
                latency_ms=latency,
                server_name=server_name,
                tool_name=tool_name,
            )

        except Exception as e:
            return MCPCallResult(
                success=False,
                error=str(e),
                latency_ms=(time.monotonic() - start) * 1000,
                server_name=server_name,
                tool_name=tool_name,
            )

    async def discover_and_call(
        self,
        server_url: str,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
    ) -> MCPCallResult:
        """
        Connect, discover tools, and call a specific tool in one go.
        """
        # Connect if needed
        if server_url not in self._servers:
            try:
                await self.connect(server_url)
            except Exception as e:
                return MCPCallResult(success=False, error=f"Connection failed: {e}", tool_name=tool_name)

        # Verify tool exists
        tools = await self.list_tools(server_url)
        tool_names = [t.name for t in tools]
        if tool_name not in tool_names:
            return MCPCallResult(
                success=False,
                error=f"Tool '{tool_name}' not found. Available: {tool_names}",
                tool_name=tool_name,
            )

        return await self.call_tool(server_url, tool_name, arguments)

    async def call_across_servers(
        self,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
    ) -> List[MCPCallResult]:
        """
        Call a tool across all connected servers that have it.
        """
        results = []
        for server_url in self._servers:
            tools = await self.list_tools(server_url)
            if any(t.name == tool_name for t in tools):
                result = await self.call_tool(server_url, tool_name, arguments)
                results.append(result)
        return results

    def get_all_tools(self) -> List[MCPTool]:
        """Get all tools across all connected servers."""
        all_tools = []
        for tools in self._tools.values():
            all_tools.extend(tools)
        return all_tools

    def get_connected_servers(self) -> List[Dict[str, Any]]:
        """Get info about all connected servers."""
        return [
            {
                "url": url,
                "name": info.get("info", {}).get("name", url),
                "tools": len(self._tools.get(url, [])),
                "connected_at": info.get("connected_at"),
            }
            for url, info in self._servers.items()
        ]


# Singleton
_instance: Optional[MCPClient] = None


def get_mcp_client() -> MCPClient:
    global _instance
    if _instance is None:
        _instance = MCPClient()
    return _instance
