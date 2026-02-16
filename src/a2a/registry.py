"""
Agent Registry Client
=====================

Discover and resolve agents via:
- 8004scan.io API (on-chain registry)
- Direct agent card URLs
- IPFS gateway resolution
- Local cache with TTL

Provides search by capability, chain, tags, and agent ID.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from .client import AgentCard

logger = logging.getLogger(__name__)

# 8004scan API base (www. required — non-www returns 307)
SCAN_API = "https://www.8004scan.io/api/v1"

# Chain name -> chain_id mapping for 8004scan
CHAIN_IDS = {
    "monad": 10143,
    "ethereum": 1,
    "base": 8453,
    "bsc": 56,
    "bnb": 56,
    "avalanche": 43114,
    "avax": 43114,
}

# IPFS gateways (fallback order)
IPFS_GATEWAYS = [
    "https://gateway.pinata.cloud/ipfs/",
    "https://ipfs.io/ipfs/",
    "https://cloudflare-ipfs.com/ipfs/",
    "https://dweb.link/ipfs/",
]


@dataclass
class AgentEntry:
    """Agent entry from the 8004scan registry."""
    agent_id: int
    name: str
    description: str
    chain: str
    owner: str
    agent_uri: str = ""
    a2a_url: Optional[str] = None
    mcp_url: Optional[str] = None
    trust_score: float = 0.0
    tags: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    x402_support: bool = False
    raw: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_scan_data(cls, data: dict, chain: str = "monad") -> "AgentEntry":
        """Parse from 8004scan API v1 response."""
        # Primary: top-level a2a_endpoint / mcp_server fields (8004scan v1 current)
        a2a_url = data.get("a2a_endpoint") or None
        mcp_url = data.get("mcp_server") or None

        # Always extract endpoints dict for skills even if URLs already found
        endpoints = data.get("endpoints") or {}
        a2a_info = endpoints.get("a2a") or {}
        mcp_info = endpoints.get("mcp") or {}

        # Fallback: endpoints dict if top-level fields missing
        if not a2a_url:
            a2a_url = a2a_info.get("endpoint") if isinstance(a2a_info, dict) else None
        if not mcp_url:
            mcp_url = mcp_info.get("endpoint") if isinstance(mcp_info, dict) else None

        # Fallback 2: services dict (8004scan also has services.a2a.endpoint)
        if not a2a_url or not mcp_url:
            services = data.get("services") or {}
            if isinstance(services, dict):
                if not a2a_url:
                    a2a_svc = services.get("a2a") or {}
                    a2a_url = a2a_svc.get("endpoint") if isinstance(a2a_svc, dict) else None
                if not mcp_url:
                    mcp_svc = services.get("mcp") or {}
                    mcp_url = mcp_svc.get("endpoint") if isinstance(mcp_svc, dict) else None

        # Extract skills from endpoints.a2a.skills or services.a2a.skills
        skills = []
        for info in [a2a_info, (data.get("services") or {}).get("a2a") or {}]:
            if isinstance(info, dict) and not skills:
                for s in info.get("skills", []):
                    if isinstance(s, dict):
                        skills.append(s.get("id", s.get("name", "")))
                    elif isinstance(s, str):
                        skills.append(s)

        # Tags and categories
        tags = data.get("tags", []) or []
        categories = data.get("categories", []) or []

        return cls(
            agent_id=int(data.get("token_id", data.get("agentId", data.get("id", 0)))),
            name=data.get("name", "Unknown"),
            description=data.get("description", "") or "",
            chain=chain,
            owner=data.get("owner_address", data.get("owner", "")),
            agent_uri=data.get("raw_metadata", {}).get("offchain_uri", "") if isinstance(data.get("raw_metadata"), dict) else "",
            a2a_url=a2a_url,
            mcp_url=mcp_url,
            trust_score=float(data.get("total_score", data.get("trustScore", 0.0))),
            tags=tags + categories,
            skills=skills,
            x402_support=bool(data.get("x402_supported", False)),
            raw=data,
        )


class AgentRegistry:
    """
    Client for discovering and resolving agents from 8004scan.

    Usage:
        registry = AgentRegistry()
        agents = await registry.search(chain="monad", tags=["trading"])
        for agent in agents:
            if agent.a2a_url:
                card = await registry.get_card(agent)
    """

    def __init__(self, cache_dir: Optional[Path] = None, cache_ttl: int = 600):
        self._cache_dir = cache_dir or Path("data/a2a_cache")
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache_ttl = cache_ttl
        self._memory_cache: Dict[str, tuple[float, Any]] = {}

    async def list_agents(self, chain: str = "monad", limit: int = 50) -> List[AgentEntry]:
        """
        List all agents on a chain from 8004scan.

        Returns parsed AgentEntry objects.
        """
        cache_key = f"list:{chain}:{limit}"
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        chain_id = CHAIN_IDS.get(chain.lower())
        params = {
            "limit": limit,
            "sort_by": "total_score",
            "sort_direction": "desc",
        }
        if chain_id:
            params["chain_id"] = chain_id

        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                resp = await client.get(
                    f"{SCAN_API}/agents",
                    params=params,
                    headers={"Accept": "application/json", "User-Agent": "GanjaMon-Registry/1.0"},
                )
                if resp.status_code != 200:
                    logger.warning(f"8004scan list failed: {resp.status_code}")
                    return []

                data = resp.json()
        except Exception as e:
            logger.error(f"8004scan list error: {e}")
            return []

        # 8004scan v1 returns {items: [...], total, limit, offset}
        agents_raw = data.get("items", data if isinstance(data, list) else data.get("agents", data.get("data", [])))

        agents = []
        for entry in agents_raw:
            try:
                agents.append(AgentEntry.from_scan_data(entry, chain))
            except Exception as e:
                logger.debug(f"Failed to parse agent entry: {e}")

        self._set_cache(cache_key, agents)
        logger.info(f"Listed {len(agents)} agents on {chain}")
        return agents

    async def get_agent(self, agent_id: int, chain: str = "monad") -> Optional[AgentEntry]:
        """Get a specific agent by ID (token_id)."""
        cache_key = f"agent:{chain}:{agent_id}"
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        # 8004scan v1 doesn't have a single-agent endpoint — filter from list
        chain_id = CHAIN_IDS.get(chain.lower())
        params = {"limit": 100}
        if chain_id:
            params["chain_id"] = chain_id

        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                resp = await client.get(
                    f"{SCAN_API}/agents",
                    params=params,
                    headers={"Accept": "application/json", "User-Agent": "GanjaMon-Registry/1.0"},
                )
                if resp.status_code != 200:
                    logger.warning(f"8004scan list failed for agent lookup: {resp.status_code}")
                    return None

                data = resp.json()
        except Exception as e:
            logger.error(f"8004scan agent fetch error: {e}")
            return None

        items = data.get("items", [])
        for item in items:
            tid = int(item.get("token_id", 0))
            if tid == agent_id:
                agent = AgentEntry.from_scan_data(item, chain)
                self._set_cache(cache_key, agent)
                return agent

        logger.warning(f"Agent {agent_id} not found on {chain}")
        return None

    async def search(
        self,
        chain: str = "monad",
        tags: Optional[List[str]] = None,
        skills: Optional[List[str]] = None,
        has_a2a: bool = False,
        has_mcp: bool = False,
        has_x402: bool = False,
        min_trust: float = 0.0,
    ) -> List[AgentEntry]:
        """
        Search for agents matching criteria.

        Fetches the full list then filters locally (8004scan may not support
        server-side filtering for all fields).
        """
        agents = await self.list_agents(chain, limit=100)

        results = []
        for agent in agents:
            # Filter by A2A availability
            if has_a2a and not agent.a2a_url:
                continue
            # Filter by MCP availability
            if has_mcp and not agent.mcp_url:
                continue
            # Filter by x402 support
            if has_x402 and not agent.x402_support:
                continue
            # Filter by minimum trust score
            if min_trust > 0 and agent.trust_score < min_trust:
                continue
            # Filter by tags
            if tags:
                agent_tags_lower = [t.lower() for t in agent.tags]
                if not any(t.lower() in agent_tags_lower for t in tags):
                    continue
            # Filter by skills
            if skills:
                agent_skills_lower = [s.lower() for s in agent.skills]
                if not any(s.lower() in agent_skills_lower for s in skills):
                    continue

            results.append(agent)

        return results

    async def get_card(self, agent: AgentEntry) -> Optional[AgentCard]:
        """
        Fetch the full agent card for an AgentEntry.

        Resolves the A2A URL or falls back to IPFS URI resolution.
        """
        if agent.a2a_url:
            try:
                from .client import get_a2a_client
                client = get_a2a_client()
                return await client.fetch_agent_card(agent.a2a_url)
            except Exception as e:
                logger.warning(f"Failed to fetch card from A2A URL {agent.a2a_url}: {e}")

        # Fallback: resolve agent URI (IPFS or HTTP)
        if agent.agent_uri:
            metadata = await self.resolve_uri(agent.agent_uri)
            if metadata:
                # Build a card from the registration metadata
                services = metadata.get("services", [])
                a2a_endpoint = None
                for svc in services:
                    if (svc.get("protocol") or svc.get("type", "")).upper() == "A2A":
                        a2a_endpoint = svc.get("endpoint") or svc.get("url")
                        break

                if a2a_endpoint:
                    try:
                        from .client import get_a2a_client
                        client = get_a2a_client()
                        return await client.fetch_agent_card(a2a_endpoint)
                    except Exception:
                        pass

                # Construct minimal card from metadata
                return AgentCard(
                    name=metadata.get("name", agent.name),
                    description=metadata.get("description", agent.description),
                    url=a2a_endpoint or "",
                    skills=metadata.get("skills", []),
                    raw=metadata,
                )

        return None

    async def resolve_uri(self, uri: str) -> Optional[Dict[str, Any]]:
        """
        Resolve an agent URI to its metadata content.

        Handles IPFS (ipfs://CID), HTTPS, and data: URIs.
        """
        if not uri:
            return None

        # data: URI — decode locally
        if uri.startswith("data:"):
            from ..blockchain.erc8004_parser import decode_agent_uri
            success, warnings, metadata = decode_agent_uri(uri)
            if success:
                return metadata
            logger.warning(f"data: URI decode failed: {warnings}")
            return None

        # IPFS URI
        if uri.startswith("ipfs://"):
            cid = uri.replace("ipfs://", "").strip("/")
            return await self._fetch_ipfs(cid)

        # Plain CID (starts with Qm or bafy)
        if uri.startswith("Qm") or uri.startswith("bafy"):
            return await self._fetch_ipfs(uri)

        # HTTP/HTTPS
        if uri.startswith("http://") or uri.startswith("https://"):
            try:
                async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                    resp = await client.get(uri, headers={"Accept": "application/json"})
                    if resp.status_code == 200:
                        return resp.json()
            except Exception as e:
                logger.warning(f"HTTP URI fetch failed: {e}")
            return None

        # Inline JSON
        if uri.startswith("{"):
            try:
                return json.loads(uri)
            except json.JSONDecodeError:
                pass

        return None

    async def _fetch_ipfs(self, cid: str) -> Optional[Dict[str, Any]]:
        """Fetch JSON content from IPFS via gateway fallback chain."""
        for gateway in IPFS_GATEWAYS:
            try:
                url = f"{gateway}{cid}"
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(url, headers={"Accept": "application/json"})
                    if resp.status_code == 200:
                        return resp.json()
            except Exception:
                continue
        logger.warning(f"All IPFS gateways failed for CID: {cid}")
        return None

    def _get_cache(self, key: str) -> Any:
        if key in self._memory_cache:
            ts, val = self._memory_cache[key]
            if time.time() - ts < self._cache_ttl:
                return val
            del self._memory_cache[key]
        return None

    def _set_cache(self, key: str, value: Any):
        self._memory_cache[key] = (time.time(), value)

    async def save_known_agents(self, agents: List[AgentEntry]):
        """Persist known agents to disk for offline access."""
        out = self._cache_dir / "known_agents.json"
        data = []
        for a in agents:
            data.append({
                "agent_id": a.agent_id,
                "name": a.name,
                "chain": a.chain,
                "a2a_url": a.a2a_url,
                "mcp_url": a.mcp_url,
                "trust_score": a.trust_score,
                "skills": a.skills,
                "tags": a.tags,
            })
        out.write_text(json.dumps(data, indent=2))
        logger.info(f"Saved {len(data)} known agents to {out}")

    async def load_known_agents(self) -> List[Dict[str, Any]]:
        """Load known agents from disk cache."""
        path = self._cache_dir / "known_agents.json"
        if path.exists():
            return json.loads(path.read_text())
        return []


# Singleton
_instance: Optional[AgentRegistry] = None


def get_registry() -> AgentRegistry:
    global _instance
    if _instance is None:
        _instance = AgentRegistry()
    return _instance
