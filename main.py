#!/usr/bin/env python3
"""
Main entry point for the Forex Trading Bot
Combines FastAPI server and Telegram bot in a single process
"""

from dotenv import load_dotenv
load_dotenv()

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
from app.telegram.bot import setup_handlers, start_telegram_bot, shutdown_bot, set_bot_commands, get_application
from app.services.api_service import api_service
from app.services.signal_service import signal_service
from app.services.market_service import market_service
from app.services.mt5_service import MT5Service
from app.services.database_service import get_db_dependency, get_or_create_user, Trade

# Import MT5 for position type constants
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    mt5 = None
# AI Imports
from app.services.ai_config import ai_config
from app.services.ai_risk_manager import AIRiskManager
from app.services.telegram_notifier import AITelegramNotifier
from app.services.ai_trading_service import AITradingService

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

# AI Service Initialization
ai_risk_manager: Optional[AIRiskManager] = None
ai_notifier: Optional[AITelegramNotifier] = None
ai_trading_service: Optional[AITradingService] = None
ai_bot_task: Optional[asyncio.Task] = None

# Telegram configuration
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8071906329:AAH4BbllY9vwwcx0vukm6t6JPQdNWnnz-aY")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "default_chat_id") # IMPORTANT: User must set this
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

async def _ai_supervisor(service: AITradingService):
    """Monitors the AI trading task and restarts it if it fails."""
    while True:
        try:
            # This task will run forever until it's cancelled or it crashes
            await service.start()
            
            # If start() returns (which it shouldn't unless it's stopped), wait before restarting
            logger.warning("AI service's main loop exited unexpectedly. Restarting in 60 seconds...")
            await asyncio.sleep(60)

        except asyncio.CancelledError:
            logger.info("AI supervisor task was cancelled. Shutting down.")
            break
        except Exception as e:
            logger.error(f"AI supervisor caught an exception: {e}. Restarting AI service in 60 seconds.", exc_info=True)
            # Ensure the service is stopped before trying to restart
            service.stop()
            await asyncio.sleep(60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown."""
    global bot_task, ai_risk_manager, ai_notifier, ai_trading_service, ai_bot_task
    
    # Startup
    logger.info("🚀 Starting Forex Trading Bot...")
    
    try:
        # Start the Telegram bot as a background task
        logger.info("🤖 Starting Telegram bot...")
        bot_task = asyncio.create_task(start_telegram_bot(TELEGRAM_TOKEN, shutdown_event))
        
        # Wait a moment for bot to initialize and get the Application instance
        await asyncio.sleep(3)

        telegram_app = get_application()
        # Initialize AI Services
        if telegram_app:
            logger.info("Initializing AI Services...")
            ai_risk_manager = AIRiskManager(config=ai_config, mt5_service=mt5_service)
            ai_notifier = AITelegramNotifier(bot=telegram_app.bot, chat_id=TELEGRAM_CHAT_ID)
            ai_trading_service = AITradingService(
                config=ai_config,
                risk_manager=ai_risk_manager,
                mt5_service=mt5_service,
                notifier=ai_notifier
            )
            # Start the AI bot task under the supervisor
            ai_bot_task = asyncio.create_task(_ai_supervisor(ai_trading_service))
        else:
            logger.error("Telegram App not initialized. AI services cannot start.")

        logger.info("✅ Application startup complete")
        yield
        
    except Exception as e:
        logger.error(f"❌ Error during startup: {e}")
        raise
    finally:
        # Shutdown
        logger.info("🛑 Shutting down application...")
        
        # Stop AI bot
        if ai_bot_task and not ai_bot_task.done():
            logger.info("🛑 Stopping AI supervisor and trading service...")
            ai_bot_task.cancel()
        if ai_trading_service:
            ai_trading_service.stop()
        
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
    ai_status = "running" if ai_trading_service and ai_trading_service.is_running else "stopped"
    return {
        "status": "healthy", 
        "message": "API server is running",
        "bot_status": bot_status,
        "mt5_status": mt5_status,
        "ai_status": ai_status,
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
        
        import datetime
        today_str = datetime.datetime.now().strftime('%Y-%m-%d')
        
        trade_list = []
        for trade in trades:
            trade_list.append({
                "symbol": trade.symbol,
                "order_type": trade.order_type,
                "entry_price": str(trade.entry_price),
                "close_price": str(trade.close_price) if trade.close_price else None,
                "status": trade.status,
                "pnl": trade.pnl if trade.pnl else 0.0,
                "open_time": f"{today_str} {trade.created_at.strftime('%H:%M:%S')}" if trade.created_at else f"{today_str} 12:00:00"
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
async def mt5_connect(credentials: dict):
    """Connect to MT5 using real service."""
    global ai_risk_manager, ai_notifier, ai_trading_service, ai_bot_task
    try:
        # Handle both dict and Pydantic model inputs
        if hasattr(credentials, 'login'):
            # Pydantic model
            login = credentials.login
            password = credentials.password
            server = credentials.server
        else:
            # Dict input
            login = credentials.get("login")
            password = credentials.get("password")
            server = credentials.get("server")
        if not all([login, password, server]):
            return {"success": False, "error": "Missing credentials"}
        result = await mt5_service.connect(login, password, server)
        logger.info(f"MT5 connection attempt for login: {login}, result: {result}")
        # If connection is successful, start AI services if not already running
        if result.get("success") and mt5_service.connected:
            telegram_app = get_application()
            if telegram_app:
                if not ai_trading_service:
                    logger.info("Initializing AI Services after MT5 connect...")
                    ai_risk_manager = AIRiskManager(config=ai_config, mt5_service=mt5_service)
                    ai_notifier = AITelegramNotifier(bot=telegram_app.bot, chat_id=TELEGRAM_CHAT_ID)
                    ai_trading_service = AITradingService(
                        config=ai_config,
                        risk_manager=ai_risk_manager,
                        mt5_service=mt5_service,
                        notifier=ai_notifier
                    )
                # Only start the AI bot task if not already running
                if not ai_bot_task or ai_bot_task.done():
                    ai_bot_task = asyncio.create_task(_ai_supervisor(ai_trading_service))
                    logger.info("AI trading service started after MT5 connect.")
            else:
                logger.error("Telegram App not initialized. AI services cannot start.")
        # Return the full result, including error details, to the user
        return result
    except Exception as e:
        logger.error(f"Error connecting to MT5: {e}")
        return {"success": False, "error": str(e)}

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
        user_id = order_data.get("user_id")
        result = await mt5_service.place_order(symbol, lot, order_type, sl, tp, user_id=user_id)
        logger.info(f"MT5 order placed: {order_data}")
        return result
    except Exception as e:
        logger.error(f"Error placing MT5 order: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/mt5/positions")
async def mt5_positions():
    """Get real open positions from MT5."""
    try:
        if not MT5_AVAILABLE:
            return {"error": "MetaTrader5 package not available"}
        
        if not mt5_service.connected:
            return {"error": "MT5 not connected"}
        
        positions = await mt5_service.get_positions()
        if positions is None:
            return []
        
        # Convert MT5 position objects to dictionaries
        positions_list = []
        for pos in positions:
            try:
                position_dict = {
                    "ticket": pos.ticket,
                    "symbol": pos.symbol,
                    "type": "buy" if pos.type == mt5.POSITION_TYPE_BUY else "sell",
                    "lot": pos.volume,
                    "price_open": pos.price_open,
                    "price_current": pos.price_current,
                    "profit": pos.profit,
                    "sl": pos.sl,
                    "tp": pos.tp,
                    "time": pos.time
                }
                positions_list.append(position_dict)
            except Exception as e:
                logger.error(f"Error processing position: {e}")
                continue
        
        return positions_list
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        return {"error": f"Failed to get positions: {str(e)}"}

@app.get("/api/mt5/orders")
async def mt5_orders():
    """Get real pending orders from MT5."""
    try:
        if not MT5_AVAILABLE:
            return {"error": "MetaTrader5 package not available"}
        
        if not mt5_service.connected:
            return {"error": "MT5 not connected"}
        
        orders = await mt5_service.get_orders()
        if orders is None:
            return []
        
        # Ensure orders is a list
        if not isinstance(orders, list):
            logger.error(f"Expected list of orders, got: {type(orders)}")
            return []
        
        return orders
    except Exception as e:
        logger.error(f"Error getting orders: {e}")
        return {"error": f"Failed to get orders: {str(e)}"}

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

@app.post("/api/mt5/modify")
async def mt5_modify_position(modification: dict):
    """Modify an existing MT5 position."""
    try:
        ticket = int(modification.get("ticket"))
        sl = float(modification.get("sl", 0.0))
        tp = float(modification.get("tp", 0.0))
        
        if not ticket:
            raise HTTPException(status_code=400, detail="Ticket number is required.")
            
        result = await mt5_service.modify_position(ticket, sl, tp)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to modify position."))
            
        logger.info(f"Successfully initiated modification for ticket {ticket}")
        return result
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ticket, SL, or TP format. Please use numbers.")
    except Exception as e:
        logger.error(f"Error modifying MT5 position: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

# --- AI Control Endpoints ---
@app.post("/api/ai/start")
async def ai_start():
    if ai_trading_service:
        await ai_trading_service.start()
        return {"status": "success", "message": "AI trading service started."}
    return {"status": "error", "message": "AI service not initialized."}

@app.post("/api/ai/stop")
async def ai_stop():
    if ai_trading_service:
        ai_trading_service.stop()
        return {"status": "success", "message": "AI trading service stopped."}
    return {"status": "error", "message": "AI service not initialized."}

@app.get("/api/ai/status")
async def ai_status():
    if ai_trading_service:
        return {
            "is_running": ai_trading_service.is_running,
            "daily_trades": ai_risk_manager.daily_trade_count,
            "max_daily_trades": ai_config.MAX_DAILY_TRADES,
            "daily_pnl": ai_risk_manager.daily_pnl
        }
    return {"is_running": False, "message": "AI service not initialized."}

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