#!/usr/bin/env python3
"""
Quick Status Checker
This script quickly checks the status of all bot components.
"""

import requests
import sys
import os

def check_api_server():
    """Check if API server is running."""
    try:
        response = requests.get("http://127.0.0.1:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ API Server: Running")
            print(f"   Status: {data.get('status', 'unknown')}")
            print(f"   Bot Status: {data.get('bot_status', 'unknown')}")
            print(f"   MT5 Status: {data.get('mt5_status', 'unknown')}")
            return True
        else:
            print(f"❌ API Server: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API Server: {e}")
        return False

def check_mt5_status():
    """Check MT5 connection status."""
    try:
        response = requests.get("http://127.0.0.1:8000/api/mt5/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("connected"):
                print("✅ MT5: Connected")
                account = data.get("account", {})
                print(f"   Account: {account.get('login', 'N/A')}")
                print(f"   Server: {account.get('server', 'N/A')}")
                print(f"   Balance: ${account.get('balance', 0):,.2f}")
            else:
                print("❌ MT5: Not Connected")
                print(f"   Error: {data.get('error', 'Unknown error')}")
            return True
        else:
            print(f"❌ MT5 Status: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ MT5 Status: {e}")
        return False

def check_bot_commands():
    """Check if bot commands are accessible."""
    try:
        response = requests.get("http://127.0.0.1:8000/api/signals", timeout=10)
        if response.status_code == 200:
            print("✅ Bot Commands: Working")
            return True
        else:
            print(f"❌ Bot Commands: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Bot Commands: {e}")
        return False

def main():
    """Main function."""
    print("="*50)
    print("  Bot Status Check")
    print("="*50)
    
    api_ok = check_api_server()
    print()
    
    if api_ok:
        mt5_ok = check_mt5_status()
        print()
        commands_ok = check_bot_commands()
        print()
        
        print("="*50)
        print("  Summary")
        print("="*50)
        
        if api_ok and commands_ok:
            print("🎉 Bot is ready to use!")
            if mt5_ok:
                print("✅ MT5 is connected and ready for trading")
            else:
                print("⚠️  MT5 is not connected - use /connect in Telegram")
        else:
            print("❌ Some components are not working")
            print("Please check the errors above")
    else:
        print("❌ API server is not running")
        print("Please start the server: python start_api_server.py")
    
    print("\n💡 Next steps:")
    print("1. If API server is not running: python start_api_server.py")
    print("2. If MT5 is not connected: Use /connect in Telegram")
    print("3. To start the complete system: python start_complete_bot.py")

if __name__ == "__main__":
    main() 