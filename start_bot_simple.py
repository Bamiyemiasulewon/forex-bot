#!/usr/bin/env python3
"""
Simple Forex Trading Bot Startup Script
This script starts the Telegram bot with proper error handling and reconnection logic.
"""

import os
import sys
import asyncio
import logging
import signal
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

def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {signum}, initiating shutdown...")
    shutdown_event.set()

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

def main():
    """Main function."""
    logger.info("🚀 Starting Forex Trading Bot (Simple Mode)")
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Run the bot with retry logic
        asyncio.run(run_bot_with_retry())
        
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        logger.error("Please check:")
        logger.error("1. Internet connection")
        logger.error("2. Bot token is valid")
        logger.error("3. All dependencies are installed")
    finally:
        logger.info("Application shutdown complete")

if __name__ == "__main__":
    main() 