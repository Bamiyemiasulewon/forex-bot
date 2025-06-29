#!/usr/bin/env python3
"""
Real MT5 Connection Test
This script helps test MT5 connection with real credentials.
"""

import asyncio
import httpx
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

async def test_real_mt5_connection():
    """Test MT5 connection with real credentials."""
    print("🔍 Testing Real MT5 Connection...")
    
    # Get credentials from user
    print("\nPlease enter your MT5 credentials:")
    login = input("Login ID: ").strip()
    password = input("Password: ").strip()
    server = input("Server: ").strip()
    
    if not all([login, password, server]):
        print("❌ All credentials are required!")
        return False
    
    print(f"\n🔗 Testing connection to MT5: {login}@{server}")
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:  # 2 minutes timeout
            credentials = {
                "login": login,
                "password": password,
                "server": server
            }
            
            print("⏳ Connecting to MT5 (this may take up to 2 minutes)...")
            response = await client.post("http://127.0.0.1:8000/api/mt5/connect", json=credentials)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    print("✅ MT5 Connection Successful!")
                    account_info = result.get("account_info", {})
                    print(f"   Account: {account_info.get('login', 'N/A')}")
                    print(f"   Server: {account_info.get('server', 'N/A')}")
                    print(f"   Balance: ${account_info.get('balance', 0):,.2f}")
                    print(f"   Equity: ${account_info.get('equity', 0):,.2f}")
                    return True
                else:
                    print("❌ MT5 Connection Failed!")
                    print(f"   Error: {result.get('error', 'Unknown error')}")
                    return False
            else:
                print(f"❌ API Error: HTTP {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
    except httpx.TimeoutException:
        print("❌ Connection timed out after 2 minutes")
        print("   This could mean:")
        print("   - MT5 terminal is not running")
        print("   - Credentials are incorrect")
        print("   - Server name is wrong")
        print("   - Network issues")
        return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def check_api_server():
    """Check if API server is running."""
    try:
        import requests
        response = requests.get("http://127.0.0.1:8000/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    """Main function."""
    print("="*60)
    print("  Real MT5 Connection Test")
    print("="*60)
    
    # Check if API server is running
    if not check_api_server():
        print("❌ API server is not running!")
        print("Please start the API server first:")
        print("   python start_api_server.py")
        return
    
    print("✅ API server is running")
    
    try:
        # Test real MT5 connection
        success = asyncio.run(test_real_mt5_connection())
        
        print("\n" + "="*60)
        if success:
            print("🎉 MT5 connection test successful!")
            print("Your bot should now be able to connect to MT5.")
        else:
            print("❌ MT5 connection test failed.")
            print("\n🔧 Troubleshooting:")
            print("1. Make sure MT5 terminal is installed and running")
            print("2. Verify your login ID, password, and server name")
            print("3. Check if your account is active")
            print("4. Try running MT5 as administrator")
            print("5. Check if antivirus is blocking the connection")
            
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    main() 