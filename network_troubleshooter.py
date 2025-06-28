#!/usr/bin/env python3
"""
Network Troubleshooter for Forex Trading Bot
This script helps diagnose and fix network connectivity issues.
"""

import socket
import subprocess
import platform
import requests
import time
import sys
import os

def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_section(title):
    print(f"\n{'-'*40}")
    print(f"  {title}")
    print(f"{'-'*40}")

def run_command(command):
    """Run a command and return the result."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def check_internet_connectivity():
    """Check basic internet connectivity."""
    print_section("Internet Connectivity Test")
    
    # Test DNS resolution
    print("Testing DNS resolution...")
    try:
        socket.gethostbyname("8.8.8.8")
        print("✅ DNS resolution working")
        dns_ok = True
    except socket.gaierror:
        print("❌ DNS resolution failed")
        dns_ok = False
    
    # Test HTTP connectivity
    print("Testing HTTP connectivity...")
    try:
        response = requests.get("http://httpbin.org/get", timeout=10)
        if response.status_code == 200:
            print("✅ HTTP connectivity working")
            http_ok = True
        else:
            print(f"❌ HTTP connectivity failed (status: {response.status_code})")
            http_ok = False
    except Exception as e:
        print(f"❌ HTTP connectivity failed: {e}")
        http_ok = False
    
    return dns_ok and http_ok

def check_telegram_api():
    """Check Telegram API connectivity."""
    print_section("Telegram API Connectivity Test")
    
    # Test DNS resolution for api.telegram.org
    print("Testing api.telegram.org DNS resolution...")
    try:
        ip = socket.gethostbyname("api.telegram.org")
        print(f"✅ api.telegram.org resolves to: {ip}")
        dns_ok = True
    except socket.gaierror as e:
        print(f"❌ Cannot resolve api.telegram.org: {e}")
        dns_ok = False
    
    # Test HTTPS connectivity to Telegram API
    print("Testing HTTPS connectivity to Telegram API...")
    try:
        response = requests.get("https://api.telegram.org", timeout=15)
        if response.status_code == 200:
            print("✅ Telegram API HTTPS connectivity working")
            https_ok = True
        else:
            print(f"❌ Telegram API HTTPS failed (status: {response.status_code})")
            https_ok = False
    except Exception as e:
        print(f"❌ Telegram API HTTPS failed: {e}")
        https_ok = False
    
    return dns_ok and https_ok

def check_local_server():
    """Check local API server."""
    print_section("Local API Server Test")
    
    # Test if port 8000 is open
    print("Testing if port 8000 is open...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('127.0.0.1', 8000))
        sock.close()
        
        if result == 0:
            print("✅ Port 8000 is open")
            port_ok = True
        else:
            print("❌ Port 8000 is not open")
            port_ok = False
    except Exception as e:
        print(f"❌ Error testing port 8000: {e}")
        port_ok = False
    
    # Test HTTP connectivity to local server
    print("Testing HTTP connectivity to local server...")
    try:
        response = requests.get("http://127.0.0.1:8000/health", timeout=10)
        if response.status_code == 200:
            print("✅ Local API server responding")
            server_ok = True
        else:
            print(f"❌ Local API server returned status: {response.status_code}")
            server_ok = False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to local API server")
        server_ok = False
    except Exception as e:
        print(f"❌ Error connecting to local API server: {e}")
        server_ok = False
    
    return port_ok and server_ok

def check_dns_settings():
    """Check and suggest DNS settings."""
    print_section("DNS Settings Check")
    
    system = platform.system()
    
    if system == "Windows":
        print("Checking Windows DNS settings...")
        success, output, error = run_command("ipconfig /all | findstr DNS")
        if success:
            print("Current DNS settings:")
            print(output)
        else:
            print("Could not retrieve DNS settings")
        
        print("\nTo change DNS settings on Windows:")
        print("1. Open Network & Internet settings")
        print("2. Click on 'Change adapter options'")
        print("3. Right-click your network adapter → Properties")
        print("4. Select 'Internet Protocol Version 4 (TCP/IPv4)' → Properties")
        print("5. Select 'Use the following DNS server addresses'")
        print("6. Set Preferred DNS: 8.8.8.8")
        print("7. Set Alternate DNS: 1.1.1.1")
        
    elif system == "Linux":
        print("Checking Linux DNS settings...")
        success, output, error = run_command("cat /etc/resolv.conf")
        if success:
            print("Current DNS settings:")
            print(output)
        else:
            print("Could not retrieve DNS settings")
        
        print("\nTo change DNS settings on Linux:")
        print("1. Edit /etc/resolv.conf (requires sudo)")
        print("2. Add: nameserver 8.8.8.8")
        print("3. Add: nameserver 1.1.1.1")
        
    elif system == "Darwin":  # macOS
        print("Checking macOS DNS settings...")
        success, output, error = run_command("scutil --dns | grep nameserver")
        if success:
            print("Current DNS settings:")
            print(output)
        else:
            print("Could not retrieve DNS settings")
        
        print("\nTo change DNS settings on macOS:")
        print("1. Open System Preferences → Network")
        print("2. Select your network connection → Advanced")
        print("3. Go to DNS tab")
        print("4. Add: 8.8.8.8 and 1.1.1.1")

def check_firewall():
    """Check firewall settings."""
    print_section("Firewall Check")
    
    system = platform.system()
    
    if system == "Windows":
        print("Checking Windows Firewall...")
        success, output, error = run_command("netsh advfirewall show allprofiles state")
        if success:
            print("Firewall status:")
            print(output)
        else:
            print("Could not retrieve firewall status")
        
        print("\nTo allow Python through Windows Firewall:")
        print("1. Open Windows Defender Firewall")
        print("2. Click 'Allow an app or feature through Windows Defender Firewall'")
        print("3. Click 'Change settings'")
        print("4. Find Python in the list or click 'Allow another app'")
        print("5. Browse to your Python executable and add it")
        
    elif system == "Linux":
        print("Checking Linux firewall...")
        success, output, error = run_command("sudo ufw status")
        if success:
            print("Firewall status:")
            print(output)
        else:
            print("Could not retrieve firewall status")
        
        print("\nTo allow Python through Linux firewall:")
        print("sudo ufw allow out 443/tcp  # HTTPS")
        print("sudo ufw allow out 80/tcp   # HTTP")
        
    elif system == "Darwin":  # macOS
        print("Checking macOS firewall...")
        success, output, error = run_command("sudo pfctl -s all")
        if success:
            print("Firewall status:")
            print(output)
        else:
            print("Could not retrieve firewall status")

def suggest_solutions():
    """Provide solutions based on test results."""
    print_section("Troubleshooting Solutions")
    
    print("If you're experiencing network issues, try these solutions:")
    print("\n1. **DNS Issues:**")
    print("   - Change DNS to Google (8.8.8.8) or Cloudflare (1.1.1.1)")
    print("   - Flush DNS cache: ipconfig /flushdns (Windows)")
    print("   - Restart your router/modem")
    
    print("\n2. **Local Server Issues:**")
    print("   - Start your local API server: python app/main.py")
    print("   - Check if port 8000 is not used by another application")
    print("   - Verify the server is running on http://127.0.0.1:8000")
    
    print("\n3. **Firewall/Antivirus:**")
    print("   - Allow Python through your firewall")
    print("   - Temporarily disable antivirus to test")
    print("   - Check if corporate firewall is blocking connections")
    
    print("\n4. **Network Issues:**")
    print("   - Try using a different network (mobile hotspot)")
    print("   - Check if you're behind a proxy")
    print("   - Restart your network adapter")
    
    print("\n5. **Bot Token Issues:**")
    print("   - Verify your bot token is correct")
    print("   - Check if the bot is not banned or restricted")
    print("   - Try creating a new bot token")

def main():
    """Main troubleshooting function."""
    print_header("Forex Trading Bot Network Troubleshooter")
    
    print("This script will help diagnose network connectivity issues.")
    print("Running comprehensive network tests...")
    
    # Run all tests
    internet_ok = check_internet_connectivity()
    telegram_ok = check_telegram_api()
    local_ok = check_local_server()
    
    # Check DNS and firewall
    check_dns_settings()
    check_firewall()
    
    # Summary
    print_section("Test Summary")
    print(f"Internet Connectivity: {'✅ OK' if internet_ok else '❌ FAILED'}")
    print(f"Telegram API: {'✅ OK' if telegram_ok else '❌ FAILED'}")
    print(f"Local API Server: {'✅ OK' if local_ok else '❌ FAILED'}")
    
    if internet_ok and telegram_ok and local_ok:
        print("\n🎉 All tests passed! Your network should work fine.")
    else:
        print("\n⚠️ Some tests failed. Check the solutions below.")
        suggest_solutions()
    
    print("\n" + "="*60)
    print("Troubleshooting complete!")

if __name__ == "__main__":
    main() 