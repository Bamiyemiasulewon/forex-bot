#!/usr/bin/env python3
"""
Local development script for the combined Forex Trading Bot.
This script sets up the environment and runs the application locally.
"""

import os
import sys
import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_environment():
    """Set up environment variables for local development."""
    # Set default environment variables for local development
    os.environ.setdefault('HOST', '127.0.0.1')
    os.environ.setdefault('PORT', '8000')
    os.environ.setdefault('RELOAD', 'true')
    os.environ.setdefault('LOG_LEVEL', 'INFO')
    os.environ.setdefault('TELEGRAM_TOKEN', '8071906329:AAH4BbllY9vwwcx0vukm6t6JPQdNWnnz-aY')
    
    # Check if TELEGRAM_TOKEN is set
    if not os.getenv('TELEGRAM_TOKEN'):
        logger.error("❌ TELEGRAM_TOKEN environment variable is not set!")
        logger.info("Please set your Telegram bot token:")
        logger.info("export TELEGRAM_TOKEN='your_bot_token_here'")
        return False
    
    logger.info("✅ Environment variables configured")
    return True

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import fastapi
        import uvicorn
        import telegram
        import httpx
        logger.info("✅ All required dependencies are installed")
        return True
    except ImportError as e:
        logger.error(f"❌ Missing dependency: {e}")
        logger.info("Please install dependencies: pip install -r requirements.txt")
        return False

def main():
    """Main function to run the application locally."""
    logger.info("🚀 Starting Forex Trading Bot (Local Development)")
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Setup environment
    if not setup_environment():
        sys.exit(1)
    
    # Display startup information
    logger.info("📋 Configuration:")
    logger.info(f"   Host: {os.getenv('HOST')}")
    logger.info(f"   Port: {os.getenv('PORT')}")
    logger.info(f"   Reload: {os.getenv('RELOAD')}")
    logger.info(f"   Log Level: {os.getenv('LOG_LEVEL')}")
    
    logger.info("\n🌐 URLs:")
    logger.info(f"   API: http://{os.getenv('HOST')}:{os.getenv('PORT')}")
    logger.info(f"   Health: http://{os.getenv('HOST')}:{os.getenv('PORT')}/health")
    logger.info(f"   Docs: http://{os.getenv('HOST')}:{os.getenv('PORT')}/docs")
    
    logger.info("\n💡 Tips:")
    logger.info("   - Press Ctrl+C to stop the application")
    logger.info("   - Check the logs for any errors")
    logger.info("   - Use /start in Telegram to test the bot")
    
    try:
        # Import and run the main application
        from main import main as run_app
        run_app()
    except KeyboardInterrupt:
        logger.info("\n🛑 Application stopped by user")
    except Exception as e:
        logger.error(f"❌ Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 