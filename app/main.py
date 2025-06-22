import logging
import asyncio
import sys
import os
from fastapi import FastAPI

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.api.endpoints import router as api_router
from app.api.telegram import router as telegram_router
from app.telegram.bot_manager import bot_manager
from app.utils.config import config
from app.utils.logging_config import setup_logging
from app.services.database_service import create_db_and_tables

# Setup logging
setup_logging(log_level=config.log_level)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Forex Trading Bot API",
    version="1.0.0",
    description="API for the Forex Trading Bot, with integrated Telegram bot.",
)

@app.on_event("startup")
async def on_startup():
    """Application startup event handler."""
    logger.info("Creating database and tables...")
    create_db_and_tables()
    logger.info("Database setup complete.")

    logger.info("Application starting up...")
    if config.bot_mode == "polling":
        logger.info("Starting bot in polling mode...")
        # Running polling in the background
        asyncio.create_task(bot_manager.start())
    else:
        logger.info("Bot will be started in webhook mode via the telegram router.")

@app.on_event("shutdown")
async def on_shutdown():
    """Application shutdown event handler."""
    logger.info("Application shutting down...")
    await bot_manager.stop()

@app.get('/')
def root():
    return {'message': 'Forex Trading Bot API'}

app.include_router(api_router, prefix='/api', tags=["API"])
app.include_router(telegram_router, tags=["Telegram"])

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "bot_running": bot_manager.is_running}


