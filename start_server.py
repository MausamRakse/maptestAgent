"""
Simple startup script for the Image Measurement API server.
"""

import uvicorn
import os

if __name__ == "__main__":
    # Check if static directory exists
    if not os.path.exists("static"):
        os.makedirs("static")
        print("Created static directory")
    
    print("Starting Image Area & Line Measurement API...")
    print("Open http://localhost:8000/static/index.html in your browser")
    print("Press Ctrl+C to stop the server")
    
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )


