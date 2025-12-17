"""
FastAPI application entry point for Terrain Generation Service.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


@app.get("/")
async def root():
    return {
        "name": "3D TerrainGen Studio API",
        "version": "1.0.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
