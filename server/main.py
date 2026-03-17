"""
FastAPI application entry point for Terrain Generation Service.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from server.routes import router


app = FastAPI(
    title="3D TerrainGen Studio API",
    description="Procedural terrain generation with wave interference and harmonic noise",
    version="1.0.0"
)

# Configure CORS for web client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/api")

# Serve the client HTML/JS/CSS frontend
_client_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "client")

@app.get("/")
async def root():
    """Serve the frontend entry point"""
    index_path = os.path.join(_client_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "name": "3D TerrainGen Studio API",
        "version": "1.0.0",
        "docs": "/docs",
        "message": "Frontend index.html not found"
    }

if os.path.isdir(_client_dir):
    app.mount("/", StaticFiles(directory=_client_dir), name="client")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
