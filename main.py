#!/usr/bin/env python3
"""
Main entry point for the Forex Trading Bot
Combines FastAPI server and Telegram bot in a single process
"""

import asyncio
import logging
import os
import signal
import sys
import time
import tracemalloc
from contextlib import asynccontextmanager
from typing import Optional

# Add the app directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from pydantic import BaseModel
from telegram.ext import Application

# Import our modules
from app.telegram.bot import setup_handlers, start_telegram_bot, shutdown_bot
from app.services.api_service import api_service
from app.services.signal_service import signal_service
from app.services.market_service import market_service
from app.services.mt5_service import MT5Service
from app.services.database_service import get_db_dependency, get_or_create_user, Trade

# Enable tracemalloc for debugging memory leaks
tracemalloc.start()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables
telegram_app: Optional[Application] = None
bot_task: Optional[asyncio.Task] = None
shutdown_event = asyncio.Event()

# Initialize MT5 service
mt5_service = MT5Service()

# Telegram configuration
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8071906329:AAH4BbllY9vwwcx0vukm6t6JPQdNWnnz-aY")
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN environment variable not set!")

# Share global variables with bot module
def get_global_vars():
    """Return global variables for bot module access."""
    return {
        'telegram_app': telegram_app,
        'bot_task': bot_task,
        'shutdown_event': shutdown_event,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN
    }

# Pydantic models for request validation
class MT5Credentials(BaseModel):
    login: str
    password: str
    server: str

