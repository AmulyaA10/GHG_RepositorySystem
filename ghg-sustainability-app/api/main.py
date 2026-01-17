"""
FastAPI Application - GHG Sustainability API
Main entry point for the REST API
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
import logging
import time

from core.config import settings
from core.db import init_db, get_pool_status

# Import routers
from api.routes.auth import router as auth_router
from api.routes.projects import router as projects_router
from api.routes.collection import router as collection_router
from api.routes.transformation import router as transformation_router
from api.routes.verification import router as verification_router
from api.routes.final_review import router as final_review_router
from api.routes.reporting import router as reporting_router

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="GHG Sustainability API",
    description="""
## GHG Data Lifecycle Management API

This API provides endpoints for managing the complete GHG (Greenhouse Gas)
data lifecycle, aligned to **GHG Protocol** and **ISO 14064-1/-3** standards.

### Workflow Lanes

The API follows a 5-lane workflow:

1. **Data Collection** (L1 - Data Collector)
   - Collect raw activity data
   - Initial quality checks
   - Submit for calculation

2. **Data Transformation** (L2 - Calculation Specialist)
   - Map data to GHG schema
   - Calculate emissions
   - Validate transformations

3. **Data Verification** (L3 - QA Reviewer)
   - Verify data integrity
   - GHG Protocol compliance check
   - Approve or reject

4. **Final Review** (L4 - Sustainability Manager)
   - Final approval
   - Lock project
   - Archive data

5. **Reporting** (All roles)
   - Dashboard data
   - GHG inventory reports
   - Compliance status

### Authentication

All endpoints (except `/auth/token`) require JWT authentication.
Include the token in the `Authorization` header:

```
Authorization: Bearer <your_token>
```

### Role-Based Access

- **L1**: Data Entry Specialist
- **L2**: Calculation Specialist
- **L3**: QA Reviewer
- **L4**: Approver/Manager
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


# Include routers
app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(collection_router)
app.include_router(transformation_router)
app.include_router(verification_router)
app.include_router(final_review_router)
app.include_router(reporting_router)


# Health check endpoints
@app.get("/", tags=["Health"])
async def root():
    """
    Root endpoint - API information
    """
    return {
        "name": "GHG Sustainability API",
        "version": "1.0.0",
        "description": "GHG Data Lifecycle Management API",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "debug": settings.DEBUG
    }


@app.get("/health/db", tags=["Health"])
async def database_health():
    """
    Database health check with connection pool status
    """
    try:
        pool_status = get_pool_status()
        return {
            "status": "healthy",
            "database": "connected",
            "pool": pool_status
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e)
            }
        )


# Startup event
@app.on_event("startup")
async def startup_event():
    """
    Application startup tasks
    """
    logger.info("Starting GHG Sustainability API...")
    logger.info(f"Debug mode: {settings.DEBUG}")

    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown tasks
    """
    logger.info("Shutting down GHG Sustainability API...")


# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="GHG Sustainability API",
        version="1.0.0",
        description=app.description,
        routes=app.routes,
    )

    # Add security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your JWT token"
        }
    }

    # Apply security globally
    openapi_schema["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# Run with uvicorn
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info"
    )
