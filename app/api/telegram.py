from fastapi import APIRouter, Request, Depends, HTTPException
import httpx
import os
import logging
from telegram import Update
from app.telegram.bot_manager import bot_manager
from app.utils.config import config

router = APIRouter()
logger = logging.getLogger(__name__)

@router.on_event("startup")
async def startup_event():
    """Initializes the bot and sets the webhook on application startup."""
    if config.is_webhook_mode:
        logger.info("Application starting up in webhook mode.")
        if not await bot_manager.start():
            logger.error("Bot failed to start in webhook mode. The application may not work correctly.")
    else:
        logger.info("Skipping webhook setup, bot is not in webhook mode.")

@router.on_event("shutdown")
async def shutdown_event():
    """Stops the bot gracefully on application shutdown."""
    logger.info("Application shutting down.")
    await bot_manager.stop()

@router.post(config.webhook_path)
async def telegram_webhook(request: Request):
    """Handles incoming updates from the Telegram webhook."""
    if not bot_manager.is_running or not bot_manager.application:
        logger.error("Webhook received but bot is not running or initialized.")
        raise HTTPException(status_code=500, detail="Bot is not running")

    try:
        update_data = await request.json()
        update = Update.de_json(update_data, bot_manager.application.bot)
        await bot_manager.application.process_update(update)
        logger.debug(f"Successfully processed update: {update.update_id}")
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error processing webhook update: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error processing update") 