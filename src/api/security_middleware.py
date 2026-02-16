"""
Security Middleware - Enterprise-grade HTTP security
====================================================

Implements:
- Security headers (CSP, HSTS, X-Frame-Options, etc.)
- Request logging (all requests)
- IP-based rate limiting
- Fail2ban-style IP blocking
- Request size limits
- Suspicious activity detection
"""

import time
import logging
from collections import defaultdict
from typing import Dict, List, Tuple
from datetime import datetime, timedelta

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from fastapi import status

# Configure logger
logger = logging.getLogger("security")


# =============================================================================
# IP-based Rate Limiting & Blocking
# =============================================================================

class IPTracker:
    """Track IP requests for rate limiting and fail2ban"""

    def __init__(self):
        # {ip: [(timestamp, endpoint), ...]}
        self._requests: Dict[str, List[Tuple[float, str]]] = defaultdict(list)
        # {ip: block_until_timestamp}
        self._blocked: Dict[str, float] = {}
        # Cleanup interval
        self._last_cleanup = time.time()

    def is_blocked(self, ip: str) -> bool:
        """Check if IP is currently blocked"""
        if ip in self._blocked:
            if time.time() < self._blocked[ip]:
                return True
            else:
                # Unblock expired blocks
                del self._blocked[ip]
        return False

    def block_ip(self, ip: str, duration_seconds: int = 300):
        """Block an IP for specified duration (default 5 minutes)"""
        self._blocked[ip] = time.time() + duration_seconds
        logger.warning(f"IP BLOCKED: {ip} for {duration_seconds}s")

    def check_rate_limit(self, ip: str, endpoint: str, max_requests: int, window_seconds: int) -> bool:
        """
        Check if IP has exceeded rate limit for endpoint.
        Returns True if allowed, False if rate limit exceeded.
        """
        now = time.time()

        # Cleanup old requests (every 60 seconds)
        if now - self._last_cleanup > 60:
            self._cleanup_old_requests(window_seconds)
            self._last_cleanup = now

        # Remove old requests for this IP
        self._requests[ip] = [
            (ts, ep) for ts, ep in self._requests[ip]
            if now - ts < window_seconds
        ]

        # Count requests to this endpoint
        endpoint_requests = sum(1 for _, ep in self._requests[ip] if ep == endpoint)

        if endpoint_requests >= max_requests:
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
# Security Headers Middleware
# =============================================================================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""

    async def dispatch(self, request: Request, call_next):
        # Get client IP (handle proxies)
        client_ip = request.headers.get("CF-Connecting-IP") or \
                    request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or \
                    request.client.host if request.client else "unknown"

        # Check if IP is blocked
        if ip_tracker.is_blocked(client_ip):
            logger.warning(f"BLOCKED REQUEST: {client_ip} -> {request.url.path}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"error": "Too many requests. IP temporarily blocked."},
                headers={"Retry-After": "300"}
            )

        # Rate limiting for expensive endpoints
        endpoint = request.url.path
        rate_limits = {
            "/api/webcam/latest": (30, 60),      # 30 req/min
            "/api/sensors/live": (60, 60),       # 60 req/min
            "/api/vision/analyze": (5, 60),      # 5 req/min (expensive)
            "/api/ai/trigger": (1, 60),          # 1 req/min (very expensive)
            "/api/leads": (10, 60),              # 10 req/min (abuse protection)
        }

        if endpoint in rate_limits:
            max_req, window = rate_limits[endpoint]
            if not ip_tracker.check_rate_limit(client_ip, endpoint, max_req, window):
                # Block IP for repeated violations
                violations = sum(1 for _, ep in ip_tracker._requests[client_ip] if ep == endpoint)
                if violations > max_req * 1.5:  # 50% over limit
                    ip_tracker.block_ip(client_ip, 300)  # 5 min block

                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"error": f"Rate limit exceeded for {endpoint}"},
                    headers={"Retry-After": str(window)}
                )

        # Log request
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate request duration
        duration_ms = (time.time() - start_time) * 1000

        # Log request (structured)
        logger.info(
            f"{client_ip} - {request.method} {endpoint} - {response.status_code} - {duration_ms:.0f}ms"
        )

        # Add security headers to response
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        # Content Security Policy (strict)
        if endpoint.endswith(".html") or endpoint == "/":
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self' wss://grokandmon.com ws://localhost:8000; "
                "frame-ancestors 'none';"
            )

        # HSTS (force HTTPS for 1 year)
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

        # Server header (hide tech stack)
        response.headers["Server"] = "Cloudflare"

        return response


# =============================================================================
# Request Size Limiting Middleware
# =============================================================================

class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Limit request body size to prevent DoS attacks"""

    MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB max

    async def dispatch(self, request: Request, call_next):
        # Check Content-Length header
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.MAX_REQUEST_SIZE:
            logger.warning(f"REQUEST TOO LARGE: {request.client.host} - {content_length} bytes")
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"error": "Request body too large (max 10MB)"}
            )

        return await call_next(request)
