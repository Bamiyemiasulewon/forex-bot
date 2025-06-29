#!/usr/bin/env python3
"""
Script to stop all running bot instances and clear webhooks
"""

import asyncio
import os
import sys
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Your bot token
TELEGRAM_TOKEN = "8071906329:AAH4BbllY9vwwcx0vukm6t6JPQdNWnnz-aY"

async def clear_webhook():
    """Clear any existing webhook to ensure polling mode."""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/deleteWebhook"
        response = requests.post(url, params={"drop_pending_updates": True})
        
        if response.status_code == 200:
            logger.info("✅ Webhook cleared successfully")
            return True
        else:
            logger.error(f"❌ Failed to clear webhook: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Error clearing webhook: {e}")
        return False

async def get_webhook_info():
    """Get current webhook information."""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getWebhookInfo"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"📡 Webhook Info: {data}")
            return data
        else:
            logger.error(f"❌ Failed to get webhook info: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"❌ Error getting webhook info: {e}")
        return None

def kill_processes_on_port(port):
    """Kill processes running on a specific port (Windows)."""
    try:
        import subprocess
        # Find processes using the port
        result = subprocess.run(
            ["netstat", "-ano"], 
            capture_output=True, 
            text=True, 
            shell=True
        )
        
        lines = result.stdout.split('\n')
        for line in lines:
            if f":{port}" in line and "LISTENING" in line:
                parts = line.split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    logger.info(f"🔄 Killing process {pid} on port {port}")
                    subprocess.run(["taskkill", "/PID", pid, "/F"], shell=True)
                    
    except Exception as e:
        logger.error(f"❌ Error killing processes: {e}")

async def main():
    """Main function to stop all bot instances."""
    logger.info("🛑 Stopping all bot instances...")
    
    # 1. Clear webhook
    await clear_webhook()
    
    # 2. Get webhook info to verify
    await get_webhook_info()
    
    # 3. Kill processes on common ports
    ports = [8000, 10000, 8080]
    for port in ports:
        kill_processes_on_port(port)
    
    logger.info("✅ Bot cleanup complete!")
    logger.info("💡 Now you can start a fresh instance of the bot.")

if __name__ == "__main__":
    asyncio.run(main()) 