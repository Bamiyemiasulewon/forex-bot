#!/usr/bin/env python3
"""
Complete Forex Trading Bot Startup Script
This script starts both the API server and the Telegram bot with proper monitoring.
"""

import subprocess
import sys
import os
import time
import signal
import threading
import requests
from pathlib import Path

# Add the app directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

class SystemManager:
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
        """Start the API server."""
        print("🚀 Starting API server...")
        
        # Get the full path to the API app.py file
        api_app_path = Path(__file__).parent / "app" / "api" / "app.py"
        
        try:
            # Start the API server from the main directory
            self.api_process = subprocess.Popen(
                [sys.executable, str(api_app_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                cwd=Path(__file__).parent  # Run from the main forex-bot directory
            )
            
            print(f"✅ API server started with PID: {self.api_process.pid}")
            
            # Wait a moment for the server to start
            time.sleep(3)
            
            # Check if server is responding
            if self.check_api_server():
                return True
            else:
                print("❌ API server failed to respond")
                return False
                
        except Exception as e:
            print(f"❌ Error starting API server: {e}")
            return False
    
    def start_telegram_bot(self):
        """Start the Telegram bot."""
        print("🤖 Starting Telegram bot...")
        
        # Change back to the main directory
        main_dir = Path(__file__).parent
        os.chdir(main_dir)
        
        try:
            # Start the bot
            self.bot_process = subprocess.Popen(
                [sys.executable, "start_bot.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            print(f"✅ Telegram bot started with PID: {self.bot_process.pid}")
            return True
            
        except Exception as e:
            print(f"❌ Error starting Telegram bot: {e}")
            return False
    
    def monitor_processes(self):
        """Monitor the running processes."""
        print("\n📊 Monitoring processes...")
        print("Press Ctrl+C to stop all services")
        
        while self.running:
            # Check API server
            if self.api_process and self.api_process.poll() is not None:
                print("❌ API server process has stopped")
                self.running = False
                break
            
            # Check bot process
            if self.bot_process and self.bot_process.poll() is not None:
                print("❌ Telegram bot process has stopped")
                self.running = False
                break
            
            # Check API server health every 30 seconds
            if time.time() % 30 < 1:  # Every 30 seconds
                try:
                    response = requests.get("http://127.0.0.1:8000/health", timeout=5)
                    if response.status_code != 200:
                        print("⚠️ API server health check failed")
                except:
                    print("⚠️ API server health check failed")
            
            time.sleep(1)
    
    def shutdown(self):
        """Shutdown all processes."""
        print("\n🛑 Shutting down all services...")
        
        # Stop bot process
        if self.bot_process:
            print("🛑 Stopping Telegram bot...")
            try:
                self.bot_process.terminate()
                self.bot_process.wait(timeout=10)
                print("✅ Telegram bot stopped")
            except subprocess.TimeoutExpired:
                print("⚠️ Force killing Telegram bot...")
                self.bot_process.kill()
            except Exception as e:
                print(f"❌ Error stopping Telegram bot: {e}")
        
        # Stop API server
        if self.api_process:
            print("🛑 Stopping API server...")
            try:
                self.api_process.terminate()
                self.api_process.wait(timeout=10)
                print("✅ API server stopped")
            except subprocess.TimeoutExpired:
                print("⚠️ Force killing API server...")
                self.api_process.kill()
            except Exception as e:
                print(f"❌ Error stopping API server: {e}")
        
        print("✅ All services stopped")

def main():
    """Main function."""
    print("="*70)
    print("  🚀 Forex Trading Bot - Complete System Startup")
    print("="*70)
    
    # Check if we're in the right directory
    script_dir = Path(__file__).parent
    api_app_path = script_dir / "app" / "api" / "app.py"
    if not api_app_path.exists():
        print(f"❌ Error: {api_app_path} not found!")
        print("Please run this script from the forex-bot directory")
        sys.exit(1)
    
    # Create system manager
    manager = SystemManager()
    
    try:
        # Start API server
        if not manager.start_api_server():
            print("❌ Failed to start API server")
            sys.exit(1)
        
        # Start Telegram bot
        if not manager.start_telegram_bot():
            print("❌ Failed to start Telegram bot")
            manager.shutdown()
            sys.exit(1)
        
        print("\n" + "="*70)
        print("  ✅ All services started successfully!")
        print("="*70)
        print("🌐 API Server: http://127.0.0.1:8000")
        print("📊 Health Check: http://127.0.0.1:8000/health")
        print("📚 API Docs: http://127.0.0.1:8000/docs")
        print("🤖 Telegram Bot: Running and monitoring...")
        print("\n💡 Keep this terminal open to monitor the services.")
        print("   Press Ctrl+C to stop all services.")
        print("="*70)
        
        # Monitor processes
        manager.monitor_processes()
        
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    finally:
        manager.shutdown()
        print("\n👋 Goodbye!")

if __name__ == "__main__":
    main() 