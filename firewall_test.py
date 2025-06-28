#!/usr/bin/env python3
"""
Firewall Test and Management Script
This script helps test and manage Windows firewall settings for the Forex Trading Bot.
"""

import subprocess
import sys
import time
import requests
import socket

def run_command(command):
    """Run a command and return the result."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def check_firewall_status():
    """Check current firewall status."""
    print("🔍 Checking current firewall status...")
    
    success, output, error = run_command("netsh advfirewall show allprofiles state")
    if success:
        print("Current firewall status:")
        print(output)
        return True
    else:
        print(f"❌ Error checking firewall status: {error}")
        return False

def disable_firewall():
    """Temporarily disable Windows firewall."""
    print("🛑 Temporarily disabling Windows firewall...")
    
    success, output, error = run_command("netsh advfirewall set allprofiles state off")
    if success:
        print("✅ Firewall disabled successfully")
        return True
    else:
        print(f"❌ Error disabling firewall: {error}")
        return False

def enable_firewall():
    """Re-enable Windows firewall."""
    print("🛡️ Re-enabling Windows firewall...")
    
    success, output, error = run_command("netsh advfirewall set allprofiles state on")
    if success:
        print("✅ Firewall enabled successfully")
        return True
    else:
        print(f"❌ Error enabling firewall: {error}")
        return False

def test_connectivity():
    """Test connectivity to various services."""
    print("\n🌐 Testing connectivity...")
    
    tests = [
        ("Internet (Google)", "https://www.google.com"),
        ("Telegram API", "https://api.telegram.org"),
        ("Local Server", "http://127.0.0.1:8000/health")
    ]
    
    results = {}
    
    for name, url in tests:
        try:
            if "127.0.0.1" in url:
                # Test local server
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    print(f"✅ {name}: Connected")
                    results[name] = True
                else:
                    print(f"❌ {name}: HTTP {response.status_code}")
                    results[name] = False
            else:
                # Test external services
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    print(f"✅ {name}: Connected")
                    results[name] = True
                else:
                    print(f"❌ {name}: HTTP {response.status_code}")
                    results[name] = False
        except requests.exceptions.ConnectionError:
            print(f"❌ {name}: Connection refused")
            results[name] = False
        except requests.exceptions.Timeout:
            print(f"⏰ {name}: Timeout")
            results[name] = False
        except Exception as e:
            print(f"❌ {name}: Error - {e}")
            results[name] = False
    
    return results

def add_python_to_firewall():
    """Add Python to Windows firewall exceptions."""
    print("\n🔧 Adding Python to firewall exceptions...")
    
    # Get Python executable path
    python_path = sys.executable
    print(f"Python path: {python_path}")
    
    # Add Python to firewall
    command = f'netsh advfirewall firewall add rule name="Python Forex Bot" dir=out action=allow program="{python_path}" enable=yes'
    success, output, error = run_command(command)
    
    if success:
        print("✅ Python added to firewall exceptions")
        return True
    else:
        print(f"❌ Error adding Python to firewall: {error}")
        return False

def main():
    """Main function."""
    print("="*60)
    print("  Windows Firewall Test and Management")
    print("="*60)
    
    # Check current status
    check_firewall_status()
    
    # Test connectivity with firewall enabled
    print("\n📊 Testing connectivity with firewall ENABLED:")
    results_enabled = test_connectivity()
    
    # Ask user if they want to test with firewall disabled
    print("\n" + "="*60)
    print("⚠️  WARNING: Disabling firewall temporarily for testing")
    print("This will make your system less secure!")
    print("="*60)
    
    response = input("\nDo you want to temporarily disable firewall for testing? (y/N): ").strip().lower()
    
    if response == 'y':
        # Disable firewall
        if disable_firewall():
            print("\n⏳ Waiting 5 seconds for firewall to disable...")
            time.sleep(5)
            
            # Test connectivity with firewall disabled
            print("\n📊 Testing connectivity with firewall DISABLED:")
            results_disabled = test_connectivity()
            
            # Compare results
            print("\n📈 Comparison:")
            for service in results_enabled:
                enabled = results_enabled[service]
                disabled = results_disabled.get(service, False)
                
                if enabled and disabled:
                    print(f"✅ {service}: Works in both cases")
                elif not enabled and disabled:
                    print(f"🔧 {service}: Works only with firewall disabled (firewall blocking)")
                elif enabled and not disabled:
                    print(f"❓ {service}: Works only with firewall enabled (unusual)")
                else:
                    print(f"❌ {service}: Doesn't work in either case (other issue)")
            
            # Re-enable firewall
            print("\n🛡️ Re-enabling firewall...")
            enable_firewall()
            
            # Add Python to firewall if needed
            if any(not results_enabled[service] and results_disabled.get(service, False) for service in results_enabled):
                print("\n🔧 Some services work with firewall disabled but not enabled.")
                add_response = input("Add Python to firewall exceptions? (y/N): ").strip().lower()
                if add_response == 'y':
                    add_python_to_firewall()
        else:
            print("❌ Failed to disable firewall. You may need administrator privileges.")
    else:
        print("✅ Firewall test skipped. Keeping firewall enabled.")
    
    print("\n" + "="*60)
    print("Firewall test complete!")
    print("="*60)

if __name__ == "__main__":
    main() 