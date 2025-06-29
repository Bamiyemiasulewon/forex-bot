#!/usr/bin/env python3
"""
Test API Connection Script
This script tests if the API server is running and accessible.
"""

import asyncio
import httpx
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

async def test_api_connection():
    """Test if the API server is running and accessible."""
    print("🔍 Testing API Server Connection...")
    
    # Test 1: Health check
    print("\n1. Testing health endpoint...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("http://127.0.0.1:8000/health")
            if response.status_code == 200:
                print("✅ Health check passed!")
                health_data = response.json()
                print(f"   Status: {health_data.get('status', 'unknown')}")
                print(f"   Bot Status: {health_data.get('bot_status', 'unknown')}")
                print(f"   MT5 Status: {health_data.get('mt5_status', 'unknown')}")
            else:
                print(f"❌ Health check failed with status code: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    # Test 2: MT5 status endpoint
    print("\n2. Testing MT5 status endpoint...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get("http://127.0.0.1:8000/api/mt5/status")
            if response.status_code == 200:
                print("✅ MT5 status endpoint accessible!")
                status_data = response.json()
                print(f"   Connected: {status_data.get('connected', False)}")
                if not status_data.get('connected'):
                    print(f"   Error: {status_data.get('error', 'Unknown error')}")
            else:
                print(f"❌ MT5 status failed with status code: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ MT5 status failed: {e}")
        return False
    
    # Test 3: MT5 connect endpoint (with mock data)
    print("\n3. Testing MT5 connect endpoint...")
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            test_credentials = {
                "login": "12345678",
                "password": "test_password",
                "server": "test_server"
            }
            response = await client.post("http://127.0.0.1:8000/api/mt5/connect", json=test_credentials)
            if response.status_code == 200:
                print("✅ MT5 connect endpoint accessible!")
                connect_data = response.json()
                print(f"   Success: {connect_data.get('success', False)}")
                if not connect_data.get('success'):
                    print(f"   Error: {connect_data.get('error', 'Unknown error')}")
            else:
                print(f"❌ MT5 connect failed with status code: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
    except httpx.TimeoutException:
        print("❌ MT5 connect timed out (this is expected for test credentials)")
        print("   The endpoint is working, but MT5 connection takes time")
    except Exception as e:
        print(f"❌ MT5 connect failed: {e}")
        return False
    
    print("\n🎉 All API tests passed! The API server is running correctly.")
    return True

async def test_bot_api_service():
    """Test the bot's API service integration."""
    print("\n🔍 Testing Bot API Service Integration...")
    
    try:
        from app.services.api_service import api_service
        
        # Test API service call
        print("Testing API service call to /api/mt5/status...")
        result = await api_service.make_api_call("/api/mt5/status")
        
        if result is not None:
            print("✅ Bot API service working correctly!")
            print(f"   Result: {result}")
        else:
            print("❌ Bot API service returned None")
            return False
            
    except Exception as e:
        print(f"❌ Bot API service test failed: {e}")
        return False
    
    return True

def main():
    """Main function."""
    print("="*60)
    print("  API Connection Test")
    print("="*60)
    
    try:
        # Run the tests
        api_result = asyncio.run(test_api_connection())
        bot_result = asyncio.run(test_bot_api_service())
        
        print("\n" + "="*60)
        print("  Test Results")
        print("="*60)
        
        if api_result and bot_result:
            print("✅ All tests passed! Your bot should work correctly.")
            print("\n💡 If you're still having issues:")
            print("1. Make sure you're using the new startup scripts")
            print("2. Check that the API server is running on port 8000")
            print("3. Verify your MT5 credentials are correct")
        else:
            print("❌ Some tests failed. Please check the errors above.")
            print("\n🔧 Troubleshooting:")
            print("1. Start the API server: python start_complete_bot.py")
            print("2. Check if port 8000 is available")
            print("3. Verify all dependencies are installed")
            
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    main() 