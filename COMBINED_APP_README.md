# Combined Forex Trading Bot

This is a combined FastAPI and Telegram bot application that runs both services in a single process. The application provides a unified entry point for running your forex trading bot with both API endpoints and Telegram bot functionality.

## 🚀 Quick Start

### Prerequisites

1. Python 3.8+
2. Required environment variables:
   - `TELEGRAM_TOKEN` - Your Telegram bot token
   - `HOST` - Server host (default: 0.0.0.0)
   - `PORT` - Server port (default: 8000)
   - `RELOAD` - Enable auto-reload (default: false)

### Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables:**
   ```bash
   export TELEGRAM_TOKEN="your_telegram_bot_token"
   export HOST="127.0.0.1"
   export PORT="8000"
   export RELOAD="true"
   ```

3. **Run the application:**
   ```bash
   python main.py
   ```

   Or use the startup script:
   ```bash
   python start_combined.py
   ```

### Production Deployment

1. **Set production environment variables:**
   ```bash
   export TELEGRAM_TOKEN="your_telegram_bot_token"
   export HOST="0.0.0.0"
   export PORT="8000"
   export RELOAD="false"
   ```

2. **Run the application:**
   ```bash
   python main.py
   ```

## 📁 File Structure

```
forex-bot/
├── main.py                 # Combined application entry point
├── start_combined.py       # Startup script with error handling
├── test_combined_app.py    # Test script for verification
├── render.yaml            # Render deployment configuration
├── app/
│   ├── api/
│   │   └── app.py         # FastAPI application with endpoints
│   └── telegram/
│       └── bot.py         # Telegram bot handlers and logic
└── requirements.txt       # Python dependencies
```

## 🔧 Features

### FastAPI Server
- **Health Check:** `GET /health`
- **API Documentation:** `GET /docs`
- **Signals Endpoint:** `GET /api/signals`
- **Trades Endpoint:** `GET /api/trades`
- **Market Data:** `GET /api/market/{pair}`
- **Risk Calculator:** `GET /api/risk/{pair}/{risk_percent}/{sl_pips}`
- **Pip Calculator:** `GET /api/pipcalc/{pair}/{trade_size}`
- **MT5 Integration:** Various MT5 endpoints for trading

### Telegram Bot
- **Commands:** `/start`, `/help`, `/signals`, `/market`, `/analysis`
- **Trading Tools:** `/risk`, `/pipcalc`
- **MT5 Commands:** `/connect`, `/buy`, `/sell`, `/positions`, `/balance`
- **Interactive Menus:** Personalized user menus with inline keyboards

## 🧪 Testing

Run the test script to verify everything is working:

```bash
python test_combined_app.py
```

This will test:
- FastAPI endpoints functionality
- Telegram bot initialization
- Overall application health

## 🚀 Deployment

### Render.com

The application is configured for Render.com deployment. The `render.yaml` file includes:

- Python 3.11 environment
- Automatic dependency installation
- Health check endpoint
- Environment variable configuration

### Other Platforms

For other platforms, ensure:
1. Set `HOST="0.0.0.0"` for external access
2. Set `PORT` to your platform's port (or use `$PORT` environment variable)
3. Set `RELOAD="false"` for production
4. Configure your `TELEGRAM_TOKEN`

## 🔍 Monitoring

### Health Check
```bash
curl http://your-domain.com/health
```

Response:
```json
{
  "status": "healthy",
  "message": "API server is running",
  "bot_status": "running",
  "timestamp": 1234567890.123
}
```

### Logs
The application provides comprehensive logging:
- Application startup/shutdown
- API requests
- Telegram bot events
- Error handling

## 🛠️ Troubleshooting

### Common Issues

1. **Telegram Bot Not Starting:**
   - Check `TELEGRAM_TOKEN` is valid
   - Verify internet connectivity
   - Check bot permissions

2. **API Endpoints Not Working:**
   - Verify server is running on correct port
   - Check firewall settings
   - Review application logs

3. **Import Errors:**
   - Ensure all dependencies are installed
   - Check Python path configuration
   - Verify file structure

### Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL="DEBUG"
python main.py
```

## 📝 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TELEGRAM_TOKEN` | Required | Your Telegram bot token |
| `HOST` | `0.0.0.0` | Server host address |
| `PORT` | `8000` | Server port |
| `RELOAD` | `false` | Enable auto-reload (development) |
| `LOG_LEVEL` | `INFO` | Logging level |

## 🔄 Architecture

The application uses:
- **FastAPI** for the web server and API endpoints
- **python-telegram-bot** for Telegram bot functionality
- **asyncio** for concurrent operation
- **Lifespan management** for proper startup/shutdown
- **Signal handling** for graceful termination

Both services run in the same process with proper async coordination, avoiding event loop conflicts and ensuring reliable operation.

## 📞 Support

For issues or questions:
1. Check the application logs
2. Run the test script
3. Verify environment variables
4. Review the troubleshooting guide

---

**Note:** This combined application replaces the need to run separate FastAPI and Telegram bot processes, providing a unified solution for your forex trading bot. 