#!/usr/bin/env python3
"""
Simple API Server Startup Script
This script starts the FastAPI server that the Telegram bot needs to function.
"""

import os
import sys
import uvicorn
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

def main():
    """Start the API server."""
    print("🚀 Starting Forex Trading Bot API Server...")
    print("📍 Server will be available at: http://127.0.0.1:8000")
    print("🔗 Health check: http://127.0.0.1:8000/health")
    print("📊 API docs: http://127.0.0.1:8000/docs")
    print("\n💡 Keep this terminal open while using the bot!")
    print("🛑 Press Ctrl+C to stop the server")
    print("="*60)
    
    try:
        # Start the server
        uvicorn.run(
            "app.api.app:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 API server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting API server: {e}")
        print("Please check:")
        print("1. All dependencies are installed")
        print("2. Port 8000 is not in use")
        print("3. You have proper permissions")

if __name__ == "__main__":
    main() 