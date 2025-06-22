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