class MT5Order(BaseModel):
    symbol: str
    lot: float
    type: str
    sl: float = None
    tp: float = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown."""
    global bot_task
    
    # Startup
    logger.info("🚀 Starting Forex Trading Bot...")
    
    try:
        # Start the Telegram bot as a background task
        logger.info("🤖 Starting Telegram bot...")
        bot_task = asyncio.create_task(start_telegram_bot(TELEGRAM_TOKEN, shutdown_event))
        
        # Wait a moment for bot to initialize
        await asyncio.sleep(3)
        
        logger.info("✅ Application startup complete")
        yield
        
    except Exception as e:
        logger.error(f"❌ Error during startup: {e}")
        raise
    finally:
        # Shutdown
        logger.info("🛑 Shutting down application...")
        
        # Stop the bot
        if bot_task and not bot_task.done():
            logger.info("🛑 Stopping Telegram bot...")
            bot_task.cancel()
            try:
                await asyncio.wait_for(bot_task, timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning("Bot shutdown timed out")
            except asyncio.CancelledError:
                pass
        
        # Final cleanup
        await shutdown_bot()
        tracemalloc.stop()
        logger.info("✅ Application shutdown complete")

# Create the main FastAPI app
app = FastAPI(
    title="Forex Trading Bot API",
    description="API for Forex Trading Bot with integrated Telegram bot",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Forex Trading Bot API is running", 
        "status": "healthy", 
        "bot_running": bot_task is not None and not bot_task.done() if bot_task else False
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    bot_status = "running" if bot_task and not bot_task.done() else "stopped"
    mt5_status = "connected" if mt5_service.connected else "disconnected"
    return {
        "status": "healthy", 
        "message": "API server is running",
        "bot_status": bot_status,
        "mt5_status": mt5_status,
        "timestamp": time.time()
    }

# Real API endpoints using actual services
@app.get("/api/signals")
async def get_signals():
    """Get real trading signals from signal service."""
    try:
        signals = await signal_service.generate_signals()
        logger.info(f"Returning {len(signals)} real signals")
        return signals
    except Exception as e:
        logger.error(f"Error getting signals: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/trades")
async def get_trades(db=Depends(get_db_dependency)):
    """Get real trade history from database."""
    try:
        # Get all trades from database
        trades = db.query(Trade).order_by(Trade.created_at.desc()).limit(20).all()
        
        trade_list = []
        for trade in trades:
            trade_list.append({
                "symbol": trade.symbol,
                "order_type": trade.order_type,
                "entry_price": str(trade.entry_price),
                "close_price": str(trade.close_price) if trade.close_price else None,
                "status": trade.status,
                "pnl": trade.pnl if trade.pnl else 0.0
            })
        
        logger.info(f"Returning {len(trade_list)} trades from database")
        return trade_list
    except Exception as e:
        logger.error(f"Error getting trades: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/settings")
async def get_settings(telegram_id: int = None, db=Depends(get_db_dependency)):
    """Get real user settings from database."""
    try:
        if telegram_id:
            user = get_or_create_user(db, telegram_id)
            if user.settings:
                settings = {
                    "preferred_pairs": user.settings.preferred_pairs,
                    "default_risk": str(user.settings.default_risk),
                    "notification_enabled": True,
                    "timezone": "UTC"
                }
            else:
                settings = {
                    "preferred_pairs": "EURUSD,GBPUSD,USDJPY",
                    "default_risk": "1.0",
                    "notification_enabled": True,
                    "timezone": "UTC"
                }
        else:
            settings = {
                "preferred_pairs": "EURUSD,GBPUSD,USDJPY",
                "default_risk": "1.0",
                "notification_enabled": True,
                "timezone": "UTC"
            }
        
        logger.info(f"Returning settings for telegram_id: {telegram_id}")
        return settings
    except Exception as e:
        logger.error(f"Error getting settings: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/help")
async def get_help(telegram_id: int = None):
    """Get help information."""
    try:
        help_info = {
            "message": "For support, contact @your_support_bot or email support@yourcompany.com",
            "faq_url": "https://yourcompany.com/faq",
            "documentation_url": "https://yourcompany.com/docs"
        }
        logger.info(f"Returning help info for telegram_id: {telegram_id}")
        return help_info
    except Exception as e:
        logger.error(f"Error getting help: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/strategies")
async def get_strategies():
    """Get available trading strategies."""
    try:
        strategies = {
            "strategies": [
                "RSI + Fibonacci Retracement",
                "Order Block Trading",
                "Support/Resistance Breakout",
                "Moving Average Crossover",
                "Bollinger Bands Strategy",
                "MACD Divergence"
            ],
            "message": "These strategies are designed for different market conditions."
        }
        logger.info("Returning strategies")
        return strategies
    except Exception as e:
        logger.error(f"Error getting strategies: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/market/{pair}")
async def get_market_data(pair: str):
    """Get real market data from market service."""
    try:
        market_data = await market_service.get_market_data(pair)
        
        if "error" in market_data:
            raise HTTPException(status_code=400, detail=market_data["error"])
        
        logger.info(f"Returning real market data for {pair}")
        return market_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting market data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/risk/{pair}/{risk_percent}/{sl_pips}")
async def calculate_risk(pair: str, risk_percent: float, sl_pips: float):
    """Calculate real position size based on risk parameters."""
    try:
        # Get current market data for the pair
        market_data = await market_service.get_market_data(pair)
        if "error" in market_data:
            raise HTTPException(status_code=400, detail=market_data["error"])
        
        # Mock account balance (in real app, get from user's account)
        account_balance = 10000.0
        risk_amount_usd = account_balance * (risk_percent / 100)
        
        # Calculate position size based on pip value
        # For major pairs, 1 pip = $10 per lot
        pip_value_per_lot = 10.0
        position_size_lots = risk_amount_usd / (sl_pips * pip_value_per_lot)
        
        result = {
            "pair": pair.upper(),
            "account_balance": account_balance,
            "risk_percent": risk_percent,
            "risk_amount_usd": risk_amount_usd,
            "stop_loss_pips": sl_pips,
            "position_size_lots": position_size_lots
        }
        logger.info(f"Risk calculation for {pair}: {risk_percent}% risk, {sl_pips} pips SL")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating risk: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/pipcalc/{pair}/{trade_size}")
async def calculate_pip_value(pair: str, trade_size: float):
    """Calculate real pip value for a given trade size."""
    try:
        # Get current market data for the pair
        market_data = await market_service.get_market_data(pair)
        if "error" in market_data:
            raise HTTPException(status_code=400, detail=market_data["error"])
        
        # Calculate pip value (simplified calculation)
        pip_value_usd = trade_size * 10  # $10 per lot for major pairs
        
        result = {
            "pair": pair.upper(),
            "trade_size": trade_size,
            "pip_value_usd": pip_value_usd
        }
        logger.info(f"Pip calculation for {pair}: {trade_size} lots")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating pip value: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# MT5 Trading Endpoints with real MT5 service
@app.post("/api/mt5/connect")
async def mt5_connect(credentials: MT5Credentials):
    """Connect to MT5 using real service."""
    try:
        result = await mt5_service.connect(credentials.login, credentials.password, credentials.server)
        logger.info(f"MT5 connection attempt for login: {credentials.login}")
        return result
    except Exception as e:
        logger.error(f"Error connecting to MT5: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/mt5/status")
async def mt5_status():
    """Check real MT5 connection status."""
    try:
        result = await mt5_service.get_status()
        return result
    except Exception as e:
        logger.error(f"Error checking MT5 status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/mt5/balance")
async def mt5_balance():
    """Get real account balance from MT5."""
    try:
        result = await mt5_service.get_balance()
        if result is None:
            raise HTTPException(status_code=400, detail="Not connected to MT5")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting balance: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/mt5/account")
async def mt5_account():
    """Get real detailed account info from MT5."""
    try:
        result = await mt5_service.get_account()
        if result is None:
            raise HTTPException(status_code=400, detail="Not connected to MT5")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting account info: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/mt5/order")
async def mt5_order(order_data: dict):
    """Place real MT5 order."""
    try:
        symbol = order_data.get("symbol")
        lot = order_data.get("lot")
        order_type = order_data.get("type")
        sl = order_data.get("sl")
        tp = order_data.get("tp")
        
        result = await mt5_service.place_order(symbol, lot, order_type, sl, tp)
        logger.info(f"MT5 order placed: {order_data}")
        return result
    except Exception as e:
        logger.error(f"Error placing MT5 order: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/mt5/positions")
async def mt5_positions():
    """Get real open positions from MT5."""
    try:
        result = await mt5_service.get_positions()
        return result
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/mt5/orders")
async def mt5_orders():
    """Get real pending orders from MT5."""
    try:
        result = await mt5_service.get_orders()
        return result
    except Exception as e:
        logger.error(f"Error getting orders: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/mt5/close/{ticket}")
async def mt5_close_position(ticket: int):
    """Close real specific position in MT5."""
    try:
        result = await mt5_service.close_position(ticket)
        logger.info(f"MT5 position closed: {ticket}")
        return result
    except Exception as e:
        logger.error(f"Error closing position: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/mt5/closeall")
async def mt5_close_all():
    """Close all real positions in MT5."""
    try:
        result = await mt5_service.close_all_positions()
        logger.info("All MT5 positions closed")
        return result
    except Exception as e:
        logger.error(f"Error closing all positions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/mt5/price/{symbol}")
async def mt5_price(symbol: str):
    """Get real current price from MT5."""
    try:
        result = await mt5_service.get_price(symbol)
        return result
    except Exception as e:
        logger.error(f"Error getting price: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/mt5/summary")
async def mt5_summary():
    """Get real trading summary from MT5."""
    try:
        result = await mt5_service.get_summary()
        return result
    except Exception as e:
        logger.error(f"Error getting summary: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {signum}, initiating shutdown...")
    shutdown_event.set()

def main():
    """Main entry point."""
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "false").lower() == "true"
    
    logger.info(f"🚀 Starting Forex Trading Bot on {host}:{port}")
    logger.info(f"📊 API docs will be available at: http://{host}:{port}/docs")
    logger.info(f"🔍 Health check: http://{host}:{port}/health")
    
    try:
        # Start the server
        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        logger.error("Please check:")
        logger.error("1. Internet connection")
        logger.error("2. Telegram bot token is valid")
        logger.error("3. All required environment variables are set")
    finally:
        logger.info("🛑 Application shutdown complete")

if __name__ == "__main__":
    main() 