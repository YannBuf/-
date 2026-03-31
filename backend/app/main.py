import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
from app.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)
from app.api.auth import router as auth_router
from app.api.datasource import router as datasource_router
from app.api.analytics import router as analytics_router
from app.api.conversation import router as conversation_router
from app.api.report import router as report_router
from app.database import engine, Base
from app.models.user import User
from app.models.datasource import DataSource
from app.models.audit import AuditLog

settings = get_settings()


async def init_db():
    """Create all database tables on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables
    await init_db()
    yield
    # Shutdown: dispose engine
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://0.0.0.0:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code,
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "message": "Validation error",
            "details": exc.errors(),
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    # Log the full error for debugging
    logger.exception(f"[UNHANDLED ERROR] {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": str(exc) if settings.DEBUG else "Internal server error",
            "status_code": 500,
        }
    )


# Health check
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "app": settings.APP_NAME}

# Auth routes
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])

# DataSource routes
app.include_router(datasource_router, prefix="/api/datasources", tags=["datasources"])

# Analytics routes
app.include_router(analytics_router, prefix="/api/analytics", tags=["analytics"])

# Conversation routes
app.include_router(conversation_router, prefix="/api/conversation", tags=["conversation"])

# Report routes
app.include_router(report_router, prefix="/api/reports", tags=["reports"])
