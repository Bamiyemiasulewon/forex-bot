# Bot Startup Guide - Fix for Disconnection Issues

## Problem Fixed
Your bot was disconnecting when you restarted it because of several issues:
1. **Port mismatch**: Bot was checking port 8001 but API server runs on port 8000
2. **Improper async handling**: The main function wasn't properly handling async startup
3. **Missing retry logic**: No automatic reconnection on failures
4. **Poor process management**: No proper cleanup on shutdown

## Solutions Provided

### 1. Fixed Bot Code (`app/telegram/bot.py`)
- ✅ Fixed port mismatch (8001 → 8000)
- ✅ Proper async startup handling
- ✅ Global shutdown event management
- ✅ Better error handling

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

### To Stop the Bot:
- Press `Ctrl+C` in the terminal
- The script will handle graceful shutdown

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
1. Check if API server is running: `http://127.0.0.1:8000/health`
2. Verify bot token is correct
3. Check internet connection
4. Look for error messages in logs

### Common Issues:
- **Port 8000 in use**: Stop other services using port 8000
- **Bot token invalid**: Check your TELEGRAM_TOKEN environment variable
- **API server not starting**: Check if all dependencies are installed

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

 