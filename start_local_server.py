#!/usr/bin/env python3
"""
Local API Server Starter for Forex Trading Bot
This script starts the local API server that the Telegram bot connects to.
"""

import subprocess
import sys
import os
import time
import signal
import requests

def check_server_running():
    """Check if the local server is already running."""
    try:
        response = requests.get("http://127.0.0.1:8000/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def start_server():
    """Start the local API server."""
    print("🚀 Starting Local API Server...")
    
    # Check if server is already running
    if check_server_running():
        print("✅ Local API server is already running!")
        return True
    
    # Try to find and start the main application
    possible_paths = [
        "app/main.py",
        "main.py",
        "api/main.py",
        "server.py"
    ]
    
    server_path = None
    for path in possible_paths:
        if os.path.exists(path):
            server_path = path
            break
    
    if not server_path:
        print("❌ Could not find server file. Please ensure one of these exists:")
        for path in possible_paths:
            print(f"   - {path}")
        return False
    
    print(f"📁 Found server file: {server_path}")
    
    try:
        # Start the server process
        print("🔄 Starting server process...")
        process = subprocess.Popen([
            sys.executable, server_path
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Wait a bit for the server to start
        print("⏳ Waiting for server to start...")
        time.sleep(3)
        
        # Check if server started successfully
        if check_server_running():
            print("✅ Local API server started successfully!")
            print(f"🌐 Server running at: http://127.0.0.1:8000")
            print(f"📊 Process ID: {process.pid}")
            print("\n💡 Keep this terminal open to keep the server running.")
            print("   Press Ctrl+C to stop the server.")
            
            return process
        else:
            print("❌ Server failed to start properly.")
            process.terminate()
            return False
            
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return False

def main():
    """Main function."""
    print("="*60)
    print("  Local API Server Starter")
    print("="*60)
    
    # Check if server is already running
    if check_server_running():
        print("✅ Local API server is already running!")
        print("🌐 Server available at: http://127.0.0.1:8000")
        return
    
    # Start the server
    process = start_server()
    
    if process:
        try:
            # Keep the process running
            process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Stopping server...")
            process.terminate()
            process.wait()
            print("✅ Server stopped.")
    else:
        print("\n❌ Failed to start server.")
        print("Please check:")
        print("1. All required dependencies are installed")
        print("2. The server file exists and is correct")
        print("3. Port 8000 is not already in use")

if __name__ == "__main__":
    main() 