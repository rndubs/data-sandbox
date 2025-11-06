"""FastAPI main application for Time Series Platform."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from src.database import init_db
from src.api.routes import datasets, workflows, nodes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Time Series Data Platform",
    description="API for managing time series data with computation graphs",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For POC; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(datasets.router, prefix="/api/datasets", tags=["datasets"])
app.include_router(workflows.router, prefix="/api/workflows", tags=["workflows"])
app.include_router(nodes.router, prefix="/api/nodes", tags=["nodes"])


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    logger.info("Starting Time Series Platform API...")
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Time Series Data Platform",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
