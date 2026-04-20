"""
API Key authentication for public-facing endpoints.
Uses X-API-Key header with timing-safe comparison.
"""

import hmac
import time
from collections import defaultdict
from typing import Optional

from fastapi import Header, HTTPException, Request

from app.config import settings


# ===== Rate Limiter (in-memory, per-IP) =====
class RateLimiter:
    """Simple sliding-window rate limiter."""

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        cutoff = now - self.window_seconds
        # Prune old entries
        self._hits[key] = [t for t in self._hits[key] if t > cutoff]
        if len(self._hits[key]) >= self.max_requests:
            return False
        self._hits[key].append(now)
        return True

    def remaining(self, key: str) -> int:
        now = time.time()
        cutoff = now - self.window_seconds
        self._hits[key] = [t for t in self._hits[key] if t > cutoff]
        return max(0, self.max_requests - len(self._hits[key]))


# Global rate limiter: 60 requests per minute per IP
rate_limiter = RateLimiter(max_requests=60, window_seconds=60)


# ===== API Key Dependency =====
async def require_api_key(
    request: Request,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    """
    Validates the API key from the X-API-Key header.
    - Returns 401 if no key is provided or key is empty.
    - Returns 403 if the key doesn't match.
    - Returns 429 if rate limit exceeded.
    """
    configured_key = settings.OMNISTATUS_API_KEY

    # Ensure the server has a key configured
    if not configured_key:
        raise HTTPException(
            status_code=500,
            detail="API key not configured on server. Set OMNISTATUS_API_KEY in .env",
        )

    # Check presence
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Provide X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Timing-safe comparison to prevent timing attacks
    if not hmac.compare_digest(x_api_key, configured_key):
        raise HTTPException(
            status_code=403,
            detail="Invalid API key.",
        )

    # Rate limiting by client IP
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Max 60 requests/min.",
            headers={"Retry-After": "60"},
        )

    return True
