from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from typing import List, Dict, Any
import logging
from pydantic import BaseModel

# Import MT5 service
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from services.mt5_service import mt5_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

app = FastAPI(
    title="Forex Trading Bot API",
    description="API for Forex Trading Bot Telegram integration",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Forex Trading Bot API is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "API server is running"}

@app.get("/api/signals")
async def get_signals():
    """Get trading signals."""
    try:
        # Mock signals data
        signals = [
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
            },
            {
                "pair": "USDJPY",
                "strategy": "Support/Resistance",
                "entry_range": "150.50-150.60",
                "stop_loss": "150.20",
                "take_profit": "151.00",
                "confidence": "Medium",
                "risk_reward_ratio": "2.0:1"
            }
        ]
        logger.info(f"Returning {len(signals)} signals")
        return signals
    except Exception as e:
        logger.error(f"Error getting signals: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/trades")
async def get_trades():
    """Get trade history."""
    try:
        import datetime
        today_str = datetime.datetime.now().strftime('%Y-%m-%d')
        
        # Mock trades data
        trades = [
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
            },
            {
                "symbol": "USDJPY",
                "order_type": "buy",
                "entry_price": "150.55",
                "close_price": "150.80",
                "status": "closed",
                "pnl": 25.0,
                "open_time": f"{today_str} 11:00:00"
            },
            {
                "symbol": "EURUSD",
                "order_type": "buy",
                "entry_price": "1.18000",
                "close_price": "1.18500",
                "status": "closed",
                "pnl": 50.0,
                "open_time": f"{today_str} 10:00:00"
            }
        ]
        logger.info(f"Returning {len(trades)} trades")
        return trades
    except Exception as e:
        logger.error(f"Error getting trades: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/settings")
