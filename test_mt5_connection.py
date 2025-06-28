import MetaTrader5 as mt5
import time
import os

# --- CONFIGURATION ---
ACCOUNT = 94067211
PASSWORD = "IgS-7mAj"
SERVER = "MetaQuotes-Demo"
MT5_PATH = r"C:\Program Files\MetaTrader 5\terminal64.exe"

def check_mt5_installation():
    """Check if MT5 is installed and accessible."""
    print("--- Checking MT5 Installation ---")
    
    # Check if the MT5 path exists
    if os.path.exists(MT5_PATH):
        print(f"✓ MT5 terminal found at: {MT5_PATH}")
    else:
        print(f"✗ MT5 terminal not found at: {MT5_PATH}")
        print("Please ensure MetaTrader 5 is installed at the specified path.")
        return False
    
    # Check if MT5 package is installed
    try:
        print(f"✓ MT5 Python package version: {mt5.__version__}")
    except Exception as e:
        print(f"✗ MT5 Python package error: {e}")
        return False
    
    return True

def try_connection_methods():
    """Try different connection methods to MT5."""
    print("\n--- Trying Connection Methods ---")
    
    # Method 1: Connect to running terminal
    print("Method 1: Connecting to running MT5 terminal...")
    if mt5.initialize():
        print("✓ Successfully connected to running MT5 terminal!")
        return True
    else:
        error = mt5.last_error()
        print(f"✗ Failed to connect to running terminal: {error}")
    
    # Method 2: Launch terminal with path
    print("\nMethod 2: Launching MT5 terminal with explicit path...")
    if mt5.initialize(path=MT5_PATH):
        print("✓ Successfully launched and connected to MT5 terminal!")
        return True
    else:
        error = mt5.last_error()
        print(f"✗ Failed to launch terminal: {error}")
    
    # Method 3: Try with server credentials
    print("\nMethod 3: Trying with server credentials...")
    if mt5.initialize(server=SERVER, login=ACCOUNT, password=PASSWORD):
        print("✓ Successfully connected with server credentials!")
        return True
    else:
        error = mt5.last_error()
        print(f"✗ Failed to connect with server credentials: {error}")
    
    return False

def test_login():
    """Test login with account credentials."""
    print("\n--- Testing Login ---")
    
    # Try to login
    if mt5.login(login=ACCOUNT, password=PASSWORD, server=SERVER):
        print("✓ Login successful!")
        return True
    else:
        error = mt5.last_error()
        print(f"✗ Login failed: {error}")
        return False

def get_account_info():
    """Get and display account information."""
    print("\n--- Account Information ---")
    
    account_info = mt5.account_info()
    if account_info is None:
        print(f"✗ Failed to get account info: {mt5.last_error()}")
        return False
    
    print(f"✓ Connected to account #{account_info.login} on {account_info.server}")
    print(f"  Balance: ${account_info.balance:.2f}")
    print(f"  Equity: ${account_info.equity:.2f}")
    print(f"  Margin: ${account_info.margin:.2f}")
    print(f"  Free Margin: ${account_info.margin_free:.2f}")
    print(f"  Profit: ${account_info.profit:.2f}")
    return True

def test_symbol_access():
    """Test access to trading symbols."""
    print("\n--- Testing Symbol Access ---")
    
    symbol = "EURUSD"
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"✗ Failed to get symbol info for {symbol}: {mt5.last_error()}")
        return False
    
    print(f"✓ Symbol {symbol} is available")
    print(f"  Point: {symbol_info.point}")
    print(f"  Digits: {symbol_info.digits}")
    print(f"  Spread: {symbol_info.spread}")
    print(f"  Trade mode: {symbol_info.trade_mode}")
    return True

def run_comprehensive_test():
    """Run a comprehensive MT5 connection test."""
    print("=== MT5 Connection Test ===")
    
    # Step 1: Check installation
    if not check_mt5_installation():
        print("\n❌ Installation check failed. Please install MetaTrader 5.")
        return False
    
    # Step 2: Try to connect
    if not try_connection_methods():
        print("\n❌ All connection methods failed.")
        return False
    
    # Step 3: Test login
    if not test_login():
        print("\n❌ Login failed.")
        return False
    
    # Step 4: Get account info
    if not get_account_info():
        print("\n❌ Failed to get account information.")
        return False
    
    # Step 5: Test symbol access
    if not test_symbol_access():
        print("\n❌ Failed to access trading symbols.")
        return False
    
    print("\n✅ All tests passed! MT5 connection is working properly.")
    return True

def cleanup():
    """Clean up MT5 connection."""
    mt5.shutdown()
    print("\n--- Connection closed ---")

if __name__ == "__main__":
    try:
        success = run_comprehensive_test()
        if success:
            print("\n🎉 MT5 is ready for trading!")
        else:
            print("\n💥 MT5 connection issues detected.")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
    finally:
        cleanup() 