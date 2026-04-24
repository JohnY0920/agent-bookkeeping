from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.webhooks import router as webhooks_router
from app.api.engagements import router as engagements_router
from app.api.documents import router as documents_router
from app.api.checklist import router as checklist_router
from app.api.review import router as review_router
from app.api.gl import router as gl_router
from app.api.workpapers import router as workpapers_router
from app.api.plan import router as plan_router
from app.api.transactions import router as transactions_router
from app.api.xero_oauth import router as xero_router
from app.tools.db import get_pool, close_pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    await get_pool()
    yield
    await close_pool()


app = FastAPI(
    title="Agent Bookkeeping — Processing Service",
    description=(
        "AI-powered bookkeeping platform for Canadian accounting firms. "
        "Handles document processing, transaction categorization, reconciliation, "
        "year-end adjustments, and tax preparation via specialized Claude agents."
    ),
    version="0.2.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict to frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(webhooks_router)
app.include_router(engagements_router, prefix="/api", tags=["engagements"])
app.include_router(documents_router, prefix="/api", tags=["documents"])
app.include_router(checklist_router, prefix="/api", tags=["checklist"])
app.include_router(review_router, prefix="/api", tags=["review"])
app.include_router(gl_router, prefix="/api", tags=["gl"])
app.include_router(workpapers_router, prefix="/api", tags=["workpapers"])
app.include_router(plan_router, prefix="/api", tags=["plan"])
app.include_router(transactions_router, prefix="/api", tags=["transactions"])
app.include_router(xero_router, prefix="/api", tags=["xero"])
