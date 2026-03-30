#!/usr/bin/env python
"""Start the FastAPI server from the correct directory."""

import os
import sys
import uvicorn

# Change to backend directory
backend_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(backend_dir)
sys.path.insert(0, backend_dir)

if __name__ == "__main__":
    print(f"Starting server from {backend_dir}")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
    )
