import os
import sys

# Ensure the backend directory is in sys.path so 'app' package is found by Vercel's Python runtime
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Import the FastAPI application instance
from app.main import app

# Expose app for Vercel serverless execution
__all__ = ["app"]
