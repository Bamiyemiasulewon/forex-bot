import MetaTrader5 as mt5

# --- CONFIGURATION ---
# Make sure to use the same credentials as in your main bot
ACCOUNT = 90404609
PASSWORD = "Mt1ms4Q*" 
SERVER = "MexAtlantic-Demo"
MT5_PATH = r"C:\Program Files\MetaTrader 5\terminal64.exe"

def run_test():
    """Runs a minimal test to check the MT5 connection."""
    print("--- Running MT5 Connection Test ---")
    print(f"MT5 package version: {mt5.__version__}")
    
    # Initialize connection
    if not mt5.initialize(server=SERVER, login=ACCOUNT, password=PASSWORD):
        print(f"Initialization failed. Error code: {mt5.last_error()}")
        mt5.shutdown()
        return

    print("Initialization successful.")

    # Check terminal info
    terminal_info = mt5.terminal_info()
    if not terminal_info:
        print(f"Failed to get terminal info: {mt5.last_error()}")
        mt5.shutdown()
        return
    print(f"Connected to MT5 terminal: {terminal_info.name} (build {terminal_info.build})")

    # Check account info
    account_info = mt5.account_info()
    if not account_info:
        print(f"Failed to get account info: {mt5.last_error()}")
        mt5.shutdown()
        return
    print(f"Connected to account #{account_info.login} on {account_info.server}.")
    print(f"Account Info: {account_info}")

    # Shutdown connection
    mt5.shutdown()
    print("--- Test Complete ---")

if __name__ == "__main__":
    run_test() 