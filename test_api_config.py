#!/usr/bin/env python3
"""
Test script to verify API service configuration
"""

import os
import sys

# Add the app directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

from app.services.api_service import api_service, get_api_base_url

def test_api_config():
    """Test the API service configuration."""
    print("🔍 Testing API Service Configuration")
    print("=" * 50)
    
    # Test the base URL function
    base_url = get_api_base_url()
    print(f"📡 API Base URL: {base_url}")
    
    # Test the API service instance
    print(f"🤖 API Service Base URL: {api_service.base_url}")
    
    # Check environment variables
    render_url = os.getenv("RENDER_EXTERNAL_URL", "")
    print(f"🌐 RENDER_EXTERNAL_URL: {render_url if render_url else 'Not set'}")
    
    # Determine if we're running locally or on Render
    if "127.0.0.1" in base_url or "localhost" in base_url:
        print("🏠 Running in LOCAL development mode")
    else:
        print("☁️ Running in PRODUCTION mode (Render)")
    
    print("=" * 50)
    print("✅ API Service configuration test complete!")

if __name__ == "__main__":
    test_api_config() 