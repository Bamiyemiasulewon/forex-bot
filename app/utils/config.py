import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class BotConfig:
    """Configuration class for the Telegram bot."""
    
    def __init__(self):
        self.telegram_token = os.getenv('TELEGRAM_TOKEN')
        self.render_external_url = os.getenv('RENDER_EXTERNAL_URL')
        self.bot_mode = os.getenv('BOT_MODE', 'webhook').lower()
        self.webhook_port = int(os.getenv('WEBHOOK_PORT', 8000))
        self.webhook_path = os.getenv('WEBHOOK_PATH', '/webhook')
        self.debug = os.getenv('DEBUG', 'False').lower() == 'true'
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self):
        """Validate the bot configuration."""
        if not self.telegram_token:
            logger.critical("TELEGRAM_TOKEN environment variable not set! The bot will not work.")
            raise ValueError("TELEGRAM_TOKEN is required")
        
        if self.bot_mode not in ['webhook', 'polling']:
            logger.warning(f"Invalid BOT_MODE '{self.bot_mode}'. Defaulting to 'webhook'")
            self.bot_mode = 'webhook'
        
        if self.bot_mode == 'webhook' and not self.render_external_url:
            logger.warning("BOT_MODE is 'webhook' but RENDER_EXTERNAL_URL is not set. Falling back to polling mode.")
            self.bot_mode = 'polling'
    
    @property
    def is_webhook_mode(self) -> bool:
        """Check if bot is configured for webhook mode."""
        return self.bot_mode == 'webhook' and self.render_external_url is not None
    
    @property
    def is_polling_mode(self) -> bool:
        """Check if bot is configured for polling mode."""
        return self.bot_mode == 'polling' or not self.render_external_url
    
    @property
    def webhook_url(self) -> Optional[str]:
        """Get the webhook URL if in webhook mode."""
        if self.is_webhook_mode:
            return f"{self.render_external_url}{self.webhook_path}"
        return None
    
    def get_log_level(self) -> int:
        """Get the logging level."""
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        return level_map.get(self.log_level.upper(), logging.INFO)

# Global configuration instance
config = BotConfig() 