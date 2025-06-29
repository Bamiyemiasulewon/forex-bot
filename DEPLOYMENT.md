# Deploying the Forex Bot on Render

This guide provides instructions for deploying, configuring, and testing the Forex Bot on the Render platform.

## 1. Fork the Repository

First, ensure you have a fork of this repository on your own GitHub account. Render will connect to this repository to deploy the application.

## 2. Create a New Web Service on Render

1.  **Go to the Render Dashboard** and click **New +** > **Web Service**.
2.  **Connect your GitHub account** and select the forked repository.
3.  **Configure the service:**
    *   **Name**: Give your service a name (e.g., `forex-telegram-bot`).
    *   **Region**: Choose a region close to you or your users.
    *   **Branch**: Select the `main` branch.
    *   **Runtime**: Select `Python 3`.
    *   **Build Command**: `pip install -r requirements.txt`
    *   **Start Command**: `gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app`
    *   **Instance Type**: `Free` is sufficient for testing and small-scale use.

4.  Click **Create Web Service**.

## 3. Configure Environment Variables

The bot requires several environment variables to function correctly. On your Render service page, go to the **Environment** tab and add the following:

*   **`TELEGRAM_TOKEN`**:
    *   **Value**: Your token from BotFather.
    *   **Required**: Yes
    *   **Description**: This is the secret token for your Telegram bot. Keep it safe.

*   **`RENDER_EXTERNAL_URL`**:
    *   **Value**: This is automatically provided by Render. It will be the URL of your web service (e.g., `https://forex-telegram-bot.onrender.com`).
    *   **Required**: Yes (for webhook mode)
    *   **Description**: The public URL of your application, used to set the Telegram webhook.

