"""
Agent Validator Service
=======================

Validates other agents' A2A/MCP/x402 endpoints on the Monad ecosystem.
Follows the SnowRail Sentinel pattern -- checks multiple protocol layers
and produces a composite bootstrap score (0-100).

Checks:
    1. A2A endpoint     (0-30 pts) - agent-card.json, required fields, response time
    2. MCP endpoint     (0-25 pts) - tools/list JSON-RPC, tool count
    3. x402 compliance  (0-15 pts) - 402 response with payment headers
    4. Infra basics     (0-20 pts) - liveness, TLS, latency
    5. 8004scan reg     (0-10 pts) - registry presence, trust score

Usage:
    validator = AgentValidator()
    report = await validator.validate_agent("https://agent.example.com")
    print(report.total_score)  # 0-100
"""

import logging
import ssl
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import httpx

from .registry import AgentRegistry, get_registry, SCAN_API, CHAIN_IDS

logger = logging.getLogger(__name__)

# Thresholds
A2A_TIMEOUT = 15.0
MCP_TIMEOUT = 15.0
X402_TIMEOUT = 10.0
INFRA_TIMEOUT = 10.0
REGISTRY_TIMEOUT = 15.0

# Required fields in agent card per A2A spec
REQUIRED_CARD_FIELDS = {"name", "description", "skills"}
RECOMMENDED_CARD_FIELDS = {"url", "version", "capabilities", "provider"}


@dataclass
class CheckResult:
    """Result from a single validation check."""
    check_name: str
    score: int
    max_score: int
    passed: bool
    details: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    latency_ms: float = 0.0

    @property
    def pct(self) -> float:
        return (self.score / self.max_score * 100) if self.max_score > 0 else 0.0


@dataclass
class ValidationReport:
    """Full validation report for an agent."""
    agent_url: str
    total_score: int
    max_score: int = 100
    checks: List[CheckResult] = field(default_factory=list)
    timestamp: str = ""
    duration_ms: float = 0.0
    agent_name: Optional[str] = None
    agent_version: Optional[str] = None
    skill_count: int = 0
    tool_count: int = 0

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    @property
    def grade(self) -> str:
        """Letter grade based on total score."""
        if self.total_score >= 90:
            return "A"
        elif self.total_score >= 80:
            return "B"
        elif self.total_score >= 65:
            return "C"
        elif self.total_score >= 50:
            return "D"
        return "F"

    @property
    def pct(self) -> float:
        return (self.total_score / self.max_score * 100) if self.max_score > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_url": self.agent_url,
            "agent_name": self.agent_name,
            "agent_version": self.agent_version,
            "total_score": self.total_score,
            "max_score": self.max_score,
            "grade": self.grade,
            "pct": round(self.pct, 1),
            "skill_count": self.skill_count,
            "tool_count": self.tool_count,
            "checks": [
                {
                    "name": c.check_name,
                    "score": c.score,
                    "max_score": c.max_score,
                    "passed": c.passed,
                    "pct": round(c.pct, 1),
                    "latency_ms": round(c.latency_ms, 1),
                    "details": c.details,
                    "errors": c.errors,
                    "warnings": c.warnings,
                }
                for c in self.checks
            ],
            "timestamp": self.timestamp,
            "duration_ms": round(self.duration_ms, 1),
        }


