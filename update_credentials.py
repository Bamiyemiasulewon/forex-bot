import MetaTrader5 as mt5
import os

def test_credentials(account, password, server):
    """Test specific credentials."""
    print(f"\n--- Testing Credentials ---")
    print(f"Account: {account}")
    print(f"Server: {server}")
    print(f"Password: {'*' * len(password)}")
    
    # Initialize connection
    if not mt5.initialize():
        print("✗ Failed to initialize MT5")
        return False
    
    # Try to login
    if mt5.login(login=account, password=password, server=server):
        print("✓ Login successful!")
        
        # Get account info
        account_info = mt5.account_info()
        if account_info:
            print(f"✓ Account Info:")
            print(f"  Login: {account_info.login}")
            print(f"  Server: {account_info.server}")
            print(f"  Balance: ${account_info.balance:.2f}")
            print(f"  Equity: ${account_info.equity:.2f}")
            print(f"  Type: {account_info.trade_mode}")
        
        mt5.shutdown()
        return True
    else:
        error = mt5.last_error()
        print(f"✗ Login failed: {error}")
        mt5.shutdown()
        return False

def main():
    print("=== MT5 Credentials Updater ===")
    print("This script will help you test and update your MT5 credentials.")
    
    # Current credentials to test
    current_account = 94067211
    current_password = "IgS-7mAj"
    current_server = "MetaQuotes-Demo"
    MT5_PATH = r"C:\Program Files\MetaTrader 5\terminal64.exe"
    # Common demo server alternatives
    demo_servers = [
        "MetaQuotes-Demo",
        "MetaQuotes-Demo01", 
        "MetaQuotes-Demo02",
        "MetaQuotes-Demo03",
        "MetaQuotes-Demo04",
        "MetaQuotes-Demo05",
        "MetaQuotes-Demo06",
        "MetaQuotes-Demo07",
        "MetaQuotes-Demo08",
        "MetaQuotes-Demo09",
        "MetaQuotes-Demo10",
        "MetaQuotes-Demo11",
        "MetaQuotes-Demo12",
        "MetaQuotes-Demo13",
        "MetaQuotes-Demo14",
        "MetaQuotes-Demo15",
        "MetaQuotes-Demo16",
        "MetaQuotes-Demo17",
        "MetaQuotes-Demo18",
        "MetaQuotes-Demo19",
        "MetaQuotes-Demo20",
        "MetaQuotes-Demo21",
        "MetaQuotes-Demo22",
        "MetaQuotes-Demo23",
        "MetaQuotes-Demo24",
        "MetaQuotes-Demo25",
        "MetaQuotes-Demo26",
        "MetaQuotes-Demo27",
        "MetaQuotes-Demo28",
        "MetaQuotes-Demo29",
        "MetaQuotes-Demo30",
        "MetaQuotes-Demo31",
        "MetaQuotes-Demo32",
        "MetaQuotes-Demo33",
        "MetaQuotes-Demo34",
        "MetaQuotes-Demo35",
        "MetaQuotes-Demo36",
        "MetaQuotes-Demo37",
        "MetaQuotes-Demo38",
        "MetaQuotes-Demo39",
        "MetaQuotes-Demo40",
        "MetaQuotes-Demo41",
        "MetaQuotes-Demo42",
        "MetaQuotes-Demo43",
        "MetaQuotes-Demo44",
        "MetaQuotes-Demo45",
        "MetaQuotes-Demo46",
        "MetaQuotes-Demo47",
        "MetaQuotes-Demo48",
        "MetaQuotes-Demo49",
        "MetaQuotes-Demo50"
    ]
    
    print(f"\nCurrent credentials in bot:")
    print(f"Account: {current_account}")
    print(f"Server: {current_server}")
    print(f"Password: {'*' * len(current_password)}")
    
    # Test current credentials
    if test_credentials(current_account, current_password, current_server):
        print("\n✅ Current credentials are working!")
        return
    
    print("\n❌ Current credentials failed. Let's try some common alternatives...")
    
    print(f"\nTesting {len(demo_servers)} different demo servers...")
    
    for i, server in enumerate(demo_servers, 1):
        print(f"\n[{i}/{len(demo_servers)}] Testing server: {server}")
        if test_credentials(current_account, current_password, server):
            print(f"\n🎉 Found working server: {server}")
            print(f"Update your bot with:")
            print(f"SERVER = \"{server}\"")
            return
        if i % 10 == 0:
            print(f"Progress: {i}/{len(demo_servers)} servers tested")
    
    print("\n❌ No working server found with current credentials.")
    print("\nPossible solutions:")
    print("1. Check if your MT5 demo account is still active")
    print("2. Try creating a new demo account")
    print("3. Verify the account number and password")
    print("4. Check if the MT5 terminal is properly configured")
    
    # Ask for manual input
    print("\n--- Manual Credential Test ---")
    try:
        new_account = input("Enter account number (or press Enter to skip): ").strip()
        if new_account:
            new_password = input("Enter password: ").strip()
            new_server = input("Enter server name: ").strip()
            
            if new_account and new_password and new_server:
                if test_credentials(int(new_account), new_password, new_server):
                    print(f"\n✅ Manual credentials work!")
                    print(f"Update your bot with:")
                    print(f"ACCOUNT = {new_account}")
                    print(f"PASSWORD = \"{new_password}\"")
                    print(f"SERVER = \"{new_server}\"")
                else:
                    print("❌ Manual credentials also failed.")
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\nError during manual input: {e}")

if __name__ == "__main__":
    main() 