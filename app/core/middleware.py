import time
import uuid
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.core.context import set_current_ip

logger = logging.getLogger("demand_manager")


def register_middlewares(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


async def logging_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    start = time.perf_counter()

    ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else None)
    set_current_ip(ip)

    response = await call_next(request)

    duration = (time.perf_counter() - start) * 1000
    logger.info(
        f"[{request_id}] {request.method} {request.url.path} "
        f"→ {response.status_code} ({duration:.1f}ms)"
    )
    response.headers["X-Request-ID"] = request_id
    return response