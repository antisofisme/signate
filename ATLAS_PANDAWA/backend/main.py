"""
ATLAS_PANDAWA Backend - FastAPI Application Entry Point
Follows CORE-STD-01 standards
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared.config import settings
from shared.api_routes import routes
from modules.auth.routes import router as auth_router

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Enterprise Hospitality Platform Backend API",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


# Include routers
app.include_router(auth_router)


# Future module routers will be added here per phase:
# Phase 2: PMS module
# from modules.pms.routes import router as pms_router
# app.include_router(pms_router)

# Phase 3: POS module
# from modules.pos.routes import router as pos_router
# app.include_router(pos_router)

# Phase 4: Accounting module
# from modules.accounting.routes import router as accounting_router
# app.include_router(accounting_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
