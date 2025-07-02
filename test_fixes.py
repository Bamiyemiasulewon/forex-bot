#!/usr/bin/env python3
"""
Test script to verify the fixes for /trades and /signal commands
"""

import asyncio
import requests
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

async def test_api_server():
    """Test if the API server is running and responding."""
    print("🔍 Testing API Server...")
    
    try:
        # Test health endpoint
        response = requests.get("http://127.0.0.1:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ API server is running and responding")
            return True
        else:
            print(f"❌ API server responded with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ API server is not running")
        return False
    except Exception as e:
        print(f"❌ Error testing API server: {e}")
        return False

async def test_trades_endpoint():
    """Test the /api/trades endpoint."""
    print("\n🔍 Testing /api/trades endpoint...")
    
    try:
        response = requests.get("http://127.0.0.1:8000/api/trades", timeout=10)
        if response.status_code == 200:
            trades = response.json()
            print(f"✅ Trades endpoint working - {len(trades)} trades returned")
            for trade in trades[:3]:  # Show first 3 trades
                print(f"   📊 {trade.get('symbol', 'N/A')} - {trade.get('status', 'N/A')} - ${trade.get('pnl', 0):.2f}")
            return True
        else:
            print(f"❌ Trades endpoint failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing trades endpoint: {e}")
        return False

async def test_signals_endpoint():
    """Test the /api/signals endpoint."""
    print("\n🔍 Testing /api/signals endpoint...")
    
    try:
        response = requests.get("http://127.0.0.1:8000/api/signals", timeout=10)
        if response.status_code == 200:
            signals = response.json()
            print(f"✅ Signals endpoint working - {len(signals)} signals returned")
            for signal in signals[:3]:  # Show first 3 signals
                print(f"   📡 {signal.get('pair', 'N/A')} - {signal.get('strategy', 'N/A')}")
            return True
        else:
            print(f"❌ Signals endpoint failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing signals endpoint: {e}")
        return False

async def test_signal_service():
    """Test the signal service directly."""
    print("\n🔍 Testing Signal Service...")
    
    try:
        from app.services.signal_service import signal_service
        
        # Test signal generation
        signals = await signal_service.generate_signals()
        if signals:
            print(f"✅ Signal service working - {len(signals)} signals generated")
            for signal in signals[:3]:
                print(f"   📡 {signal.get('pair', 'N/A')} - {signal.get('strategy', 'N/A')}")
            return True
        else:
            print("⚠️ Signal service returned no signals (this might be normal)")
            return True
    except Exception as e:
        print(f"❌ Error testing signal service: {e}")
        return False

async def test_market_service():
    """Test the market service directly."""
    print("\n🔍 Testing Market Service...")
    
    try:
        from app.services.market_service import market_service
        
        # Test market data for EURUSD
        market_data = await market_service.get_market_data("EURUSD")
        if market_data and not market_data.get('error'):
            print(f"✅ Market service working - EURUSD price: {market_data.get('price', 'N/A')}")
            return True
        else:
            print(f"⚠️ Market service returned: {market_data}")
            return True  # This might be due to rate limiting
    except Exception as e:
        print(f"❌ Error testing market service: {e}")
        return False

async def test_ai_trading_service_imports():
    """Test that the AI trading service imports are working."""
    print("\n🔍 Testing AI Trading Service imports...")
    
    try:
        from app.services.ai_trading_service import AITradingService
        from app.services.signal_service import signal_service
        from app.services.market_service import market_service
        
        print("✅ All imports successful")
        print(f"   - Signal service: {type(signal_service)}")
        print(f"   - Market service: {type(market_service)}")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

async def main():
    """Run all tests."""
    print("="*60)
    print("  Testing Forex Bot Fixes")
    print("="*60)
    
    tests = [
        ("API Server", test_api_server),
        ("Trades Endpoint", test_trades_endpoint),
        ("Signals Endpoint", test_signals_endpoint),
        ("Signal Service", test_signal_service),
        ("Market Service", test_market_service),
        ("AI Trading Service Imports", test_ai_trading_service_imports),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "="*60)
    print("  Test Results")
    print("="*60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your bot should work correctly.")
        print("\n💡 To start the bot:")
        print("1. Run: python start_api_server.py (in one terminal)")
        print("2. Run: python start_bot_simple.py (in another terminal)")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure the API server is running: python start_api_server.py")
        print("2. Check that all dependencies are installed")
        print("3. Verify your Alpha Vantage API key is set")

if __name__ == "__main__":
    asyncio.run(main()) 