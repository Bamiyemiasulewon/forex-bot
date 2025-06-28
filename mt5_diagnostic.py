
import os
import sys
import subprocess
import platform

def check_python_environment():
    """Check Python environment and MT5 package."""
    print("=== Python Environment Check ===")
    print(f"Python version: {sys.version}")
    print(f"Platform: {platform.platform()}")
    
    try:
        import MetaTrader5 as mt5
        print(f"✓ MT5 package version: {mt5.__version__}")
        return True
    except ImportError as e:
        print(f"✗ MT5 package not installed: {e}")
        print("Install with: pip install MetaTrader5")
        return False
    except Exception as e:
        print(f"✗ MT5 package error: {e}")
        return False

def check_mt5_installation():
    """Check if MT5 is installed on the system."""
    print("\n=== MT5 Installation Check ===")
    
    # Common MT5 installation paths
    mt5_paths = [
        r"C:\Program Files\MetaTrader 5\terminal64.exe",
        r"C:\Program Files (x86)\MetaTrader 5\terminal64.exe",
        r"C:\Program Files\MetaTrader 5\terminal.exe",
        r"C:\Program Files (x86)\MetaTrader 5\terminal.exe",
        r"C:\Users\{}\AppData\Roaming\MetaQuotes\Terminal\Common\Files\terminal64.exe".format(os.getenv('USERNAME')),
        r"C:\Users\{}\AppData\Roaming\MetaQuotes\Terminal\Common\Files\terminal.exe".format(os.getenv('USERNAME'))
    ]
    
    found_paths = []
    for path in mt5_paths:
        if os.path.exists(path):
            print(f"✓ Found MT5 at: {path}")
            found_paths.append(path)
        else:
            print(f"✗ Not found: {path}")
    
    if not found_paths:
        print("\n❌ MetaTrader 5 not found in common locations.")
        print("Please install MetaTrader 5 from: https://www.metatrader5.com/en/download")
        return False
    
    return found_paths[0]  # Return the first found path

def check_mt5_process():
    """Check if MT5 is currently running."""
    print("\n=== MT5 Process Check ===")
    
    try:
        # Check for MT5 processes
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq terminal64.exe'], 
                              capture_output=True, text=True, shell=True)
        if 'terminal64.exe' in result.stdout:
            print("✓ MT5 terminal64.exe is running")
            return True
        
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq terminal.exe'], 
                              capture_output=True, text=True, shell=True)
        if 'terminal.exe' in result.stdout:
            print("✓ MT5 terminal.exe is running")
            return True
        
        print("✗ MT5 is not currently running")
        return False
        
    except Exception as e:
        print(f"✗ Error checking MT5 process: {e}")
        return False

def try_manual_mt5_launch():
    """Try to manually launch MT5."""
    print("\n=== Manual MT5 Launch Test ===")
    
    mt5_path = check_mt5_installation()
    if not mt5_path:
        return False
    
    try:
        print(f"Attempting to launch: {mt5_path}")
        subprocess.Popen([mt5_path], shell=True)
        print("✓ MT5 launch command sent")
        print("Please wait 10-15 seconds for MT5 to start...")
        return True
    except Exception as e:
        print(f"✗ Failed to launch MT5: {e}")
        return False

def test_mt5_connection():
    """Test basic MT5 connection."""
    print("\n=== MT5 Connection Test ===")
    
    try:
        import MetaTrader5 as mt5
        
        # Try simple initialization
        if mt5.initialize():
            print("✓ MT5 initialization successful")
            
            # Get terminal info
            terminal_info = mt5.terminal_info()
            if terminal_info:
                print(f"✓ Terminal: {terminal_info.name} (build {terminal_info.build})")
            
            mt5.shutdown()
            return True
        else:
            error = mt5.last_error()
            print(f"✗ MT5 initialization failed: {error}")
            return False
            
    except Exception as e:
        print(f"✗ MT5 connection error: {e}")
        return False

def provide_solutions():
    """Provide step-by-step solutions."""
    print("\n=== Troubleshooting Solutions ===")
    
    print("\n1. INSTALLATION ISSUES:")
    print("   - Download MetaTrader 5 from: https://www.metatrader5.com/en/download")
    print("   - Install as administrator")
    print("   - Make sure to install the 64-bit version")
    
    print("\n2. PERMISSION ISSUES:")
    print("   - Run PowerShell as Administrator")
    print("   - Right-click PowerShell → 'Run as administrator'")
    print("   - Try running the script again")
    
    print("\n3. MT5 NOT RUNNING:")
    print("   - Open MetaTrader 5 manually")
    print("   - Log in to your account")
    print("   - Keep MT5 running in the background")
    print("   - Then run the bot script")
    
    print("\n4. PYTHON PACKAGE ISSUES:")
    print("   - Reinstall MT5 package: pip uninstall MetaTrader5")
    print("   - Then: pip install MetaTrader5")
    print("   - Or try: pip install --upgrade MetaTrader5")
    
    print("\n5. FIREWALL/ANTIVIRUS:")
    print("   - Add MT5 to firewall exceptions")
    print("   - Temporarily disable antivirus")
    print("   - Check Windows Defender settings")
    
    print("\n6. ALTERNATIVE APPROACH:")
    print("   - Use a different MT5 broker")
    print("   - Create a new demo account")
    print("   - Try a different MT5 terminal version")

def main():
    print("=== MT5 Diagnostic Tool ===")
    print("This tool will help diagnose MT5 connection issues.\n")
    
    # Step 1: Check Python environment
    if not check_python_environment():
        print("\n❌ Python environment issues detected.")
        provide_solutions()
        return
    
    # Step 2: Check MT5 installation
    mt5_path = check_mt5_installation()
    if not mt5_path:
        print("\n❌ MT5 installation issues detected.")
        provide_solutions()
        return
    
    # Step 3: Check if MT5 is running
    mt5_running = check_mt5_process()
    if not mt5_running:
        print("\n⚠️  MT5 is not running. Attempting to launch...")
        if try_manual_mt5_launch():
            print("Please wait for MT5 to start, then run the bot again.")
        else:
            print("Failed to launch MT5 automatically.")
            print("Please launch MT5 manually and try again.")
        return
    
    # Step 4: Test connection
    if test_mt5_connection():
        print("\n✅ MT5 is working properly!")
        print("You should now be able to run your trading bot.")
    else:
        print("\n❌ MT5 connection issues detected.")
        provide_solutions()

if __name__ == "__main__":
    main() 