*   **`EXCHANGERATE_API_KEY`**:
    *   **Value**: Your API key from [ExchangeRate-API.com](https://www.exchangerate-api.com/).
    *   **Required**: Yes
    *   **Description**: Required for the `/risk` and `/pipcalc` commands to function. The bot will not work correctly without this.

*   **`DATABASE_URL`** (Optional, for PostgreSQL):
    *   **Value**: The connection string for your database. If you create a Render PostgreSQL database, this will be provided.
    *   **Required**: For production use with a persistent database.
    *   **Description**: If not set, the bot will default to a temporary SQLite database.

*   **`ALPHA_VANTAGE_API_KEY`** (Optional):
    *   **Value**: Your API key from Alpha Vantage.
    *   **Required**: If you want to use live market data features.
    *   **Description**: API key for fetching financial data.

After setting these, Render will automatically trigger a new deployment.

## 4. Set the Telegram Webhook

Once your application is deployed and running, Telegram needs to be told where to send updates. While the bot attempts to set this on startup, you can also set it manually if needed.

Send a `GET` request to the following URL (you can do this in your browser):
`https://api.telegram.org/bot<YOUR_TELEGRAM_TOKEN>/setWebhook?url=<YOUR_RENDER_EXTERNAL_URL>/telegram/webhook`

Replace `<YOUR_TELEGRAM_TOKEN>` and `<YOUR_RENDER_EXTERNAL_URL>` with your actual values. A successful response will look like: `{"ok":true,"result":true,"description":"Webhook was set"}`.

## 5. Testing Checklist

After deployment, test the bot's functionality by sending it commands in your Telegram chat.

| Command                     | Expected Outcome                                                                    | Status      |
| --------------------------- | ----------------------------------------------------------------------------------- | ----------- |
| `/start`                    | Displays the welcome message sequence and main menu.                                | `[ ]` Pass  |
| `/help`                     | Shows the list of available commands.                                               | `[ ]` Pass  |
| `/trades`                   | Shows a list of mock trades (e.g., "Open: EUR/USD, 1.0 lots @ 1.0900").              | `[ ]` Pass  |
| `/risk EURUSD 2 20`         | Returns a calculated position size for the specified pair.                          | `[ ]` Pass  |
| `/risk eurusd 1 50`         | Returns a valid calculation (case-insensitive).                                     | `[ ]` Pass  |
| `/risk INVALID 2 20`        | Returns an error about being unable to calculate the pip value.                     | `[ ]` Pass  |
| `/pipcalc EURUSD 1.0 50`    | Returns a calculated profit/loss for the specified pair.                            | `[ ]` Pass  |
| `/pipcalc usdjpy 0.5 -100`  | Returns a calculated loss for a JPY pair.                                           | `[ ]` Pass  |
| `/pipcalc INVALID 1.0 50`   | Returns an error about being unable to calculate the pip value.                     | `[ ]` Pass  |
| `/signals`                  | Displays a mock signal alert.                                                       | `[ ]` Pass  |
| `/market`                   | Shows market data for EURUSD.                                                       | `[ ]` Pass  |
| `/market GBPJPY`            | Shows market data for GBPJPY.                                                       | `[ ]` Pass  |

## 6. Monitoring

Check the **Logs** tab in your Render service dashboard to monitor the bot for any errors or unexpected behavior. This is crucial for debugging if the bot doesn't respond as expected.

# Deployment Guide

## Environment Configuration

### Local Development
When running locally, the API service automatically detects that you're in development mode and uses:
- **API Base URL**: `http://127.0.0.1:8000`
- **Environment**: Local development
- **Configuration**: No `RENDER_EXTERNAL_URL` environment variable set

### Production (Render)
When deployed to Render, the API service uses:
- **API Base URL**: `https://forex-telegram-bot.onrender.com` (or your actual Render URL)
- **Environment**: Production
- **Configuration**: `RENDER_EXTERNAL_URL` environment variable is set by Render

## How It Works

The API service configuration in `app/services/api_service.py` automatically detects the environment:

```python
def get_api_base_url():
    """Get the appropriate API base URL based on environment."""
    render_url = os.getenv("RENDER_EXTERNAL_URL", "")
    
    if not render_url or "localhost" in render_url or "127.0.0.1" in render_url:
        # Local development - use local server
        return "http://127.0.0.1:8000"
    else:
        # Production - use Render URL
        return render_url.rstrip('/')
```

## Deployment Steps

### 1. Local Development
```bash
# Start the application locally
python main.py

# The bot will automatically use http://127.0.0.1:8000 for API calls
```

### 2. Production Deployment
1. Update the `RENDER_EXTERNAL_URL` in `render.yaml` with your actual Render URL
2. Deploy to Render using the `render.yaml` configuration
3. Set your environment variables in Render dashboard:
   - `TELEGRAM_TOKEN`
   - `EXCHANGERATE_API_KEY`
   - `DATABASE_URL` (automatically set by Render)

### 3. Testing Configuration
Run the test script to verify your configuration:
```bash
python test_api_config.py
```

## Troubleshooting

### Issue: Bot trying to call Render URL locally
**Solution**: The bot should automatically detect local development. If it's still calling Render URL:
1. Check that `RENDER_EXTERNAL_URL` is not set in your local environment
2. Restart the application after clearing any environment variables

### Issue: Bot trying to call localhost in production
**Solution**: Ensure `RENDER_EXTERNAL_URL` is properly set in your Render environment variables.

### Issue: 404 errors on MT5 endpoints
**Solution**: 
1. Verify the API server is running on the correct port
2. Check that all MT5 endpoints are properly implemented in `main.py`
3. Ensure the API service is using the correct base URL

## Environment Variables Reference

| Variable | Local | Production | Description |
|----------|-------|------------|-------------|
| `RENDER_EXTERNAL_URL` | Not set | `https://your-app.onrender.com` | Determines API base URL |
| `TELEGRAM_TOKEN` | Required | Required | Your Telegram bot token |
| `EXCHANGERATE_API_KEY` | Optional | Optional | For exchange rate data |
| `DATABASE_URL` | Optional | Required | Database connection string |
| `HOST` | `0.0.0.0` | `0.0.0.0` | Server host |
| `PORT` | `8000` | `8000` | Server port |
| `RELOAD` | `true` | `false` | Enable auto-reload 