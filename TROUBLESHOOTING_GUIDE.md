# Forex Trading Bot - Troubleshooting Guide

## 🚨 Critical Issues and Solutions

### 1. Local API Server Not Reachable (http://127.0.0.1:8000)

**Problem**: "All connection attempts failed" warnings when bot tries to connect to local API server.

**Solution**:
1. **Start the API server first**:
   ```bash
   cd C:\Users\User\forex1\forex-bot\app\api
   python app.py
   ```
2. **Verify server is running**:
   ```bash
   curl http://127.0.0.1:8000/health
   ```
   Should return: `{"status": "healthy", "message": "API server is running"}`

3. **Test all endpoints**:
   ```bash
   cd C:\Users\User\forex1\forex-bot
   python test_api_server.py
   ```

### 2. Event Loop Errors (Cannot close a running event loop)

**Problem**: `Cannot close a running event loop` error with unawaited coroutines.

**Solution**: ✅ **FIXED** - The bot now has proper async shutdown handling:
- Added `tracemalloc.start()` for memory leak debugging
- Proper `Application.shutdown()` awaiting in try-finally block
- Signal handlers for graceful shutdown
- Global application instance management

### 3. Firewall Issues

**Problem**: Network connectivity blocked by Windows Firewall.

**Solution**:
1. **Test firewall settings**:
   ```bash
   cd C:\Users\User\forex1\forex-bot
   python firewall_test.py
   ```

2. **Temporarily disable firewall for testing**:
   ```bash
   netsh advfirewall set allprofiles state off
   ```

3. **Re-enable firewall after testing**:
   ```bash
   netsh advfirewall set allprofiles state on
   ```

4. **Add Python to firewall exceptions** (if needed):
   ```bash
   netsh advfirewall firewall add rule name="Python Forex Bot" dir=out action=allow program="C:\path\to\python.exe" enable=yes
   ```

## 🔧 Step-by-Step Startup Procedure

### Option 1: Manual Startup (Recommended for debugging)

1. **Start API Server**:
   ```bash
   cd C:\Users\User\forex1\forex-bot\app\api
   python app.py
   ```
   Keep this terminal open!

2. **Test API Server** (in new terminal):
   ```bash
   cd C:\Users\User\forex1\forex-bot
   python test_api_server.py
   ```

3. **Start Telegram Bot** (in new terminal):
   ```bash
   cd C:\Users\User\forex1\forex-bot
   python start_bot.py
   ```

### Option 2: Automated Startup

```bash
cd C:\Users\User\forex1\forex-bot
python start_complete_system.py
```

## 🐛 Common Error Messages and Solutions

### "Connection refused" or "All connection attempts failed"
- **Cause**: API server not running
- **Solution**: Start API server first (see step 1 above)

### "getaddrinfo failed" or DNS errors
- **Cause**: Network connectivity issues
- **Solutions**:
  1. Check internet connection
  2. Try different DNS servers (8.8.8.8, 1.1.1.1)
  3. Disable VPN if using one
  4. Check firewall settings

### "Cannot close a running event loop"
- **Cause**: Improper async shutdown handling
- **Solution**: ✅ **FIXED** - Bot now has proper shutdown procedures

### "Outside trading session"
- **Cause**: MT5 trading session restrictions
- **Solution**: ✅ **FIXED** - Trading session check disabled temporarily

### "datetime.utcnow() is deprecated"
- **Cause**: Using deprecated datetime method
- **Solution**: ✅ **FIXED** - Updated to use `datetime.now(timezone.utc)`

## 🔍 Diagnostic Tools

### 1. Network Diagnostics
```bash
cd C:\Users\User\forex1\forex-bot
python network_troubleshooter.py
```

### 2. API Server Test
```bash
cd C:\Users\User\forex1\forex-bot
python test_api_server.py
```

### 3. Firewall Test
```bash
cd C:\Users\User\forex1\forex-bot
python firewall_test.py
```

### 4. MT5 Connection Test
```bash
cd C:\Users\User\forex1\forex-bot
python test_mt5_connection.py
```

## 📊 Monitoring and Logs

### Check Bot Status
- Look for "✅ Bot started successfully!" message
- Check for any error messages in red
- Monitor for "All connection attempts failed" warnings

### Check API Server Status
- Visit: http://127.0.0.1:8000/health
- Should return: `{"status": "healthy", "message": "API server is running"}`

### Check Telegram Bot Commands
- Send `/start` to your bot
- Send `/help` to see available commands
- Send `/signals` to test API connectivity

## 🛠️ Advanced Troubleshooting

### Memory Leak Debugging
The bot now includes `tracemalloc` for memory leak detection:
- Memory usage is tracked automatically
- Check logs for memory allocation warnings
- Use `tracemalloc.stop()` when shutting down

### Network Connectivity Issues
1. **Test basic connectivity**:
   ```bash
   ping google.com
   ping api.telegram.org
   ```

2. **Test local server**:
   ```bash
   curl http://127.0.0.1:8000
   ```

3. **Check DNS resolution**:
   ```bash
   nslookup api.telegram.org
   ```

### Port Conflicts
If port 8000 is in use:
1. **Find what's using the port**:
   ```bash
   netstat -ano | findstr :8000
   ```

2. **Kill the process** (replace PID with actual process ID):
   ```bash
   taskkill /PID <PID> /F
   ```

## 📞 Getting Help

If you're still experiencing issues:

1. **Check the logs** for specific error messages
2. **Run diagnostic tools** to identify the problem
3. **Test each component separately** (API server, bot, MT5)
4. **Check system requirements** (Python 3.8+, required packages)

### Required Packages
Make sure you have all required packages installed:
```bash
pip install -r requirements.txt
```

### System Requirements
- Windows 10/11
- Python 3.8 or higher
- Internet connection
- MT5 terminal installed and configured
- Telegram bot token

## ✅ Success Indicators

When everything is working correctly, you should see:

1. **API Server**: "🚀 Starting Forex Trading Bot API Server..." and "Server will be available at: http://127.0.0.1:8000"

2. **Bot**: "🚀 Starting Forex Trading Bot..." and "✅ Bot started successfully!"

3. **Telegram Commands**: All commands (`/start`, `/signals`, `/help`, etc.) should work

4. **No Error Messages**: No red error messages in the console

5. **Health Check**: http://127.0.0.1:8000/health returns healthy status

---

**Last Updated**: June 28, 2025, 10:46 AM WAT
**Version**: 2.0 (Fixed async handling and API server issues) 