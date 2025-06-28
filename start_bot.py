#!/usr/bin/env python3
"""
Forex Trading Bot Startup Script
This script starts both the local API server and the Telegram bot.
"""

import subprocess
import sys
import os
import time
import signal
import requests
import threading
from pathlib import Path

def check_server_running():
    """Check if the local server is running."""
    try:
        response = requests.get("http://127.0.0.1:8000/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def start_local_server():
    """Start the local API server in a separate thread."""
    print("🚀 Starting Local API Server...")
    
    # Check if server is already running
    if check_server_running():
        print("✅ Local API server is already running!")
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
        print("⏳ Waiting for server to start...")
        for i in range(30):  # Wait up to 30 seconds
            time.sleep(1)
            if check_server_running():
                print("✅ Local API server started successfully!")
                return True
            print(f"   Waiting... ({i+1}/30)")
        
        print("❌ Server failed to start within 30 seconds")
        process.terminate()
        return False
        
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return False

def start_telegram_bot():
    """Start the Telegram bot."""
    print("\n🤖 Starting Telegram Bot...")
    
    bot_py_path = Path("app/telegram/bot.py")
    if not bot_py_path.exists():
        print("❌ Could not find app/telegram/bot.py")
        return False
    
    try:
        # Start the bot process
        process = subprocess.Popen([
            sys.executable, str(bot_py_path)
        ])
        
        print("✅ Telegram bot started successfully!")
        return process
        
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        return False

def main():
    """Main function."""
    print("="*60)
    print("  Forex Trading Bot Startup")
    print("="*60)
    
    # Step 1: Start local server
    if not start_local_server():
        print("\n❌ Failed to start local server. Exiting.")
        return
    
    # Step 2: Start Telegram bot
    bot_process = start_telegram_bot()
    if not bot_process:
        print("\n❌ Failed to start Telegram bot. Exiting.")
        return
    
    print("\n🎉 Both services started successfully!")
    print("📊 Local API Server: http://127.0.0.1:8000")
    print("🤖 Telegram Bot: Running")
    print("\n💡 Press Ctrl+C to stop both services.")
    
    try:
        # Keep both processes running
        bot_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Stopping services...")
        bot_process.terminate()
        bot_process.wait()
        print("✅ Services stopped.")

if __name__ == "__main__":
    main() 