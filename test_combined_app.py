#!/usr/bin/env python3
"""
Test script for the combined Forex Trading Bot application.
This script tests the basic functionality of both the FastAPI server and Telegram bot.
"""

import asyncio
import httpx
import logging
import os
import sys
import time

# Add the current directory to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_api_endpoints():
    """Test the FastAPI endpoints."""
    base_url = "http://127.0.0.1:8000"
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            # Test root endpoint
            logger.info("Testing root endpoint...")
            response = await client.get(f"{base_url}/")
            assert response.status_code == 200
            logger.info("✅ Root endpoint working")
            
            # Test health endpoint
            logger.info("Testing health endpoint...")
            response = await client.get(f"{base_url}/health")
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "bot_status" in data
            logger.info("✅ Health endpoint working")
            
            # Test API signals endpoint
            logger.info("Testing signals endpoint...")
            response = await client.get(f"{base_url}/api/signals")
            assert response.status_code == 200
            signals = response.json()
            assert isinstance(signals, list)
            logger.info(f"✅ Signals endpoint working - {len(signals)} signals returned")
            
            # Test API trades endpoint
            logger.info("Testing trades endpoint...")
            response = await client.get(f"{base_url}/api/trades")
            assert response.status_code == 200
            trades = response.json()
            assert isinstance(trades, list)
            logger.info(f"✅ Trades endpoint working - {len(trades)} trades returned")
            
            logger.info("🎉 All API endpoints are working correctly!")
            return True
            
        except Exception as e:
            logger.error(f"❌ API test failed: {e}")
            return False

async def test_bot_connection():
    """Test if the Telegram bot is properly initialized."""
    try:
        # Import the main module to check bot status
        from main import telegram_app, bot_task
        
        # Check if bot task is running
        if bot_task and not bot_task.done():
            logger.info("✅ Telegram bot task is running")
            return True
        else:
            logger.warning("⚠️ Telegram bot task is not running")
            return False
            
    except Exception as e:
        logger.error(f"❌ Bot connection test failed: {e}")
        return False

async def main():
    """Run all tests."""
    logger.info("🧪 Starting combined application tests...")
    
    # Wait a moment for the application to start
    logger.info("⏳ Waiting for application to start...")
    await asyncio.sleep(5)
    
    # Test API endpoints
    api_success = await test_api_endpoints()
    
    # Test bot connection
    bot_success = await test_bot_connection()
    
    # Summary
    logger.info("\n📊 Test Results:")
    logger.info(f"API Endpoints: {'✅ PASS' if api_success else '❌ FAIL'}")
    logger.info(f"Telegram Bot: {'✅ PASS' if bot_success else '❌ FAIL'}")
    
    if api_success and bot_success:
        logger.info("🎉 All tests passed! The combined application is working correctly.")
        return True
    else:
        logger.error("❌ Some tests failed. Please check the application logs.")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test script error: {e}")
        sys.exit(1) 