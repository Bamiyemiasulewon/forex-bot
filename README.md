# Forex Trading Bot

A production-ready, fully automated Forex trading bot that generates profitable trading signals, executes trades, and delivers real-time alerts via Telegram.

## Tech Stack
- **Framework:** FastAPI (APIs), python-telegram-bot (async)
- **Database:** PostgreSQL + SQLAlchemy ORM + Redis (caching/queues)
- **Background Tasks:** Celery + Redis, asyncio
- **Data APIs:** ccxt, Alpha Vantage
- **Trading:** pandas, numpy, ta-lib, custom strategies
- **Testing:** pytest

## Features
- Market analysis & signal generation (RSI, MACD, Bollinger Bands, etc.)
- Automated trading execution with order management
- Telegram bot interface for live alerts and trade management
- Historical market analysis engine & backtesting
- Real-time data integration & live feeds
- Risk management & trade monitoring
- User management, authentication, and premium tiers

## Project Structure
```
app/
├── main.py (FastAPI entry)
├── models/ (database models)
├── services/ (forex data, signals)
├── telegram/ (bot handlers)
├── api/ (REST endpoints)
└── utils/ (helpers, indicators)
```

## Setup
1. Clone the repo and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Configure environment variables in a `.env` file.
3. Run database migrations with Alembic.
4. Start the FastAPI server:
   ```bash
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
   ```
5. Start Celery worker:
   ```bash
   celery -A app.services.tasks worker --loglevel=info
   ```
6. Set up and start the Telegram bot.

## License
MIT 

### Environment Variables

To run this application, you will need to set the following environment variables. You can create a `.env` file in the root directory to manage these locally.

- `TELEGRAM_TOKEN`: Your secret token from Telegram's BotFather.
- `EXCHANGERATE_API_KEY`: A free API key from [ExchangeRate-API.com](https://www.exchangerate-api.com/) required for calculator commands.
- `RENDER_EXTERNAL_URL` (for production): The public URL of your deployed application on a service like Render. If this is set, the bot will run in webhook mode. Otherwise, it defaults to polling.
- `DATABASE_URL` (optional): The connection string for your database (e.g., `postgresql://...`). Defaults to a local SQLite database (`sqlite:///./forex_bot.db`).

## Deployment

This application is designed to be deployed on [Render](https://render.com/). Please see the detailed `DEPLOYMENT.md` file for step-by-step instructions.

## Contributing
MIT 