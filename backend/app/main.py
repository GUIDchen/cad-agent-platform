from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import ai, alerts, approvals, audit, auth, bom, comments, drawings, generation, internal, jobs, notifications, projects, rag, stats, system, users, versions, wecom
from .api.spa import mount_spa
from .config import APP_VERSION
from .db import init_db
from .middleware import CSRFMiddleware, RateLimitMiddleware, RequestContextMiddleware, SecurityHeadersMiddleware
from .security import validate_config


@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_config()
    init_db()
    yield


app = FastAPI(title="CAD Agent Platform", version=APP_VERSION, lifespan=lifespan)

app.add_middleware(RequestContextMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CSRFMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (
    auth.router,
    ai.router,
    projects.router,
    drawings.router,
    comments.router,
    generation.router,
    bom.router,
    versions.router,
    approvals.router,
    notifications.router,
    rag.router,
    jobs.router,
    audit.router,
    stats.router,
    users.router,
    wecom.router,
    alerts.router,
    system.router,
    internal.router,
):
    app.include_router(router, prefix="/api")

mount_spa(app)
