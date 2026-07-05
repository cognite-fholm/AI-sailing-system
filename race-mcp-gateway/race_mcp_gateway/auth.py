from __future__ import annotations

import os
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class BearerAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, token_env: str = "RACE_MCP_API_KEY") -> None:
        super().__init__(app)
        self._token_env = token_env

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path == "/health":
            return await call_next(request)
        expected = os.environ.get(self._token_env, "").strip()
        if not expected:
            return await call_next(request)
        auth = request.headers.get("authorization", "")
        if auth != f"Bearer {expected}":
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        return await call_next(request)
