#!/usr/bin/env python3
"""
Forex Trading Bot with API Server Startup Script
This script starts both the API server and the Telegram bot.
"""

import os
import sys
import asyncio
import subprocess
import time
import requests
import signal
import threading
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

class BotManager:
    def __init__(self):
        self.api_process = None
        self.bot_process = None
        self.running = True
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print(f"\n🛑 Received signal {signum}, shutting down...")
        self.running = False
        self.shutdown()
    
    def check_api_server(self, max_retries=30, retry_delay=2):
        """Check if API server is running and responding."""
        print("🔍 Checking API server status...")
        
        for attempt in range(max_retries):
            try:
                response = requests.get("http://127.0.0.1:8000/health", timeout=5)
                if response.status_code == 200:
                    print("✅ API server is running and responding")
                    return True
                else:
                    print(f"⚠️ API server responded with status {response.status_code}")
            except requests.exceptions.ConnectionError:
                print(f"⏳ API server not ready yet (attempt {attempt + 1}/{max_retries})")
            except requests.exceptions.Timeout:
                print(f"⏰ API server timeout (attempt {attempt + 1}/{max_retries})")
            except Exception as e:
                print(f"❌ Error checking API server: {e}")
            
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
        
        print("❌ API server failed to start or respond")
        return False
    
    def start_api_server(self):
        """Start the API server in a separate process."""
        print("🚀 Starting API server...")
        
        try:
            # Start API server
            self.api_process = subprocess.Popen([
                sys.executable, "start_api_server.py"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for API server to be ready
            if self.check_api_server():
                print("✅ API server started successfully")
                return True
            else:
                print("❌ Failed to start API server")
                return False
                
        except Exception as e:
            print(f"❌ Error starting API server: {e}")
            return False
    
    def start_bot(self):
        """Start the Telegram bot."""
        print("🤖 Starting Telegram bot...")
        
        try:
            # Import and start the bot
            from app.telegram.bot import start_telegram_bot
            
            # Create shutdown event
            shutdown_event = asyncio.Event()
            
            # Start the bot
            asyncio.run(start_telegram_bot(shutdown_event_param=shutdown_event))
            
        except Exception as e:
            print(f"❌ Error starting bot: {e}")
            return False
    
    def shutdown(self):
        """Shutdown all processes."""
        print("🛑 Shutting down...")
        
        if self.api_process:
            print("🛑 Stopping API server...")
            self.api_process.terminate()
            try:
                self.api_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.api_process.kill()
        
        print("✅ Shutdown complete")

def main():
    """Main function."""
    print("="*60)
    print("  Forex Trading Bot with API Server")
    print("="*60)
    
    manager = BotManager()
    
    try:
        # Start API server
        if not manager.start_api_server():
            print("❌ Failed to start API server. Exiting.")
            return
        
        print("\n" + "="*60)
        print("✅ API server is running!")
        print("📍 API Server: http://127.0.0.1:8000")
        print("🔍 Health Check: http://127.0.0.1:8000/health")
        print("📚 API Docs: http://127.0.0.1:8000/docs")
        print("="*60)
        
        # Start bot
        print("\n🤖 Starting Telegram bot...")
        manager.start_bot()
        
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    finally:
        manager.shutdown()

if __name__ == "__main__":
    main() 