from fastapi import HTTPException, Request

from .state import state


def limiter(scope: str, limit: int = 20, window: int = 60):
    def dependency(request: Request) -> None:
        ip = request.client.host if request.client else "unknown"
        if not state.rate(f"{scope}:{ip}", limit, window):
            raise HTTPException(
                status_code=429,
                detail={"code": "RATE_LIMITED", "message": "请求过于频繁，请稍后再试"},
                headers={"Retry-After": str(window)},
            )

    return dependency
