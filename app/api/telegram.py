from fastapi import APIRouter, Request, Depends
import httpx
import os
import logging
from app.telegram.bot import handle_update, application

router = APIRouter()
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
RENDER_URL = os.environ.get('RENDER_EXTERNAL_URL')  # Render provides this env var

@router.on_event("startup")
async def setup_telegram_webhook():
    if not RENDER_URL or not TELEGRAM_TOKEN:
        logger.warning("RENDER_EXTERNAL_URL or TELEGRAM_TOKEN is not set. Skipping webhook setup.")
        return
        
    webhook_url = f"{RENDER_URL}/webhook"
    set_webhook_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook?url={webhook_url}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(set_webhook_url)
            response.raise_for_status()
            logger.info(f"Webhook set to {webhook_url}: {response.json()}")
        except httpx.HTTPStatusError as e:
            logger.error(f"Error setting webhook: {e.response.text}")
        except Exception as e:
            logger.error(f"An error occurred during webhook setup: {e}")

@router.post("/webhook")
async def telegram_webhook(request: Request):
    update = await request.json()
    logger.info(f"Received update: {update}")
    await handle_update(update)
    return {"status": "ok"} 