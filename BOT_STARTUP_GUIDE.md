# Bot Startup Guide - Fix for Disconnection Issues

## Problem Fixed
Your bot was disconnecting when you restarted it because of several issues:
1. **Port mismatch**: Bot was checking port 8001 but API server runs on port 8000
2. **Improper async handling**: The main function wasn't properly handling async startup
3. **Missing retry logic**: No automatic reconnection on failures
4. **Poor process management**: No proper cleanup on shutdown
5. **MT5 Connection Error**: "'NoneType' object has no attribute 'get'" when API server not running

## Solutions Provided

### 1. Fixed Bot Code (`app/telegram/bot.py`)
- ✅ Fixed port mismatch (8001 → 8000)
- ✅ Proper async startup handling
- ✅ Global shutdown event management
- ✅ Better error handling
- ✅ **Fixed MT5 connection error handling**
- ✅ **Increased timeouts for MT5 operations**

### 2. New Startup Scripts

#### Option A: Simple Bot Only (`start_bot_simple.py`)
```bash
python start_bot_simple.py
```
- Starts only the Telegram bot
- Assumes API server is already running
- Includes automatic retry logic
- Best for development/testing

#### Option B: Complete System (`start_complete_bot.py`) - **RECOMMENDED**
```bash
python start_complete_bot.py
```
- Starts both API server and Telegram bot
- Automatic retry logic for both services
- Service monitoring and health checks
- Proper cleanup on shutdown
- **Best for production deployment**

#### Option C: API Server Only (`start_api_server.py`)
```bash
python start_api_server.py
```
- Starts only the API server
- Useful for testing and development
- Quick startup for API testing

### 3. Test Script (`test_api_connection.py`)
```bash
python test_api_connection.py
```
- Tests if API server is running correctly
- Verifies all endpoints are accessible
- Checks bot API service integration
- **Use this to diagnose connection issues**

## How to Use

### For Development (API server already running):
```bash
cd forex-bot
python start_bot_simple.py
```

### For Production (starts everything):
```bash
cd forex-bot
python start_complete_bot.py
```

### To Test API Connection:
```bash
cd forex-bot
python test_api_connection.py
```

### To Stop the Bot:
- Press `Ctrl+C` in the terminal
- The script will handle graceful shutdown

## MT5 Connection Error Fix

### The Problem:
When you tried to connect to MT5, you got: `❌ **Connection failed:** 'NoneType' object has no attribute 'get'`

### The Cause:
This happened because the API server wasn't running, so the bot's API call returned `None`, but the code tried to call `.get()` on `None`.

### The Fix:
- ✅ Added proper null checks in all MT5 functions
- ✅ Better error messages when API server is not running
- ✅ Clear instructions to start the server first

### Now the bot will show:
```
❌ **Connection Failed:** API server is not running. Please start the server first.
```

Instead of the confusing error message.

## Timeout Fixes

### The Problem:
API calls were timing out during MT5 operations, causing connection failures.

### The Fix:
- ✅ **Increased API timeouts**: 60 seconds for MT5 operations (was 15 seconds)
- ✅ **Better MT5 connection logic**: Multiple connection methods with fallbacks
- ✅ **Improved error messages**: More informative error details
- ✅ **Timeout handling**: Proper timeout handling in test scripts

### MT5 Connection Improvements:
- **Method 1**: Connect to running MT5 terminal
- **Method 2**: Launch MT5 with explicit path
- **Method 3**: Connect with server credentials
- **Better error reporting**: Clear error messages for each failure

## Features of the New Startup Scripts

### Automatic Retry Logic
- Bot automatically restarts if it crashes
- Exponential backoff (10s, 20s, 40s, 80s, 160s)
- Maximum 5 retry attempts

### Service Monitoring
- Checks API server health every 30 seconds
- Logs warnings if services are down
- Graceful error handling

### Proper Cleanup
- Stops all processes on shutdown
- Cleans up resources properly
- Handles Ctrl+C gracefully

### Better Logging
- Clear status messages
- Error details for debugging
- Progress indicators

## Troubleshooting

### If bot still disconnects:
1. **Run the test script first**: `python test_api_connection.py`
2. Check if API server is running: `http://127.0.0.1:8000/health`
3. Verify bot token is correct
4. Check internet connection
5. Look for error messages in logs

### If MT5 connection fails:
1. **Make sure API server is running**: Use `start_complete_bot.py`
2. Check your MT5 credentials
3. Verify MT5 terminal is installed and running
4. Check if MetaTrader5 package is installed: `pip install MetaTrader5`

### Common Issues:
- **Port 8000 in use**: Stop other services using port 8000
- **Bot token invalid**: Check your TELEGRAM_TOKEN environment variable
- **API server not starting**: Check if all dependencies are installed
- **MT5 not connecting**: Make sure MT5 terminal is running and credentials are correct

## Deployment Tips

### For Production:
1. Use `start_complete_bot.py` - it handles everything
2. Set up proper environment variables
3. Use a process manager like `systemd` or `supervisor`
4. Monitor logs for any issues

### Environment Variables:
```bash
export TELEGRAM_TOKEN="your_bot_token_here"
export HOST="127.0.0.1"
export PORT="8000"
```

## Migration from Old Scripts

### Old way (causing disconnections):
```bash
python start_bot.py  # ❌ Old script with issues
```

### New way (stable):
```bash
python start_complete_bot.py  # ✅ New stable script
```

The new scripts are backward compatible and will work with your existing bot configuration.

## Quick Test Checklist

Before using your bot, run this checklist:

1. **Test API server**: `python test_api_connection.py`
2. **Start complete system**: `python start_complete_bot.py`
3. **Test bot commands**: Try `/start` and `/help` in Telegram
4. **Test MT5 connection**: Try `/connect` with your credentials

If all steps pass, your bot is ready for use!

 