#!/usr/bin/env python3
"""
Complete Forex Trading Bot Startup Script
This script starts both the API server and the Telegram bot with proper error handling.
"""

import os
import sys
import asyncio
import logging
import signal
import subprocess
import time
import requests
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables for graceful shutdown
shutdown_event = asyncio.Event()
api_process = None

def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {signum}, initiating shutdown...")
    shutdown_event.set()

def check_api_server():
    """Check if the API server is running."""
    try:
        response = requests.get("http://127.0.0.1:8000/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def start_api_server():
    """Start the API server."""
    global api_process
    
    logger.info("🚀 Starting API Server...")
    
    # Check if server is already running
    if check_api_server():
        logger.info("✅ API server is already running!")
        return True
    
    # Find the main.py file
    main_py_path = Path("app/main.py")
    if not main_py_path.exists():
        logger.error("❌ Could not find app/main.py")
        return False
    
    try:
        # Start the server process
        api_process = subprocess.Popen([
            sys.executable, str(main_py_path)
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Wait for server to start
        logger.info("⏳ Waiting for API server to start...")
        for i in range(30):  # Wait up to 30 seconds
            time.sleep(1)
            if check_api_server():
                logger.info("✅ API server started successfully!")
                return True
            logger.info(f"   Waiting... ({i+1}/30)")
        
        logger.error("❌ API server failed to start within 30 seconds")
        if api_process:
            api_process.terminate()
        return False
        
    except Exception as e:
        logger.error(f"❌ Error starting API server: {e}")
        return False

async def run_bot_with_retry():
    """Run the bot with automatic retry on failure."""
    from app.telegram.bot import start_telegram_bot, shutdown_bot
    
    max_retries = 5
    retry_delay = 10  # seconds
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Starting bot (attempt {attempt + 1}/{max_retries})")
            
            # Start the bot
            await start_telegram_bot(shutdown_event_param=shutdown_event)
            
            # If we get here, the bot has stopped normally
            logger.info("Bot stopped normally")
            break
            
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
            break
        except Exception as e:
            logger.error(f"Bot crashed on attempt {attempt + 1}: {e}")
            
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error("Max retries reached. Bot will not restart.")
                break
        finally:
            # Always try to shutdown gracefully
            try:
                await shutdown_bot()
            except Exception as e:
                logger.error(f"Error during shutdown: {e}")

async def monitor_services():
    """Monitor both API server and bot."""
    while not shutdown_event.is_set():
        try:
            # Check API server health
            if not check_api_server():
                logger.warning("⚠️ API server is not responding")
            
            await asyncio.sleep(30)  # Check every 30 seconds
            
        except Exception as e:
            logger.error(f"Error in service monitoring: {e}")
            await asyncio.sleep(30)

def cleanup():
    """Clean up processes on shutdown."""
    global api_process
    
    logger.info("🛑 Cleaning up processes...")
    
    # Stop API server
    if api_process:
        try:
            logger.info("Stopping API server...")
            api_process.terminate()
            api_process.wait(timeout=10)
            logger.info("✅ API server stopped")
        except subprocess.TimeoutExpired:
            logger.warning("API server did not stop gracefully, forcing...")
            api_process.kill()
        except Exception as e:
            logger.error(f"Error stopping API server: {e}")
    
    logger.info("✅ Cleanup complete")

async def main():
    """Main async function."""
    logger.info("🚀 Starting Complete Forex Trading Bot System")
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start API server
        if not start_api_server():
            logger.error("❌ Failed to start API server")
            return
        
        # Start monitoring task
        monitor_task = asyncio.create_task(monitor_services())
        
        # Start bot with retry logic
        await run_bot_with_retry()
        
        # Cancel monitoring task
        monitor_task.cancel()
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass
        
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        logger.error("Please check:")
        logger.error("1. Internet connection")
        logger.error("2. Bot token is valid")
        logger.error("3. All dependencies are installed")
    finally:
        cleanup()
        logger.info("Application shutdown complete")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application interrupted")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        cleanup() 