import logging
import asyncio
import sys
import os
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.api.endpoints import router as api_router
from app.api.telegram import router as telegram_router
from app.telegram.bot_manager import bot_manager
from app.utils.config import config
from app.utils.logging_config import setup_logging
from app.services.database_service import create_db_and_tables
from app.security.simple_credential_manager import SimpleCredentialManager
from app.mt5.mt5_manager import MT5Service
import sqlite3
from app.telegram.bot import start_telegram_bot

credential_manager = SimpleCredentialManager()
mt5_service = MT5Service()

# Setup logging
setup_logging(log_level=config.log_level)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info("Creating database and tables...")
    create_db_and_tables()
    logger.info("Database setup complete.")

    logger.info("Application starting up...")
    bot_task = None
    if config.bot_mode == "polling":
        logger.info("Starting bot in polling mode...")
        bot_task = asyncio.create_task(bot_manager.start())
    else:
        logger.info("Bot will be started in webhook mode via the telegram router.")
    try:
        yield
    finally:
        # Shutdown logic
        logger.info("Application shutting down...")
        await bot_manager.stop()

app = FastAPI(
    title="Forex Trading Bot API",
    version="1.0.0",
    description="API for the Forex Trading Bot, with integrated Telegram bot.",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    # Auto-reconnect for all users with stored credentials
    try:
        with sqlite3.connect(credential_manager.db_path) as conn:
            for row in conn.execute("SELECT user_id FROM credentials"):
                creds = credential_manager.get_credentials(row[0])
                if creds:
                    login, password, server = creds
                    mt5_service.connect(login, password, server)
    except Exception as e:
        print(f"[Startup] Error during auto-reconnect: {e}")
    # Start the Telegram bot as a background task
    import asyncio
    asyncio.create_task(start_telegram_bot())

@app.get('/')
def root():
    return {'message': 'Forex Trading Bot API'}

app.include_router(api_router, prefix='/api', tags=["API"])
app.include_router(telegram_router, tags=["Telegram"])

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "bot_running": bot_manager.is_running}

@app.get("/api/signals")
async def get_signals():
    """Mock signals endpoint for testing."""
    return [
        {
            "pair": "EURUSD",
            "strategy": "RSI + Fibonacci",
            "entry_range": "1.0850-1.0860",
            "stop_loss": "1.0820",
            "take_profit": "1.0900",
            "confidence": "High",
            "risk_reward_ratio": "2.5:1"
        },
        {
            "pair": "GBPUSD",
            "strategy": "Order Block",
            "entry_range": "1.2650-1.2660",
            "stop_loss": "1.2620",
            "take_profit": "1.2720",
            "confidence": "Medium",
            "risk_reward_ratio": "2.0:1"
        }
    ]

@app.get("/api/trades")
async def get_trades():
    """Mock trades endpoint for testing."""
    import datetime
    today_str = datetime.datetime.now().strftime('%Y-%m-%d')
    
    return [
        {
            "symbol": "EURUSD",
            "order_type": "buy",
            "entry_price": "1.0855",
            "close_price": "1.0880",
            "status": "closed",
            "pnl": 25.0,
            "open_time": f"{today_str} 09:00:00"
        },
        {
            "symbol": "GBPUSD",
            "order_type": "sell",
            "entry_price": "1.2655",
            "close_price": None,
            "status": "open",
            "pnl": 0.0,
            "open_time": f"{today_str} 10:00:00"
        }
    ]

@app.get("/api/settings")
async def get_settings(telegram_id: int = None):
    """Mock settings endpoint for testing."""
    return {
        "preferred_pairs": "EURUSD, GBPUSD, USDJPY",
        "default_risk": "2.0"
    }

@app.get("/api/help")
async def get_help(telegram_id: int = None):
    """Mock help endpoint for testing."""
    return {
        "message": "For support, contact @your_support_bot or email support@yourcompany.com"
    }

@app.get("/api/strategies")
async def get_strategies():
    """Mock strategies endpoint for testing."""
    return {
        "strategies": [
            "RSI + Fibonacci Retracement",
            "Order Block Trading",
            "Support/Resistance Breakout",
            "Moving Average Crossover"
        ],
        "message": "These strategies are designed for different market conditions."
    }

def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger.info("🚀 Starting Forex Trading Bot...")
    # The bot is now started in the FastAPI startup event
    # No need to run asyncio.run(start_telegram_bot()) here
    pass

if __name__ == "__main__":
    main()


