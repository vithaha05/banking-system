"""
Banking Transaction Processing System
Main application entry point
"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.database import init_db
from src.api import account_router, transaction_router
from src.exceptions import BankingException


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup: Initialize database
    await init_db()
    yield
    # Shutdown: Cleanup (if needed)


# Create FastAPI application
app = FastAPI(
    title="Banking Transaction Processing System",
    description="Production-quality banking transaction processing system with ACID guarantees",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware (for development/testing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(account_router)
app.include_router(transaction_router)


# Global exception handler
@app.exception_handler(BankingException)
async def banking_exception_handler(request, exc: BankingException):
    """Handle custom banking exceptions"""
    return JSONResponse(
        status_code=400,
        content={"error": exc.__class__.__name__, "detail": str(exc)}
    )


@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint"""
    return {
        "message": "Banking Transaction Processing System",
        "status": "operational",
        "version": "1.0.0"
    }


@app.get("/health", tags=["Health"])
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)

