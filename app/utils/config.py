import os
import logging
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

class Config:
    # Core
    debug: bool = os.getenv("DEBUG", "False").lower() in ("true", "1")
    log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()

    # Telegram
    telegram_token: str = os.getenv("TELEGRAM_TOKEN")
    if not telegram_token:
        raise ValueError("TELEGRAM_TOKEN environment variable not set!")

    # Webhook vs Polling
    render_external_url: Optional[str] = os.getenv("RENDER_EXTERNAL_URL")
    is_webhook_mode: bool = bool(render_external_url)
    
    webhook_path: str = "/telegram/webhook"
    webhook_url: Optional[str] = f"{render_external_url}{webhook_path}" if render_external_url else None
    bot_mode: str = "webhook" if is_webhook_mode else "polling"
    
    # Database
    db_url: str = os.getenv("DATABASE_URL", "sqlite:///./forex_bot.db")

    # API Keys
    exchangerate_api_key: Optional[str] = os.getenv("EXCHANGERATE_API_KEY")

    # Celery
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    def __post_init__(self):
        # Log the bot mode for clarity during startup
        logger.info(f"Configuration loaded. Bot mode: {self.bot_mode.upper()}")
        if self.is_webhook_mode:
            logger.info(f"Webhook URL configured: {self.webhook_url}")
        else:
            logger.info("Polling mode configured.")
        
        if not self.exchangerate_api_key:
            logger.warning("EXCHANGERATE_API_KEY is not set. Calculator commands will not work.")

# Global config instance
try:
    config = Config()
except ValueError as e:
    logger.critical(e)
    # Exit or handle the missing configuration appropriately
    exit(1) 