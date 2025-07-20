import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import validate_environment, CORS_ORIGINS, CORS_HEADERS, CORS_EXPOSE_HEADERS
from .routers import health, chat, transactions

# Validate environment variables
validate_environment()

# --- FastAPI App Initialization ---
app = FastAPI(
    title="Payment Ops Copilot API",
    description="REST API for React frontend to analyze transaction data with AI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware for React development and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=CORS_HEADERS,
    expose_headers=CORS_EXPOSE_HEADERS,
    max_age=600,  # Cache preflight requests for 10 minutes
)

# Include routers
app.include_router(chat.router, tags=["Chat & Queries"])
app.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])

# --- API Startup/Shutdown Events ---

# @app.on_event("startup")
# async def startup_event():
#     """Initialize services on startup."""
#     await init_db_pools()

# @app.on_event("shutdown")
# async def shutdown_event():
#     """Cleanup on shutdown."""
#     await close_db_pools()

if __name__ == "__main__":
    print("🚀 Starting API on http://127.0.0.1:8001")
    
    uvicorn.run(app, host="127.0.0.1", port=8001) 