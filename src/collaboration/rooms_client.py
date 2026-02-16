"""
Agent Rooms Client (Python)
============================

Python client for the OpenClaw Agent Rooms API (Pattern #30).

Enables GanjaMon's sub-agents (grow orchestrator, trading agent, social daemon)
to collaborate through shared rooms instead of file-based IPC.

Rooms:
  - ganjamon-cultivation: Grok agent ↔ sensor bot ↔ scheduling bot
  - ganjamon-trading: Trading agent ↔ alpha scanner ↔ risk manager

Usage:
    from src.collaboration.rooms_client import AgentRoomsClient

    client = AgentRoomsClient()
    await client.join("ganjamon-cultivation", agent="GrowOrchestrator")
    await client.post("ganjamon-cultivation",
                       from_agent="GrowOrchestrator",
                       content="VPD at 1.2 kPa, watered 200ml")
    messages = await client.get_history("ganjamon-cultivation", limit=10)
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

# Default to the public Railway instance; can override with env var
DEFAULT_ROOMS_URL = "https://agent-rooms-production.up.railway.app"


class AgentRoomsClient:
    """
    Async Python client for the Agent Rooms collaboration API.

    Supports room lifecycle (create/join/leave), messaging, and task management.
    Falls back to local file-based IPC if the rooms server is unreachable.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        agent_name: str = "GanjaMon",
        timeout: float = 10.0,
    ):
        self.base_url = base_url or os.getenv("AGENT_ROOMS_URL", DEFAULT_ROOMS_URL)
        self.agent_name = agent_name
        self.timeout = timeout
        self._joined_rooms: set = set()
        self._fallback_dir = Path("data/rooms_fallback")
        self._healthy = True  # Track server health for fallback

    async def _request(
        self,
        method: str,
        path: str,
        body: Optional[dict] = None,
    ) -> Optional[dict]:
        """Make an HTTP request to the rooms server."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                kwargs: Dict[str, Any] = {
                    "headers": {"Content-Type": "application/json"},
                }
                if body:
                    kwargs["json"] = body

                resp = await getattr(client, method.lower())(
                    f"{self.base_url}{path}", **kwargs
                )

                if resp.status_code >= 400:
                    logger.warning(f"Rooms API error: {resp.status_code} on {method} {path}")
                    return None

                self._healthy = True
                return resp.json()

        except httpx.TimeoutException:
            logger.warning(f"Rooms API timeout: {method} {path}")
            self._healthy = False
            return None
        except Exception as e:
            logger.warning(f"Rooms API error: {e}")
            self._healthy = False
            return None

    # ==================== ROOMS ====================

    async def list_rooms(self) -> List[dict]:
        """List all public rooms."""
        data = await self._request("GET", "/rooms")
        if data:
            return data.get("rooms", [])
        return []

    async def create_room(
        self,
        name: str,
        description: str = "",
        public: bool = True,
    ) -> Optional[dict]:
        """Create a new room."""
        data = await self._request("POST", "/rooms", {
            "name": name,
            "description": description,
            "owner": self.agent_name,
            "public": public,
        })
        if data:
            room = data.get("room", data)
            room_id = room.get("id", room.get("_id", ""))
            self._joined_rooms.add(room_id)
            logger.info(f"Created room: {name} (id={room_id})")
            return room
        return None

    async def get_room(self, room_id: str) -> Optional[dict]:
        """Get room details."""
        data = await self._request("GET", f"/rooms/{room_id}")
        return data.get("room", data) if data else None

    async def join(self, room_id: str, agent: Optional[str] = None, skills: Optional[list] = None) -> bool:
        """Join a room."""
        data = await self._request("POST", f"/rooms/{room_id}/join", {
            "agent": agent or self.agent_name,
            "skills": skills or ["cultivation", "trading", "social"],
        })
        if data:
            self._joined_rooms.add(room_id)
            logger.info(f"Joined room: {room_id} as {agent or self.agent_name}")
            return True
        return False

    async def leave(self, room_id: str) -> bool:
        """Leave a room."""
        data = await self._request("POST", f"/rooms/{room_id}/leave", {
            "agent": self.agent_name,
        })
        self._joined_rooms.discard(room_id)
        return data is not None

    # ==================== MESSAGES ====================

    async def post(
        self,
        room_id: str,
        content: str,
        from_agent: Optional[str] = None,
        attachments: Optional[list] = None,
        reply_to: Optional[str] = None,
    ) -> Optional[dict]:
        """Post a message to a room.

        Falls back to local file-based IPC if server is unreachable.
        """
        body = {
            "from": from_agent or self.agent_name,
            "content": content,
            "attachments": attachments or [],
        }
        if reply_to:
            body["replyTo"] = reply_to

        data = await self._request("POST", f"/rooms/{room_id}/messages", body)
        if data:
            return data.get("message", data)

        # Fallback: write to local file
        self._write_fallback(room_id, body)
        return None

    async def get_history(
        self,
        room_id: str,
        limit: int = 50,
        before: Optional[str] = None,
    ) -> List[dict]:
        """Get room message history."""
        path = f"/rooms/{room_id}/messages?limit={limit}"
        if before:
            path += f"&before={before}"
        data = await self._request("GET", path)
        if data:
            return data.get("messages", [])

        # Fallback: read from local file
        return self._read_fallback(room_id)

    # ==================== TASKS ====================

    async def add_task(
        self,
        room_id: str,
        title: str,
        description: str = "",
        assignee: Optional[str] = None,
    ) -> Optional[dict]:
        """Add a task to a room."""
        data = await self._request("POST", f"/rooms/{room_id}/tasks", {
            "title": title,
            "description": description,
            "assignee": assignee or self.agent_name,
            "createdBy": self.agent_name,
        })
        return data.get("task", data) if data else None

    async def get_tasks(self, room_id: str) -> List[dict]:
        """Get room tasks."""
        data = await self._request("GET", f"/rooms/{room_id}/tasks")
        return data.get("tasks", []) if data else []

    async def complete_task(self, room_id: str, task_id: str) -> bool:
        """Mark a task as done."""
        data = await self._request(
            "PATCH", f"/rooms/{room_id}/tasks/{task_id}",
            {"status": "done"}
        )
        return data is not None

    # ==================== CONVENIENCE ====================

    async def broadcast_decision(
        self,
        room_id: str,
        decision: dict,
        sensor_data: dict,
    ):
        """Broadcast an AI grow decision to a collaboration room.

        This replaces file-based IPC (data/ipc_decisions.json) with
        room-based messaging.
        """
        # Format as a structured message
        vpd = sensor_data.get("environment", {}).get("vpd_kpa", "?")
        temp = sensor_data.get("environment", {}).get("temperature_f", "?")
        health = decision.get("analysis", {}).get("overall_health", "stable")

        content = (
            f"🌱 **Decision Broadcast**\n"
            f"VPD: {vpd} kPa | Temp: {temp}°F | Health: {health}\n"
        )

        actions = decision.get("actions", [])
        if actions:
            action_strs = [f"- {a.get('tool', '?')}: {a.get('parameters', {})}" for a in actions[:5]]
            content += "Actions:\n" + "\n".join(action_strs) + "\n"

        recommendations = decision.get("recommendations", [])
        if recommendations:
            content += "Recommendations:\n" + "\n".join(f"- {r}" for r in recommendations[:3])

        await self.post(
            room_id,
            content=content,
            from_agent="GrowOrchestrator",
            attachments=[{
                "type": "json",
                "name": "decision.json",
                "data": json.dumps(decision, default=str)[:2000],
            }],
        )

    async def health_check(self) -> bool:
        """Check if the rooms server is reachable."""
        data = await self._request("GET", "/health")
        self._healthy = data is not None
        return self._healthy

    # ==================== FALLBACK ====================

    def _write_fallback(self, room_id: str, message: dict):
        """Write message to local fallback file when server is down."""
        try:
            fallback_file = self._fallback_dir / f"{room_id}.jsonl"
            fallback_file.parent.mkdir(parents=True, exist_ok=True)
            message["timestamp"] = time.time()
            message["_fallback"] = True
            with open(fallback_file, "a") as f:
                f.write(json.dumps(message, default=str) + "\n")
            logger.debug(f"Fallback write: {room_id}")
        except Exception as e:
            logger.warning(f"Fallback write failed: {e}")

    def _read_fallback(self, room_id: str) -> List[dict]:
        """Read messages from local fallback file."""
        fallback_file = self._fallback_dir / f"{room_id}.jsonl"
        if not fallback_file.exists():
            return []
        try:
            messages = []
            for line in fallback_file.read_text().strip().split("\n"):
                if line:
                    messages.append(json.loads(line))
            return messages[-50:]  # Last 50
        except Exception:
            return []

    async def flush_fallback(self, room_id: str) -> int:
        """Send any buffered fallback messages to the server.

        Call this when the server comes back online.
        Returns the number of messages flushed.
        """
        fallback_file = self._fallback_dir / f"{room_id}.jsonl"
        if not fallback_file.exists():
            return 0

        messages = self._read_fallback(room_id)
        flushed = 0

        for msg in messages:
            msg.pop("_fallback", None)
            msg.pop("timestamp", None)
            result = await self._request("POST", f"/rooms/{room_id}/messages", msg)
            if result:
                flushed += 1
            else:
                # Server went down again, stop trying
                break

        if flushed == len(messages):
            # All messages flushed, remove fallback file
            try:
                fallback_file.unlink()
            except Exception:
                pass
            logger.info(f"Flushed {flushed} fallback messages to room {room_id}")
        else:
            logger.info(f"Partial flush: {flushed}/{len(messages)} messages to room {room_id}")

        return flushed


# ==================== SINGLETON ====================

_client: Optional[AgentRoomsClient] = None


def get_rooms_client() -> AgentRoomsClient:
    """Get or create the singleton rooms client."""
    global _client
    if _client is None:
        _client = AgentRoomsClient()
    return _client
