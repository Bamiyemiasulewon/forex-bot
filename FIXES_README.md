# Forex Bot Fixes - /trades and /signal Commands

## Issues Fixed

### 1. `/trades` Command Error
**Problem**: The `/trades` command was showing "😕 An error occurred while fetching today's trades. Please try again later."

**Root Cause**: The API server was not running, so the bot couldn't fetch trade data.

**Solution**: 
- Created `start_api_server.py` to start the FastAPI server
- The API server provides mock trade data for testing
- Added proper error handling in the bot commands

### 2. `/signal` Command Not Fetching Data
**Problem**: The `/signal` command wasn't fetching any data.

**Root Cause**: Missing imports in the AI trading service for `signal_service` and `market_service`.

**Solution**:
- Added missing imports in `ai_trading_service.py`:
  ```python
  from app.services.signal_service import signal_service
  from app.services.market_service import market_service
  ```

## How to Use the Fixes

### Option 1: Start API Server Only
If you just want to test the bot commands:

1. **Start the API server**:
   ```bash
   python start_api_server.py
   ```

2. **In another terminal, start the bot**:
   ```bash
   python start_bot_simple.py
   ```

### Option 2: Start Both Together
For a complete setup:

1. **Start both API server and bot together**:
   ```bash
   python start_bot_with_api.py
   ```

### Option 3: Test the Fixes
To verify everything is working:

1. **Run the test script**:
   ```bash
   python test_fixes.py
   ```

## What Each Script Does

### `start_api_server.py`
- Starts the FastAPI server on `http://127.0.0.1:8000`
- Provides endpoints for `/api/trades`, `/api/signals`, etc.
- Returns mock data for testing

### `start_bot_with_api.py`
- Starts the API server in a background process
- Waits for the API server to be ready
- Starts the Telegram bot
- Handles graceful shutdown of both processes

### `test_fixes.py`
- Tests if the API server is running
- Tests the `/api/trades` endpoint
- Tests the `/api/signals` endpoint
- Tests the signal and market services
- Verifies all imports are working

## API Endpoints Available

- `GET /health` - Health check
- `GET /api/trades` - Get trade history (mock data)
- `GET /api/signals` - Get trading signals (mock data)
- `GET /api/market/{pair}` - Get market data for a pair
- `GET /api/risk/{pair}/{risk%}/{sl_pips}` - Calculate position size
- `GET /api/pipcalc/{pair}/{trade_size}` - Calculate pip value

## Bot Commands That Should Now Work

- `/trades` - Show today's trades
- `/trades_today` - Show detailed daily trading status
- `/history` - Show detailed trade history
- `/signal EURUSD` - Get trading signal for EURUSD
- `/signals` - Get latest trading signals
- `/market EURUSD` - Get market data for EURUSD

## Troubleshooting

### If `/trades` still shows an error:
1. Make sure the API server is running: `python start_api_server.py`
2. Check if port 8000 is available
3. Run the test script: `python test_fixes.py`

### If `/signal` still doesn't work:
1. Check that all dependencies are installed
2. Verify your Alpha Vantage API key is set in `app/utils/secrets.py`
3. The signal service might be rate-limited by Alpha Vantage

### If the bot won't start:
1. Check your Telegram bot token is set correctly
2. Make sure all Python dependencies are installed
3. Check the logs for specific error messages

## Files Modified

1. **`app/services/ai_trading_service.py`** - Added missing imports
2. **`start_api_server.py`** - Created API server startup script
3. **`start_bot_with_api.py`** - Created combined startup script
4. **`test_fixes.py`** - Created test script

## Next Steps

1. Test the bot commands to ensure they work
2. If you want real data instead of mock data, update the API endpoints
3. Set up your Alpha Vantage API key for real market data
4. Configure your MT5 connection for real trading

## Support

If you encounter any issues:
1. Run `python test_fixes.py` to diagnose problems
2. Check the console output for error messages
3. Make sure all required services are running 