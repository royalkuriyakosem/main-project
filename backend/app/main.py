"""
PhishDetect Backend - Main Application Entry Point

A hybrid URL-DOM based phishing detection framework powered by:
- FastAPI for the REST API
- TensorFlow/Keras for URL-based ML prediction
- Puppeteer for DOM extraction
- SSIM for visual similarity analysis
"""

import os
import sys

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.api.routes import router, set_paths
from app.ml.url_predictor import initialize_model

# Define paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # backend/app/
BACKEND_DIR = os.path.dirname(BASE_DIR)                 # backend/
ROOT_DIR = os.path.dirname(BACKEND_DIR)                 # main-project/
MODELS_DIR = os.path.join(ROOT_DIR, "models")
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend", "src")
SCRIPTS_DIR = os.path.join(BACKEND_DIR, "scripts")

# Debug prints
print(f"Root Dir: {ROOT_DIR}")
print(f"Models Dir: {MODELS_DIR}")
print(f"Frontend Dir: {FRONTEND_DIR}")
print(f"Scripts Dir: {SCRIPTS_DIR}")

# Initialize ML model
try:
    initialize_model(MODELS_DIR)
except Exception as e:
    print(f"Error loading model: {e}")
    raise

# Set paths for routes
set_paths(FRONTEND_DIR, SCRIPTS_DIR)

# Create FastAPI app
app = FastAPI(
    title="PhishDetect API",
    description="A Hybrid URL-DOM Based Phishing Detection Framework",
    version="2.0.0"
)

# Mount static files (frontend)
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
    print(f"✓ Static files mounted from: {FRONTEND_DIR}")
else:
    print(f"⚠ Warning: Frontend directory not found: {FRONTEND_DIR}")

# Include API routes
app.include_router(router)


@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the frontend HTML page."""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path) as f:
            return f.read()
    return "<h1>PhishDetect API</h1><p>Frontend not found. API is running.</p>"


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "phishdetect"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
