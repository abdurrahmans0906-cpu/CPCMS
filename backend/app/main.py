import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.scheduler import start_scheduler, stop_scheduler

from app.routers.auth import router as auth_router
from app.routers.courses import router as courses_router
from app.routers.projects import router as projects_router
from app.routers.teams import router as teams_router
from app.routers.proposals import router as proposals_router
from app.routers.cis import router as cis_router
from app.routers.baselines import router as baselines_router
from app.routers.change_requests import router as change_requests_router
from app.routers.repository import router as repository_router
from app.routers.progress import router as progress_router
from app.routers.submissions import router as submissions_router
from app.routers.evaluations import router as evaluations_router
from app.routers.releases import router as releases_router
from app.routers.reports import router as reports_router
from app.routers.notifications import router as notifications_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure upload directory exists and start scheduler
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    start_scheduler()
    yield
    # Shutdown
    stop_scheduler()


app = FastAPI(
    title="CPCMS — Course Project Configuration and Management System",
    description="Internal University Course Project SCM & Configuration Management System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Consistent error handling: { detail: "...", code: ... }
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": str(exc.detail), "code": exc.status_code}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    first_err = exc.errors()[0] if exc.errors() else {"msg": "Validation error"}
    loc_str = " -> ".join([str(l) for l in first_err.get("loc", [])])
    detail_msg = f"{loc_str}: {first_err.get('msg', 'Invalid input')}" if loc_str else first_err.get("msg", "Invalid input")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": detail_msg, "code": 422}
    )


# Root and health check
@app.get("/api/v1/health", tags=["Health"])
def health_check():
    return {"status": "healthy", "app": "CPCMS", "version": "1.0.0"}


# Mount all routers under /api/v1
api_v1_prefix = "/api/v1"
app.include_router(auth_router, prefix=api_v1_prefix)
app.include_router(courses_router, prefix=api_v1_prefix)
app.include_router(projects_router, prefix=api_v1_prefix)
app.include_router(teams_router, prefix=api_v1_prefix)
app.include_router(proposals_router, prefix=api_v1_prefix)
app.include_router(cis_router, prefix=api_v1_prefix)
app.include_router(baselines_router, prefix=api_v1_prefix)
app.include_router(change_requests_router, prefix=api_v1_prefix)
app.include_router(repository_router, prefix=api_v1_prefix)
app.include_router(progress_router, prefix=api_v1_prefix)
app.include_router(submissions_router, prefix=api_v1_prefix)
app.include_router(evaluations_router, prefix=api_v1_prefix)
app.include_router(releases_router, prefix=api_v1_prefix)
app.include_router(reports_router, prefix=api_v1_prefix)
app.include_router(notifications_router, prefix=api_v1_prefix)
