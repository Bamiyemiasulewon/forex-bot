#!/usr/bin/env python3
"""
Startup script for the combined Forex Trading Bot (FastAPI + Telegram Bot)
This script provides a simple way to start the application with proper error handling.
"""

import os
import sys
import logging

# Add the current directory to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Start the combined application."""
    try:
        # Import and run the main application
        from main import main as run_app
        run_app()
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error("Make sure all dependencies are installed: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 