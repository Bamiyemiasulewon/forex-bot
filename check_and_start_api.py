#!/usr/bin/env python3
"""
Script to check and start the API server if needed
"""

import asyncio
import httpx
import subprocess
import time
import logging
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_api_server():
    """Check if the API server is running."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://127.0.0.1:8000/health")
            if response.status_code == 200:
                logger.info("✅ API server is running!")
                return True
            else:
                logger.warning(f"⚠️ API server responded with status {response.status_code}")
                return False
    except Exception as e:
        logger.warning(f"⚠️ API server is not responding: {e}")
        return False

def start_api_server():
    """Start the API server in a separate process."""
    try:
        logger.info("🚀 Starting API server...")
        
        # Start the server in a new process
        process = subprocess.Popen([
            sys.executable, "main.py"
        ], cwd=os.getcwd())
        
        logger.info(f"📊 API server started with PID: {process.pid}")
        return process
    except Exception as e:
        logger.error(f"❌ Failed to start API server: {e}")
        return None

async def wait_for_api_server(max_wait=30):
    """Wait for the API server to become available."""
    logger.info("⏳ Waiting for API server to start...")
    
    for i in range(max_wait):
        if await check_api_server():
            logger.info("✅ API server is ready!")
            return True
        await asyncio.sleep(1)
    
    logger.error("❌ API server failed to start within timeout")
    return False

async def main():
    """Main function to check and start API server."""
    logger.info("🔍 Checking API server status...")
    
    # Check if server is already running
    if await check_api_server():
        logger.info("✅ API server is already running!")
        return
    
    # Start the server
    process = start_api_server()
    if not process:
        logger.error("❌ Failed to start API server")
        return
    
    # Wait for server to be ready
    if await wait_for_api_server():
        logger.info("🎉 API server is ready for use!")
        logger.info("💡 You can now start your Telegram bot")
    else:
        logger.error("❌ API server failed to start properly")
        process.terminate()

if __name__ == "__main__":
    asyncio.run(main()) 