#!/usr/bin/env python3
"""
Simple API Server Starter
This script starts just the API server for testing purposes.
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path

def check_server_running():
    """Check if the API server is already running."""
    try:
        response = requests.get("http://127.0.0.1:8000/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def start_api_server():
    """Start the API server."""
    print("🚀 Starting API Server...")
    
    # Check if server is already running
    if check_server_running():
        print("✅ API server is already running!")
        return True
    
    # Find the main.py file
    main_py_path = Path("app/main.py")
    if not main_py_path.exists():
        print("❌ Could not find app/main.py")
        return False
    
    try:
        # Start the server process
        process = subprocess.Popen([
            sys.executable, str(main_py_path)
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Wait for server to start
        print("⏳ Waiting for API server to start...")
        for i in range(30):  # Wait up to 30 seconds
            time.sleep(1)
            if check_server_running():
                print("✅ API server started successfully!")
                return True
            print(f"   Waiting... ({i+1}/30)")
        
        print("❌ API server failed to start within 30 seconds")
        process.terminate()
        return False
        
    except Exception as e:
        print(f"❌ Error starting API server: {e}")
        return False

def main():
    """Main function."""
    print("="*60)
    print("  API Server Starter")
    print("="*60)
    
    # Start API server
    if not start_api_server():
        print("\n❌ Failed to start API server. Exiting.")
        return
    
    print("\n🎉 API server started successfully!")
    print("📊 API Server: http://127.0.0.1:8000")
    print("🔍 Health Check: http://127.0.0.1:8000/health")
    print("📚 API Docs: http://127.0.0.1:8000/docs")
    print("\n💡 Press Ctrl+C to stop the server.")
    
    try:
        # Keep the server running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping API server...")
        print("✅ API server stopped.")

if __name__ == "__main__":
    main() 