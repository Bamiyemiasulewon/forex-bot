import asyncio
import logging
from typing import Optional
from telegram.ext import Application
from app.utils.config import config

from app.telegram.bot import setup_handlers
from app.services.market_service import shutdown_event as shutdown_market_service

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
            
            # Create application with increased connection timeouts
            self.application = (
                Application.builder()
                .token(config.telegram_token)
                .connect_timeout(30)
                .pool_timeout(30)
                .build()
            )
            
            # Setup handlers
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

            # Initialize before accessing bot attribute
            await self.application.initialize()
            
            # Force delete any existing webhook with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    webhook_info = await self.application.bot.get_webhook_info()
                    if webhook_info.url:
                        logger.info(f"Attempt {attempt + 1}: Deleting existing webhook for {webhook_info.url}")
                        success = await self.application.bot.delete_webhook()
                        if success:
                            logger.info("Webhook deleted successfully")
                            break
                        else:
                            logger.warning(f"Webhook deletion attempt {attempt + 1} failed")
                    else:
                        logger.info("No existing webhook found")
                        break
                except Exception as e:
                    logger.warning(f"Webhook deletion attempt {attempt + 1} failed: {e}")
                    if attempt == max_retries - 1:
                        logger.error("Failed to delete webhook after all attempts")
                        return False
                    await asyncio.sleep(1)  # Wait before retry

            # Start polling
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
            # Always try to delete webhook to prevent conflicts
            try:
                webhook_info = await self.application.bot.get_webhook_info()
                if webhook_info.url:
                    logger.info(f"Deleting webhook: {webhook_info.url}")
                    await self.application.bot.delete_webhook()
                    logger.info("Webhook deleted successfully")
            except Exception as e:
                logger.warning(f"Error deleting webhook during shutdown: {e}")
            
            if config.is_webhook_mode:
                # Webhook already deleted above
                pass
            else:
                # Stop polling
                try:
                    await self.application.updater.stop()
                    await self.application.stop()
                    await self.application.shutdown()
                    logger.info("Polling stopped successfully")
                except Exception as e:
                    logger.warning(f"Error stopping polling: {e}")
            
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

    def run(self):
        """Starts the bot and blocks until interrupted."""
        logger.info("Bot is starting...")
        # Run the bot until the user presses Ctrl-C
        self.application.run_polling()
        logger.info("Bot has stopped.")

    async def shutdown(self):
        """Gracefully shuts down the bot and its resources."""
        logger.info("Shutting down bot...")
        # You might have other cleanup tasks here
        await shutdown_market_service()
        logger.info("Bot shutdown complete.")

async def main():
    """Main entry point for running the bot."""
    bot_manager = BotManager()
    
    try:
        bot_manager.run()
    except (KeyboardInterrupt, SystemExit):
        await bot_manager.shutdown()

if __name__ == '__main__':
    asyncio.run(main())

# Global bot manager instance
bot_manager = BotManager() 