class AgentValidator:
    """
    Validates agents across five protocol layers.

    Scoring breakdown:
        A2A endpoint:       0-30 points
        MCP endpoint:       0-25 points
        x402 compliance:    0-15 points
        Infrastructure:     0-20 points
        8004scan registry:  0-10 points
        ---------------------------------
        Total:              0-100 points
    """

    def __init__(self, registry: Optional[AgentRegistry] = None):
        self._registry = registry

    @property
    def registry(self) -> AgentRegistry:
        if self._registry is None:
            self._registry = get_registry()
        return self._registry

    async def validate_agent(
        self,
        agent_url: str,
        agent_id: Optional[int] = None,
        chain: str = "monad",
    ) -> ValidationReport:
        """
        Run all validation checks against an agent URL.

        Args:
            agent_url: Base URL of the agent (e.g. https://agent.example.com)
            agent_id: Optional 8004scan token ID for registry check
            chain: Blockchain to check registry on

        Returns:
            ValidationReport with composite score 0-100
        """
        start = time.monotonic()

        # Normalize URL
        agent_url = agent_url.rstrip("/")
        if not agent_url.startswith("http"):
            agent_url = f"https://{agent_url}"

        report = ValidationReport(agent_url=agent_url, total_score=0)

        # Run all checks (sequentially to avoid overwhelming the target)
        a2a_result = await self.validate_a2a(agent_url)
        report.checks.append(a2a_result)

        # Extract agent metadata from A2A check
        if a2a_result.details.get("name"):
            report.agent_name = a2a_result.details["name"]
        if a2a_result.details.get("version"):
            report.agent_version = a2a_result.details["version"]
        if a2a_result.details.get("skill_count"):
            report.skill_count = a2a_result.details["skill_count"]

        mcp_result = await self.validate_mcp(agent_url)
        report.checks.append(mcp_result)
        if mcp_result.details.get("tool_count"):
            report.tool_count = mcp_result.details["tool_count"]

        x402_result = await self.validate_x402(agent_url)
        report.checks.append(x402_result)

        infra_result = await self.validate_infra(agent_url)
        report.checks.append(infra_result)

        reg_result = await self.validate_registration(agent_id, chain)
        report.checks.append(reg_result)

        # Sum scores
        report.total_score = sum(c.score for c in report.checks)
        report.duration_ms = (time.monotonic() - start) * 1000

        logger.info(
            f"Validated {agent_url}: {report.total_score}/{report.max_score} "
            f"({report.grade}) in {report.duration_ms:.0f}ms"
        )

        return report

    # -------------------------------------------------------------------------
    # Check 1: A2A Endpoint (0-30 points)
    # -------------------------------------------------------------------------

    async def validate_a2a(self, url: str) -> CheckResult:
        """
        Validate the agent's A2A endpoint.

        Scoring:
            - Reachable and returns JSON:      10 pts
            - Has required fields (name, description, skills): 10 pts
            - Has recommended fields + skills have ids/descriptions: 5 pts
            - Response time < 2s:              3 pts
            - Response time < 5s:              2 pts (fallback)
        """
        result = CheckResult(check_name="a2a", score=0, max_score=30, passed=False)

        # Try multiple discovery paths
        card_urls = [
            f"{url}/.well-known/agent-card.json",
            f"{url}/a2a/v1",
            url,
        ]

        card_data = None
        start = time.monotonic()

        async with httpx.AsyncClient(
            timeout=A2A_TIMEOUT,
            follow_redirects=True,
            verify=True,
        ) as client:
            for card_url in card_urls:
                try:
                    resp = await client.get(
                        card_url,
                        headers={"Accept": "application/json", "User-Agent": "GanjaMon-Validator/1.0"},
                    )
                    latency = (time.monotonic() - start) * 1000
                    result.latency_ms = latency

                    if resp.status_code == 200:
                        content_type = resp.headers.get("content-type", "")
                        if "json" in content_type or "text" in content_type:
                            try:
                                card_data = resp.json()
                                result.details["resolved_url"] = card_url
                                break
                            except Exception:
                                result.warnings.append(f"Invalid JSON from {card_url}")
                        else:
                            result.warnings.append(
                                f"{card_url} returned content-type: {content_type}"
                            )
                    else:
                        result.warnings.append(f"{card_url} returned HTTP {resp.status_code}")

                except httpx.TimeoutException:
                    result.errors.append(f"Timeout fetching {card_url}")
                except Exception as e:
                    result.errors.append(f"Error fetching {card_url}: {str(e)[:100]}")

        if card_data is None:
            result.errors.append("No valid agent card found at any discovery path")
            return result

        # +10: Reachable and returns valid JSON
        result.score += 10
        result.passed = True

        # Check required fields
        missing_required = REQUIRED_CARD_FIELDS - set(card_data.keys())
        if not missing_required:
            result.score += 10
            result.details["required_fields"] = "all present"
        else:
            # Partial credit for some required fields
            present = len(REQUIRED_CARD_FIELDS) - len(missing_required)
            partial = int(10 * present / len(REQUIRED_CARD_FIELDS))
            result.score += partial
            result.warnings.append(f"Missing required fields: {missing_required}")
            result.details["required_fields"] = f"{present}/{len(REQUIRED_CARD_FIELDS)}"

        # Extract metadata
        result.details["name"] = card_data.get("name", "")
        result.details["version"] = card_data.get("version", "")
        result.details["description_length"] = len(card_data.get("description", ""))

        # Check skills quality
        skills = card_data.get("skills", [])
        result.details["skill_count"] = len(skills)

        recommended_present = RECOMMENDED_CARD_FIELDS & set(card_data.keys())
        skills_have_ids = all(
            isinstance(s, dict) and ("id" in s or "name" in s) for s in skills
        ) if skills else False
        skills_have_descriptions = all(
            isinstance(s, dict) and "description" in s for s in skills
        ) if skills else False

        quality_score = 0
        if len(recommended_present) >= 3:
            quality_score += 2
        if skills and skills_have_ids:
            quality_score += 2
        if skills and skills_have_descriptions:
            quality_score += 1
        result.score += min(quality_score, 5)

        if not skills:
            result.warnings.append("No skills defined in agent card")

        # Response time scoring
        if result.latency_ms < 2000:
            result.score += 3
        elif result.latency_ms < 5000:
            result.score += 2
        else:
            result.warnings.append(f"Slow A2A response: {result.latency_ms:.0f}ms")

        result.details["latency_ms"] = round(result.latency_ms, 1)
        return result

    # -------------------------------------------------------------------------
    # Check 2: MCP Endpoint (0-25 points)
    # -------------------------------------------------------------------------

    async def validate_mcp(self, url: str) -> CheckResult:
        """
        Validate the agent's MCP endpoint.

        Scoring:
            - Reachable and returns valid JSON-RPC response: 10 pts
            - Returns tools array:                          5 pts
            - Has >= 5 tools:                               5 pts (scaled)
            - Tools have proper schemas:                    3 pts
            - Response time < 3s:                           2 pts
        """
        result = CheckResult(check_name="mcp", score=0, max_score=25, passed=False)

        # Try MCP discovery paths
        mcp_urls = [
            f"{url}/mcp/v1",
            f"{url}/mcp",
        ]

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {},
        }

        tools_data = None
        start = time.monotonic()

        async with httpx.AsyncClient(
            timeout=MCP_TIMEOUT,
            follow_redirects=True,
            verify=True,
        ) as client:
            for mcp_url in mcp_urls:
                try:
                    resp = await client.post(
                        mcp_url,
                        json=payload,
                        headers={
                            "Content-Type": "application/json",
                            "Accept": "application/json",
                            "User-Agent": "GanjaMon-Validator/1.0",
                        },
                    )
                    latency = (time.monotonic() - start) * 1000
                    result.latency_ms = latency

                    if resp.status_code == 200:
                        body = resp.json()

                        # Check for JSON-RPC error
                        if "error" in body and body["error"]:
                            result.warnings.append(
                                f"MCP returned error: {body['error'].get('message', '')}"
                            )
                            continue

                        # Extract tools from result
                        rpc_result = body.get("result", {})
                        if isinstance(rpc_result, dict):
                            tools_data = rpc_result.get("tools", [])
                        elif isinstance(rpc_result, list):
                            tools_data = rpc_result

                        if tools_data is not None:
                            result.details["resolved_url"] = mcp_url
                            break

                    # Also try GET (some MCP endpoints return tools on GET)
                    resp_get = await client.get(
                        mcp_url,
                        headers={"Accept": "application/json", "User-Agent": "GanjaMon-Validator/1.0"},
                    )
                    if resp_get.status_code == 200:
                        body = resp_get.json()
                        if "tools" in body:
                            tools_data = body["tools"]
                            result.details["resolved_url"] = mcp_url
                            result.details["discovery_method"] = "GET"
                            break

                except httpx.TimeoutException:
                    result.errors.append(f"Timeout calling {mcp_url}")
                except Exception as e:
                    result.errors.append(f"Error calling {mcp_url}: {str(e)[:100]}")

        if tools_data is None:
            result.errors.append("No valid MCP tools/list response found")
            return result

        # +10: Reachable and returns valid JSON-RPC
        result.score += 10
        result.passed = True

        # +5: Returns a tools array
        if isinstance(tools_data, list):
            result.score += 5
            result.details["tool_count"] = len(tools_data)

            # +5: Scaled by tool count (1 pt per 5 tools, max 5)
            tool_pts = min(len(tools_data) // 5, 5) if len(tools_data) >= 5 else min(len(tools_data), 4)
            result.score += tool_pts

            # +3: Tools have proper input schemas
            tools_with_schema = sum(
                1 for t in tools_data
                if isinstance(t, dict) and (
                    "inputSchema" in t or "input_schema" in t or "parameters" in t
                )
            )
            if tools_with_schema > 0:
                schema_ratio = tools_with_schema / max(len(tools_data), 1)
                result.score += min(int(schema_ratio * 3), 3)
                result.details["tools_with_schema"] = tools_with_schema
            else:
                result.warnings.append("No tools have input schemas defined")

            # Log tool names
            tool_names = [
                t.get("name", "?") for t in tools_data[:20] if isinstance(t, dict)
            ]
            result.details["tool_names"] = tool_names
        else:
            result.warnings.append("tools/list result is not an array")

        # Response time
        if result.latency_ms < 3000:
            result.score += 2
        else:
            result.warnings.append(f"Slow MCP response: {result.latency_ms:.0f}ms")

        result.details["latency_ms"] = round(result.latency_ms, 1)
        return result

    # -------------------------------------------------------------------------
    # Check 3: x402 Compliance (0-15 points)
    # -------------------------------------------------------------------------

    async def validate_x402(self, url: str) -> CheckResult:
        """
        Validate x402 payment protocol compliance.

        Scoring:
            - Agent card declares x402 support:             5 pts
            - Returns 402 with payment requirements:        5 pts
            - Has X-Payment-Address or payTo field:         3 pts
            - Has pricing info (priceUSD, amount):          2 pts
        """
        result = CheckResult(check_name="x402", score=0, max_score=15, passed=False)

        start = time.monotonic()

        async with httpx.AsyncClient(
            timeout=X402_TIMEOUT,
            follow_redirects=True,
            verify=True,
        ) as client:
            # Step 1: Check agent card for x402 declaration
            card_urls = [
                f"{url}/.well-known/agent-card.json",
                f"{url}/a2a/v1",
            ]

            x402_declared = False
            pricing_info = None

            for card_url in card_urls:
                try:
                    resp = await client.get(
                        card_url,
                        headers={"Accept": "application/json", "User-Agent": "GanjaMon-Validator/1.0"},
                    )
                    if resp.status_code == 200:
                        card = resp.json()

                        # Check capabilities
                        caps = card.get("capabilities", {})
                        if caps.get("x402Payments") or caps.get("x402"):
                            x402_declared = True

                        # Check security schemes
                        schemes = card.get("securitySchemes", {})
                        if "x402" in schemes:
                            x402_declared = True
                            pricing_info = schemes["x402"]

                        # Check top-level x402 field
                        if "x402" in card:
                            x402_declared = True
                            pricing_info = card["x402"]

                        break
                except Exception:
                    continue

            if x402_declared:
                result.score += 5
                result.passed = True
                result.details["declared"] = True

                if pricing_info:
                    result.details["pricing"] = pricing_info
            else:
                result.details["declared"] = False
                result.warnings.append("Agent card does not declare x402 support")

            # Step 2: Check x402-pricing.json
            try:
                pricing_resp = await client.get(
                    f"{url}/.well-known/x402-pricing.json",
                    headers={"Accept": "application/json", "User-Agent": "GanjaMon-Validator/1.0"},
                )
                if pricing_resp.status_code == 200:
                    pricing_data = pricing_resp.json()
                    result.details["pricing_endpoint"] = True
                    if not pricing_info:
                        pricing_info = pricing_data
                    if not x402_declared:
                        result.score += 3
                        result.passed = True
                        result.details["declared_via_pricing"] = True
                else:
                    result.details["pricing_endpoint"] = False
            except Exception:
                result.details["pricing_endpoint"] = False

            # Step 3: Try to trigger a 402 by POSTing to A2A without payment
            a2a_urls = [f"{url}/a2a/v1", url]

            for a2a_url in a2a_urls:
                try:
                    resp = await client.post(
                        a2a_url,
                        json={
                            "jsonrpc": "2.0",
                            "id": "x402-probe",
                            "method": "message/send",
                            "params": {"skill": "probe", "message": "x402 compliance check"},
                        },
                        headers={
                            "Content-Type": "application/json",
                            "User-Agent": "GanjaMon-Validator/1.0",
                        },
                    )

                    if resp.status_code == 402:
                        result.score += 5
                        result.passed = True
                        result.details["returns_402"] = True

                        # Check for payment headers / body
                        pay_addr = (
                            resp.headers.get("X-Payment-Address")
                            or resp.headers.get("x-payment-address")
                        )
                        pay_amount = (
                            resp.headers.get("X-Payment-Amount")
                            or resp.headers.get("x-payment-amount")
                        )

                        body_data = {}
                        try:
                            body_data = resp.json()
                        except Exception:
                            pass

                        # Check body for payment info (JSON-RPC error.data)
                        error_data = body_data.get("error", {}).get("data", {})
                        pay_to_body = error_data.get("payTo", error_data.get("pay_to", ""))
                        price_body = error_data.get("priceUSD", error_data.get("price", ""))

                        has_address = bool(pay_addr or pay_to_body)
                        has_pricing = bool(pay_amount or price_body)

                        if has_address:
                            result.score += 3
                            result.details["payment_address"] = pay_addr or pay_to_body
                        else:
                            result.warnings.append("402 response missing payment address")

                        if has_pricing:
                            result.score += 2
                            result.details["payment_amount"] = pay_amount or price_body
                        else:
                            result.warnings.append("402 response missing pricing info")

                        break

                    elif resp.status_code == 200:
                        # Agent doesn't require payment -- check if it at least declares it
                        result.details["returns_402"] = False
                        result.warnings.append(
                            "Agent accepts requests without payment (x402 not enforced)"
                        )
                        # Still give partial credit if declared
                        break

                except Exception:
                    continue

        result.latency_ms = (time.monotonic() - start) * 1000
        result.details["latency_ms"] = round(result.latency_ms, 1)
        return result

    # -------------------------------------------------------------------------
    # Check 4: Infrastructure Basics (0-20 points)
    # -------------------------------------------------------------------------

    async def validate_infra(self, url: str) -> CheckResult:
        """
        Validate basic infrastructure health.

        Scoring:
            - HEAD request returns 2xx:         5 pts
            - Uses HTTPS with valid TLS:        5 pts
            - Latency < 1s:                     5 pts (scaled)
            - Proper CORS headers:              3 pts
            - Content-Type header present:      2 pts
        """
        result = CheckResult(check_name="infra", score=0, max_score=20, passed=False)

        parsed = urlparse(url)
        start = time.monotonic()

        async with httpx.AsyncClient(
            timeout=INFRA_TIMEOUT,
            follow_redirects=True,
            verify=True,
        ) as client:
            # HEAD request for liveness
            try:
                resp = await client.head(
                    url,
                    headers={"User-Agent": "GanjaMon-Validator/1.0"},
                )
                latency = (time.monotonic() - start) * 1000
                result.latency_ms = latency

                if 200 <= resp.status_code < 400:
                    result.score += 5
                    result.passed = True
                    result.details["status_code"] = resp.status_code
                else:
                    result.warnings.append(f"HEAD returned {resp.status_code}")
                    result.details["status_code"] = resp.status_code

                    # Try GET as fallback (some servers reject HEAD)
                    try:
                        resp_get = await client.get(
                            url,
                            headers={"User-Agent": "GanjaMon-Validator/1.0"},
                        )
                        if 200 <= resp_get.status_code < 400:
                            result.score += 5
                            result.passed = True
                            result.details["status_code"] = resp_get.status_code
                            result.details["liveness_method"] = "GET"
                            resp = resp_get
                    except Exception:
                        pass

            except httpx.TimeoutException:
                result.errors.append("Liveness check timed out")
                return result
            except Exception as e:
                result.errors.append(f"Liveness check failed: {str(e)[:100]}")
                return result

            # TLS check
            if parsed.scheme == "https":
                result.score += 5
                result.details["tls"] = True

                # Check TLS version/cert details
                try:
                    ctx = ssl.create_default_context()
                    import socket
                    hostname = parsed.hostname
                    port = parsed.port or 443
                    with ctx.wrap_socket(
                        socket.create_connection((hostname, port), timeout=5),
                        server_hostname=hostname,
                    ) as ssock:
                        cert = ssock.getpeercert()
                        tls_version = ssock.version()
                        result.details["tls_version"] = tls_version
                        if cert:
                            issuer = dict(x[0] for x in cert.get("issuer", []))
                            result.details["cert_issuer"] = issuer.get(
                                "organizationName", issuer.get("commonName", "unknown")
                            )
                            not_after = cert.get("notAfter", "")
                            result.details["cert_expires"] = not_after
                except Exception as e:
                    result.warnings.append(f"TLS inspection warning: {str(e)[:80]}")
                    result.details["tls_inspection_error"] = True
            else:
                result.details["tls"] = False
                result.warnings.append("Not using HTTPS")

            # Latency scoring (0-5 pts scaled)
            if result.latency_ms < 500:
                result.score += 5
            elif result.latency_ms < 1000:
                result.score += 4
            elif result.latency_ms < 2000:
                result.score += 3
            elif result.latency_ms < 5000:
                result.score += 1
            else:
                result.warnings.append(f"High latency: {result.latency_ms:.0f}ms")

            # CORS headers check
            cors_origin = resp.headers.get("access-control-allow-origin", "")
            cors_methods = resp.headers.get("access-control-allow-methods", "")
            if cors_origin:
                result.score += 2
                result.details["cors_origin"] = cors_origin
                if cors_methods:
                    result.score += 1
                    result.details["cors_methods"] = cors_methods
            else:
                result.warnings.append("No CORS headers present")

            # Content-Type header
            content_type = resp.headers.get("content-type", "")
            if content_type:
                result.score += 2
                result.details["content_type"] = content_type
            else:
                result.warnings.append("No Content-Type header")

        result.details["latency_ms"] = round(result.latency_ms, 1)
        return result

    # -------------------------------------------------------------------------
    # Check 5: 8004scan Registration (0-10 points)
    # -------------------------------------------------------------------------

    async def validate_registration(
        self,
        agent_id: Optional[int] = None,
        chain: str = "monad",
    ) -> CheckResult:
        """
        Validate agent's registration on 8004scan.

        Scoring:
            - Found on registry:               5 pts
            - Trust score >= 50:                3 pts (scaled)
            - Has on-chain reputation data:     2 pts
        """
        result = CheckResult(check_name="registration", score=0, max_score=10, passed=False)

        if agent_id is None:
            result.warnings.append(
                "No agent_id provided -- cannot check 8004scan registration"
            )
            result.details["skipped"] = True
            return result

        start = time.monotonic()

        try:
            agent_entry = await self.registry.get_agent(agent_id, chain)
            result.latency_ms = (time.monotonic() - start) * 1000

            if agent_entry is None:
                result.errors.append(
                    f"Agent #{agent_id} not found on {chain} in 8004scan"
                )
                return result

            # +5: Found on registry
            result.score += 5
            result.passed = True
            result.details["agent_id"] = agent_entry.agent_id
            result.details["name"] = agent_entry.name
            result.details["chain"] = agent_entry.chain
            result.details["owner"] = agent_entry.owner

            # Trust score (0-3 pts scaled)
            trust = agent_entry.trust_score
            result.details["trust_score"] = trust
            if trust >= 80:
                result.score += 3
            elif trust >= 60:
                result.score += 2
            elif trust >= 50:
                result.score += 1
            else:
                result.warnings.append(f"Low trust score: {trust}")

            # On-chain data presence
            has_uri = bool(agent_entry.agent_uri)
            has_endpoints = bool(agent_entry.a2a_url or agent_entry.mcp_url)
            if has_uri or has_endpoints:
                result.score += 2
                result.details["has_agent_uri"] = has_uri
                result.details["has_endpoints"] = has_endpoints
            else:
                result.warnings.append("No on-chain URI or endpoint data found")

        except Exception as e:
            result.latency_ms = (time.monotonic() - start) * 1000
            result.errors.append(f"Registry check failed: {str(e)[:100]}")

        result.details["latency_ms"] = round(result.latency_ms, 1)
        return result


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_instance: Optional[AgentValidator] = None


def get_validator() -> AgentValidator:
    """Get or create the global AgentValidator instance."""
    global _instance
    if _instance is None:
        _instance = AgentValidator()
    return _instance
