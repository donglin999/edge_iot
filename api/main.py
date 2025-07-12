from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn
import os
from dotenv import load_dotenv

from routers import processes, data, config, system, websocket
from core.database import init_db
from core.websocket_manager import websocket_manager

# Load environment variables
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    await websocket_manager.start()
    yield
    # Shutdown
    await websocket_manager.stop()

app = FastAPI(
    title="IoT Data Acquisition System API",
    description="Web interface for IoT data collection system with real-time monitoring",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(processes.router, prefix="/api/processes", tags=["processes"])
app.include_router(data.router, prefix="/api/data", tags=["data"])
app.include_router(config.router, prefix="/api/config", tags=["config"])
app.include_router(system.router, prefix="/api/system", tags=["system"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "IoT Data Acquisition API"}

# Root endpoint
@app.get("/")
async def root():
    return {"message": "IoT Data Acquisition System API", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )