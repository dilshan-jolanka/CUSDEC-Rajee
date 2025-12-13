"""
CV Analyzer AI - FastAPI Main Application

This is the main entry point for the CV Analyzer AI system.
It provides AI-powered CV analysis capabilities through REST API endpoints.
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager
import uvicorn
from typing import Dict, Any

from app.config.settings import get_settings
from app.api import cv_analyzer, auth, dashboard
from app.config.database import init_db

# Initialize security
security = HTTPBearer()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    print("Starting CV Analyzer AI...")
    await init_db()
    print("Database initialized")
    
    yield
    
    # Shutdown
    print("Shutting down CV Analyzer AI...")


# Create FastAPI application
app = FastAPI(
    title="CV Analyzer AI",
    description="AI-powered CV analysis system for automated resume screening and job matching",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.get("/", response_model=Dict[str, Any])
async def root():
    """Root endpoint providing API information"""
    return {
        "message": "Welcome to CV Analyzer AI",
        "version": "1.0.0",
        "status": "operational",
        "documentation": "/docs",
        "features": [
            "CV parsing and analysis",
            "Skill extraction and matching",
            "Experience scoring",
            "Job compatibility assessment",
            "Batch processing"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "cv-analyzer-ai"}


# Include API routers
app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["Authentication"]
)

app.include_router(
    cv_analyzer.router,
    prefix="/api/v1",
    tags=["CV Analysis"]
)

app.include_router(
    dashboard.router,
    prefix="/api/v1/dashboard",
    tags=["Dashboard"]
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return {
        "error": exc.detail,
        "status_code": exc.status_code
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )