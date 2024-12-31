from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.activities import router as activities_router
from src.api.activity_types import router as activity_types_router, register_activities
from src.api.workflows import router as workflows_router
from src.database.connection import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI application."""
    # Startup: Initialize database and register activities
    await init_db()
    register_activities()
    yield
    # Shutdown: Clean up if needed
    pass


app = FastAPI(
    title="AI Platform API",
    description="API for managing AI platform activities and workflows",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(activity_types_router)
app.include_router(activities_router)
app.include_router(workflows_router)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint returning API information."""
    return {
        "name": "AI Platform API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }
