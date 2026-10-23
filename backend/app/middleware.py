import hmac
import time
import uuid

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from .config import ALLOW_DEV_AUTH, CSRF_COOKIE, GLOBAL_RATE_LIMIT, SESSION_COOKIE
from .context import request_id as request_id_ctx
from .context import request_ip as request_ip_ctx
from .state import state

UNSAFE = {"POST", "PUT", "PATCH", "DELETE"}
CSRF_EXEMPT = ("/api/auth/", "/api/wecom/", "/api/internal/", "/api/alerts", "/api/health", "/api/ready", "/api/metrics")


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if (
            request.method in UNSAFE
            and path.startswith("/api")
            and not path.startswith(CSRF_EXEMPT)
            and request.cookies.get(SESSION_COOKIE)
            and not (ALLOW_DEV_AUTH and request.headers.get("X-User"))
        ):
            token = request.headers.get("X-CSRF-Token", "")
            cookie = request.cookies.get(CSRF_COOKIE, "")
            if not token or not cookie or not hmac.compare_digest(token, cookie):
                return JSONResponse(
                    status_code=403,
                    content={"detail": {"code": "CSRF", "message": "CSRF 校验失败"}},
                )
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path.startswith("/api") and not path.startswith(("/api/health", "/api/ready", "/api/metrics")):
            ip = request.client.host if request.client else "unknown"
            if not state.rate(f"global:{ip}", GLOBAL_RATE_LIMIT, 60):
                return JSONResponse(
                    status_code=429,
                    content={"detail": {"code": "RATE_LIMITED", "message": "请求过于频繁"}},
                    headers={"Retry-After": "60"},
                )
        return await call_next(request)


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-Id") or uuid.uuid4().hex
        ip = request.client.host if request.client else "unknown"
        ip_token = request_ip_ctx.set(ip)
        id_token = request_id_ctx.set(request_id)
        started = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            request_ip_ctx.reset(ip_token)
            request_id_ctx.reset(id_token)
        elapsed = time.perf_counter() - started
        response.headers["X-Request-Id"] = request_id
        state.record_request(request.method, request.url.path, response.status_code)
        state.add_duration(elapsed)
        return response
