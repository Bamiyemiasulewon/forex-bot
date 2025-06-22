import asyncio
import logging
from typing import Optional
from telegram.ext import Application
from app.utils.config import config

logger = logging.getLogger(__name__)

class BotManager:
    """Manages the Telegram bot application with support for webhook and polling modes."""
    
    def __init__(self):
        self.application: Optional[Application] = None
        self._is_running = False
        self._is_starting = False
    
    async def initialize(self) -> bool:
        """Initialize the bot application."""
        try:
            logger.info(f"Initializing bot in {config.bot_mode} mode")
            
            # Create application
            self.application = Application.builder().token(config.telegram_token).build()
            
            # Setup handlers
            from app.telegram.bot import setup_handlers
            setup_handlers(self.application)
            
            logger.info("Bot application initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize bot: {e}")
            return False
    
    async def start_webhook(self) -> bool:
        """Start the bot in webhook mode, checking if the webhook is already set."""
        if not self.application:
            logger.error("Application not initialized")
            return False
        
        try:
            # Initialize the application before setting the webhook
            await self.application.initialize()

            webhook_url = config.webhook_url
            if not webhook_url:
                logger.error("Webhook URL not available")
                return False

            # Check if the webhook is already set correctly
            current_webhook_info = await self.application.bot.get_webhook_info()
            if current_webhook_info and current_webhook_info.url == webhook_url:
                logger.info(f"Webhook is already set to {webhook_url}. Skipping setup.")
                self._is_running = True
                return True
            
            logger.info(f"Attempting to set webhook to {webhook_url}")
            
            # Set webhook
            if await self.application.bot.set_webhook(url=webhook_url):
                logger.info(f"Webhook set successfully to {webhook_url}")
                self._is_running = True
                return True
            else:
                logger.error("The call to set_webhook returned False, indicating failure.")
                return False
            
        except Exception as e:
            logger.error(f"Failed to start webhook mode: {e}", exc_info=config.debug)
            return False
    
    async def start_polling(self) -> bool:
        """Start the bot in polling mode."""
        if not self.application:
            logger.error("Application not initialized")
            return False
        
        try:
            logger.info("Starting polling mode")
            
            # Start polling
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling(read_timeout=30)
            
            self._is_running = True
            logger.info("Bot started in polling mode successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start polling mode: {e}")
            return False
    
    async def start(self) -> bool:
        """Start the bot in the appropriate mode."""
        if self._is_running or self._is_starting:
            logger.warning("Bot start already in progress or completed, skipping.")
            return True

        self._is_starting = True

        try:
            if not await self.initialize():
                return False
            
            if config.is_webhook_mode:
                result = await self.start_webhook()
            else:
                result = await self.start_polling()
            
            # The `is_running` flag is set within start_webhook/start_polling
            return result
        finally:
            self._is_starting = False
    
    async def stop(self):
        """Stop the bot."""
        if not self.application:
            return
        
        try:
            if config.is_webhook_mode:
                # Delete webhook
                await self.application.bot.delete_webhook()
                logger.info("Webhook deleted successfully")
            else:
                # Stop polling
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
                logger.info("Polling stopped successfully")
            
            self._is_running = False
            
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")
    
    @property
    def is_running(self) -> bool:
        """Check if the bot is running."""
        return self._is_running
    
    def get_application(self) -> Optional[Application]:
        """Get the bot application instance."""
        return self.application

# Global bot manager instance
bot_manager = BotManager() 