async def get_settings(telegram_id: int = None):
    """Get user settings."""
    try:
        # Mock settings data
        settings = {
            "preferred_pairs": "EURUSD, GBPUSD, USDJPY",
            "default_risk": "2.0",
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
    """Get market data for a specific pair."""
    try:
        # Mock market data
        market_data = {
            "pair": pair.upper(),
            "price": 1.0855,
            "open": 1.0840,
            "high": 1.0870,
            "low": 1.0830,
            "volume": 125000,
            "change": 0.0015,
            "change_percent": 0.14
        }
        logger.info(f"Returning market data for {pair}")
        return market_data
    except Exception as e:
        logger.error(f"Error getting market data for {pair}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/risk/{pair}/{risk_percent}/{sl_pips}")
async def calculate_risk(pair: str, risk_percent: float, sl_pips: float):
    """Calculate position size based on risk parameters."""
    try:
        # Mock risk calculation
        account_balance = 10000.0
        risk_amount_usd = account_balance * (risk_percent / 100)
        
        risk_data = {
            "pair": pair.upper(),
            "account_balance": account_balance,
            "risk_percent": risk_percent,
            "risk_amount_usd": risk_amount_usd,
            "stop_loss_pips": sl_pips,
            "position_size_lots": round(risk_amount_usd / (sl_pips * 10), 2)
        }
        logger.info(f"Calculated risk for {pair}: {risk_percent}% risk, {sl_pips} pips SL")
        return risk_data
    except Exception as e:
        logger.error(f"Error calculating risk: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/pipcalc/{pair}/{trade_size}")
async def calculate_pip_value(pair: str, trade_size: float):
    """Calculate pip value for a trade size."""
    try:
        # Mock pip calculation
        pip_value_usd = trade_size * 10  # Simplified calculation
        
        pip_data = {
            "pair": pair.upper(),
            "trade_size": trade_size,
            "pip_value_usd": pip_value_usd
        }
        logger.info(f"Calculated pip value for {pair}: {trade_size} lots = ${pip_value_usd}")
        return pip_data
    except Exception as e:
        logger.error(f"Error calculating pip value: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# --- MT5 Trading API Endpoints ---

@app.post("/api/mt5/connect")
async def mt5_connect(credentials: dict):
    """Connect to MT5 with credentials."""
    try:
        login = credentials.get("login")
        password = credentials.get("password")
        server = credentials.get("server")
        
        if not all([login, password, server]):
            raise HTTPException(status_code=400, detail="Missing credentials")
        
        # Call the real MT5 connection logic
        result = await mt5_service.connect(login, password, server)
        if not result.get("success"):
            logger.error(f"MT5 connection failed for {login}: {result.get('error')}")
        else:
            logger.info(f"MT5 connection successful for {login}")
        return result
        
    except Exception as e:
        logger.error(f"MT5 connection error: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/mt5/status")
async def mt5_status():
    """Get MT5 connection status."""
    try:
        # Mock status - replace with actual MT5 status check
        status_data = {
            "connected": True,
            "account": {
                "login": "12345678",
                "server": "MetaQuotes-Demo",
                "balance": 10000.0,
                "equity": 10050.0,
                "margin": 0.0,
                "free_margin": 10050.0,
                "margin_level": 0.0
            }
        }
        
        logger.info("MT5 status check completed")
        return status_data
        
    except Exception as e:
        logger.error(f"MT5 status error: {e}")
        return {"connected": False, "error": str(e)}

@app.get("/api/mt5/balance")
async def mt5_balance():
    """Get account balance information."""
    try:
        # Mock balance data - replace with actual MT5 balance fetch
        balance_data = {
            "balance": 10000.0,
            "equity": 10050.0,
            "margin": 0.0,
            "free_margin": 10050.0,
            "margin_level": 0.0,
            "currency": "USD"
        }
        
        logger.info("MT5 balance fetched")
        return balance_data
        
    except Exception as e:
        logger.error(f"MT5 balance error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch balance")

@app.get("/api/mt5/account")
async def mt5_account():
    """Get detailed account information."""
    try:
        # Mock account data - replace with actual MT5 account info
        account_data = {
            "login": "12345678",
            "server": "MetaQuotes-Demo",
            "balance": 10000.0,
            "equity": 10050.0,
            "margin": 0.0,
            "free_margin": 10050.0,
            "margin_level": 0.0,
            "currency": "USD",
            "leverage": 100,
            "company": "MetaQuotes Software Corp."
        }
        
        logger.info("MT5 account info fetched")
        return account_data
        
    except Exception as e:
        logger.error(f"MT5 account error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch account info")

@app.post("/api/mt5/order")
async def mt5_order(order_data: dict):
    """Place a market order."""
    try:
        symbol = order_data.get("symbol")
        lot = order_data.get("lot")
        order_type = order_data.get("type")
        sl = order_data.get("sl")
        tp = order_data.get("tp")
        
        if not all([symbol, lot, order_type]):
            raise HTTPException(status_code=400, detail="Missing required order parameters")
        
        # Mock order placement - replace with actual MT5 order
        ticket = 12345678  # Mock ticket number
        
        logger.info(f"Placing {order_type} order: {symbol} {lot} lots")
        
        order_result = {
            "success": True,
            "ticket": ticket,
            "symbol": symbol,
            "lot": lot,
            "type": order_type,
            "price": 1.0855 if order_type == "buy" else 1.0850,
            "sl": sl,
            "tp": tp
        }
        
        logger.info(f"Order placed successfully: {ticket}")
        return order_result
        
    except Exception as e:
        logger.error(f"MT5 order error: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/mt5/positions")
async def mt5_positions():
    """Get open positions."""
    try:
        # Mock positions data - replace with actual MT5 positions fetch
        positions = [
            {
                "ticket": 12345678,
                "symbol": "EURUSD",
                "type": "buy",
                "lot": 0.1,
                "price_open": 1.0855,
                "price_current": 1.0860,
                "profit": 5.0,
                "sl": 1.0820,
                "tp": 1.0900
            },
            {
                "ticket": 12345679,
                "symbol": "GBPUSD",
                "type": "sell",
                "lot": 0.05,
                "price_open": 1.2655,
                "price_current": 1.2650,
                "profit": 2.5,
                "sl": 1.2700,
                "tp": 1.2600
            }
        ]
        
        logger.info(f"Fetched {len(positions)} open positions")
        return positions
        
    except Exception as e:
        logger.error(f"MT5 positions error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch positions")

@app.get("/api/mt5/orders")
async def mt5_orders():
    """Get pending orders."""
    try:
        # Mock pending orders data - replace with actual MT5 orders fetch
        orders = [
            {
                "ticket": 12345680,
                "symbol": "USDJPY",
                "type": "buylimit",
                "lot": 0.1,
                "price": 150.50,
                "sl": 150.20,
                "tp": 151.00
            }
        ]
        
        logger.info(f"Fetched {len(orders)} pending orders")
        return orders
        
    except Exception as e:
        logger.error(f"MT5 orders error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch orders")

@app.post("/api/mt5/close/{ticket}")
async def mt5_close_position(ticket: int):
    """Close a specific position."""
    try:
        # Mock position close - replace with actual MT5 close operation
        logger.info(f"Closing position: {ticket}")
        
        close_result = {
            "success": True,
            "ticket": ticket,
            "message": "Position closed successfully"
        }
        
        logger.info(f"Position {ticket} closed successfully")
        return close_result
        
    except Exception as e:
        logger.error(f"MT5 close position error: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/mt5/closeall")
async def mt5_close_all():
    """Close all positions."""
    try:
        # Mock close all - replace with actual MT5 close all operation
        logger.info("Closing all positions")
        
        close_result = {
            "success": True,
            "closed_count": 2,
            "message": "All positions closed successfully"
        }
        
        logger.info("All positions closed successfully")
        return close_result
        
    except Exception as e:
        logger.error(f"MT5 close all error: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/mt5/price/{symbol}")
async def mt5_price(symbol: str):
    """Get current price for a symbol."""
    try:
        # Mock price data - replace with actual MT5 price fetch
        price_data = {
            "symbol": symbol.upper(),
            "bid": 1.0850,
            "ask": 1.0855,
            "spread": 0.5,
            "time": "2024-01-01T12:00:00Z"
        }
        
        logger.info(f"Fetched price for {symbol}")
        return price_data
        
    except Exception as e:
        logger.error(f"MT5 price error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch price")

@app.get("/api/mt5/summary")
async def mt5_summary():
    """Get trading summary."""
    try:
        # Mock summary data - replace with actual MT5 summary calculation
        summary_data = {
            "total_pnl": 7.5,
            "open_positions": 2,
            "pending_orders": 1,
            "balance": 10000.0,
            "equity": 10007.5
        }
        
        logger.info("MT5 trading summary generated")
        return summary_data
        
    except Exception as e:
        logger.error(f"MT5 summary error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate summary")

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "message": str(exc)}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False) 