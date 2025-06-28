#!/usr/bin/env python3
"""
Test script to check bot imports and dependencies
"""

import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

def test_imports():
    """Test all required imports for the bot."""
    print("Testing bot imports...")
    
    try:
        print("1. Testing telegram imports...")
        from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
        from telegram.ext import Application, ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters as TFilters
        print("✅ Telegram imports successful")
    except Exception as e:
        print(f"❌ Telegram import error: {e}")
        return False
    
    try:
        print("2. Testing httpx import...")
        import httpx
        print("✅ httpx import successful")
    except Exception as e:
        print(f"❌ httpx import error: {e}")
        return False
    
    try:
        print("3. Testing app.services.api_service import...")
        from app.services.api_service import api_service, ApiService
        print("✅ API service import successful")
    except Exception as e:
        print(f"❌ API service import error: {e}")
        return False
    
    try:
        print("4. Testing app.security.credential_manager import...")
        from app.security.credential_manager import CredentialManager
        print("✅ Credential manager import successful")
    except Exception as e:
        print(f"❌ Credential manager import error: {e}")
        return False
    
    try:
        print("5. Testing app.mt5.mt5_manager import...")
        from app.mt5.mt5_manager import MT5Manager
        print("✅ MT5 manager import successful")
    except Exception as e:
        print(f"❌ MT5 manager import error: {e}")
        return False
    
    print("✅ All imports successful!")
    return True

def test_bot_token():
    """Test if the bot token is valid."""
    print("\nTesting bot token...")
    
    try:
        import requests
        token = "8071906329:AAH4BbllY9vwwcx0vukm6t6JPQdNWnnz-aY"
        url = f"https://api.telegram.org/bot{token}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data['result']
                print(f"✅ Token is valid!")
                print(f"   Bot name: {bot_info.get('first_name', 'N/A')}")
                print(f"   Username: @{bot_info.get('username', 'N/A')}")
                return True
            else:
                print(f"❌ Token is invalid: {data.get('description', 'Unknown error')}")
                return False
        else:
            print(f"❌ Failed to validate token: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing token: {e}")
        return False

if __name__ == "__main__":
    print("="*50)
    print("BOT IMPORT DIAGNOSTICS")
    print("="*50)
    
    imports_ok = test_imports()
    token_ok = test_bot_token()
    
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    
    if imports_ok and token_ok:
        print("✅ All tests passed! The bot should work.")
    else:
        print("❌ Some tests failed. Check the errors above.")
    
    print("="*50) 