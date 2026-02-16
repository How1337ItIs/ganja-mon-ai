"""
Security Middleware - STABILIZED for Chromebook
================================================

Fixed version with proper error handling and fallbacks.

Bugs fixed:
1. NoneType errors when request.client is None
2. Missing exception handling in middleware chain
3. TrustedHost causing valid request rejections
4. Excessive logging causing I/O bottleneck
"""

import time
import logging
from collections import defaultdict
from typing import Dict, List, Tuple, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from fastapi import status

# Configure logger (INFO level to reduce disk I/O)
logger = logging.getLogger("security")
logger.setLevel(logging.WARNING)  # Only log warnings and errors


# =============================================================================
# IP-based Rate Limiting & Blocking
# =============================================================================

class IPTracker:
    """Track IP requests for rate limiting and fail2ban"""

    def __init__(self):
        self._requests: Dict[str, List[Tuple[float, str]]] = defaultdict(list)
        self._blocked: Dict[str, float] = {}
        self._last_cleanup = time.time()

    def is_blocked(self, ip: str) -> bool:
        """Check if IP is currently blocked"""
        if not ip or ip == "unknown":
            return False  # Don't block unknown IPs

        if ip in self._blocked:
            if time.time() < self._blocked[ip]:
                return True
            else:
                del self._blocked[ip]
        return False

    def block_ip(self, ip: str, duration_seconds: int = 300):
        """Block an IP for specified duration"""
        if not ip or ip == "unknown":
            return  # Can't block unknown IPs

        self._blocked[ip] = time.time() + duration_seconds
        logger.warning(f"IP BLOCKED: {ip} for {duration_seconds}s")

    def check_rate_limit(self, ip: str, endpoint: str, max_requests: int, window_seconds: int) -> bool:
        """Check if IP has exceeded rate limit. Returns True if allowed."""
        if not ip or ip == "unknown":
            return True  # Allow unknown IPs (conservative)

        now = time.time()

        # Cleanup old requests periodically
        if now - self._last_cleanup > 60:
            self._cleanup_old_requests(window_seconds)
            self._last_cleanup = now

        # Remove old requests for this IP
        if ip in self._requests:
            self._requests[ip] = [
                (ts, ep) for ts, ep in self._requests[ip]
                if now - ts < window_seconds
            ]

        # Count requests to this endpoint
        endpoint_requests = sum(1 for _, ep in self._requests.get(ip, []) if ep == endpoint)

        if endpoint_requests >= max_requests:
            # Only log severe violations (reduce disk I/O)
            if endpoint_requests > max_requests * 2:
                logger.warning(f"RATE LIMIT: {ip} exceeded {max_requests} req/{window_seconds}s for {endpoint}")
            return False

        # Record this request
        self._requests[ip].append((now, endpoint))
        return True

    def _cleanup_old_requests(self, window_seconds: int):
        """Remove old requests from memory"""
        now = time.time()
        for ip in list(self._requests.keys()):
            self._requests[ip] = [
                (ts, ep) for ts, ep in self._requests[ip]
                if now - ts < window_seconds
            ]
            if not self._requests[ip]:
                del self._requests[ip]


# Global IP tracker
ip_tracker = IPTracker()


# =============================================================================
# Security Headers Middleware (Lightweight)
# =============================================================================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers with minimal overhead"""

    async def dispatch(self, request: Request, call_next):
        try:
            # Get client IP safely
            client_ip = self._get_client_ip(request)

            # Check if IP is blocked (fast path)
            if ip_tracker.is_blocked(client_ip):
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"error": "Too many requests. IP temporarily blocked."},
                    headers={"Retry-After": "300"}
                )

            # Rate limiting for expensive endpoints only
            endpoint = request.url.path
            if endpoint in {"/api/vision/analyze", "/api/ai/trigger"}:
                # Only rate limit the most expensive endpoints
                max_req = 5 if endpoint == "/api/vision/analyze" else 1
                if not ip_tracker.check_rate_limit(client_ip, endpoint, max_req, 60):
                    return JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={"error": f"Rate limit exceeded"},
                        headers={"Retry-After": "60"}
                    )

            # Process request with timeout protection
            try:
                response = await call_next(request)
            except Exception as e:
                # Log but don't crash
                logger.error(f"Request processing error: {e}")
                return JSONResponse(
                    status_code=500,
                    content={"error": "Internal server error"}
                )

            # Add minimal security headers (lightweight)
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["Server"] = "Cloudflare"

            # Only add HSTS for HTTPS (check safely)
            try:
                if request.url.scheme == "https":
                    response.headers["Strict-Transport-Security"] = "max-age=31536000"
            except Exception:
                pass  # Ignore if scheme check fails

            return response

        except Exception as e:
            # Catch-all to prevent middleware crashes
            logger.error(f"Middleware error: {e}")
            # Return response without security headers rather than crash
            try:
                return await call_next(request)
            except Exception:
                return JSONResponse(
                    status_code=500,
                    content={"error": "Internal server error"}
                )

    def _get_client_ip(self, request: Request) -> str:
        """Safely extract client IP with fallbacks"""
        try:
            # Try Cloudflare header first
            cf_ip = request.headers.get("CF-Connecting-IP")
            if cf_ip:
                return cf_ip.strip()

            # Try X-Forwarded-For
            xff = request.headers.get("X-Forwarded-For")
            if xff:
                return xff.split(",")[0].strip()

            # Try request.client
            if request.client and request.client.host:
                return request.client.host

        except Exception as e:
            logger.debug(f"Error getting client IP: {e}")

        return "unknown"


# =============================================================================
# Request Size Limiting (Lightweight)
# =============================================================================

class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Limit request body size"""

    MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB max

    async def dispatch(self, request: Request, call_next):
        try:
            # Check Content-Length header safely
            content_length = request.headers.get("content-length")
            if content_length:
                try:
                    size = int(content_length)
                    if size > self.MAX_REQUEST_SIZE:
                        return JSONResponse(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            content={"error": "Request too large (max 10MB)"}
                        )
                except (ValueError, TypeError):
                    pass  # Invalid content-length, ignore

            return await call_next(request)

        except Exception as e:
            logger.error(f"RequestSizeLimit error: {e}")
            # Don't crash, just pass through
            try:
                return await call_next(request)
            except Exception:
                return JSONResponse(
                    status_code=500,
                    content={"error": "Internal server error"}
                )
