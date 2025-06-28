#!/usr/bin/env python3
"""
API Server Test Script
This script tests the local API server to ensure it's working correctly.
"""

import requests
import time
import sys

def test_api_endpoints():
    """Test all API endpoints."""
    base_url = "http://127.0.0.1:8000"
    
    endpoints = [
        ("/", "Root endpoint"),
        ("/health", "Health check"),
        ("/api/signals", "Trading signals"),
        ("/api/trades", "Trade history"),
        ("/api/settings", "User settings"),
        ("/api/help", "Help information"),
        ("/api/strategies", "Trading strategies"),
        ("/api/market/EURUSD", "Market data"),
        ("/api/risk/EURUSD/2.0/50", "Risk calculation"),
        ("/api/pipcalc/EURUSD/0.1", "Pip calculation")
    ]
    
    print("🧪 Testing API Server Endpoints")
    print("="*50)
    
    all_passed = True
    
    for endpoint, description in endpoints:
        try:
            print(f"Testing {description} ({endpoint})...", end=" ")
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            
            if response.status_code == 200:
                print("✅ PASS")
                # Show a sample of the response
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    print(f"   📊 Response: {len(data)} items")
                elif isinstance(data, dict):
                    print(f"   📊 Response: {list(data.keys())[:3]}...")
            else:
                print(f"❌ FAIL (HTTP {response.status_code})")
                all_passed = False
                
        except requests.exceptions.ConnectionError:
            print("❌ FAIL (Connection refused)")
            all_passed = False
        except requests.exceptions.Timeout:
            print("❌ FAIL (Timeout)")
            all_passed = False
        except Exception as e:
            print(f"❌ FAIL (Error: {e})")
            all_passed = False
    
    print("\n" + "="*50)
    if all_passed:
        print("🎉 All API endpoints are working correctly!")
        return True
    else:
        print("❌ Some API endpoints failed. Check the server logs.")
        return False

def test_server_availability():
    """Test if the server is available."""
    print("🔍 Testing server availability...")
    
    try:
        response = requests.get("http://127.0.0.1:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is available and responding")
            return True
        else:
            print(f"❌ Server responded with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Server is not available (Connection refused)")
        return False
    except requests.exceptions.Timeout:
        print("❌ Server timeout")
        return False
    except Exception as e:
        print(f"❌ Error testing server: {e}")
        return False

def main():
    """Main function."""
    print("🚀 API Server Test")
    print("="*50)
    
    # Test server availability first
    if not test_server_availability():
        print("\n❌ Server is not available!")
        print("Please start the API server first:")
        print("1. Navigate to: C:\\Users\\User\\forex1\\forex-bot\\app\\api")
        print("2. Run: python app.py")
        print("3. Keep that terminal open")
        print("4. Run this test again in another terminal")
        sys.exit(1)
    
    print("\n" + "="*50)
    
    # Test all endpoints
    if test_api_endpoints():
        print("\n🎉 API server is working perfectly!")
        print("You can now start the Telegram bot.")
    else:
        print("\n❌ API server has issues.")
        print("Check the server logs for more details.")

if __name__ == "__main__":
    main() 