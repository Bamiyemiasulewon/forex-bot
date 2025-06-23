from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any

from app.services.market_service import market_service
from app.services.risk_service import risk_service
from app.services.signal_service import signal_service
from app.services.database_service import get_db_dependency, User, Trade, UserSettings
from sqlalchemy.orm import Session


router = APIRouter()

# --- Signal Endpoints ---
@router.get("/signals", response_model=List[Dict])
async def get_trading_signals():
    """Generate and return AI trading signals."""
    try:
        signals = await signal_service.generate_signals()
        if not signals:
            raise HTTPException(status_code=404, detail="No new trading signals found at the moment.")
        return signals
    except Exception as e:
        # Log the exception for debugging
        # logger.error(f"Failed to generate signals: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail="The signal generation service is temporarily unavailable. Please try again later.")

# --- Market Data Endpoints ---
@router.get("/market/{pair}", response_model=Dict)
async def get_market_data(pair: str):
    """Fetch market data for a given pair."""
    data = await market_service.get_market_data(pair)
    if not data:
        raise HTTPException(status_code=404, detail=f"Market data for {pair} not found or pair is unsupported.")
    return data

# --- Calculator Endpoints ---
@router.get("/pipcalc/{pair}/{trade_size}")
async def get_pip_value(pair: str, trade_size: float):
    """Calculate the value of a single pip in USD."""
    value = await market_service.get_pip_value_in_usd(pair, trade_size)
    if value is None:
        raise HTTPException(status_code=400, detail=f"Could not calculate pip value for {pair}.")
    return {"pair": pair, "trade_size": trade_size, "pip_value_usd": value}

@router.get("/risk/{pair}/{risk_percent}/{stop_loss_pips}")
async def get_risk_calculation(pair: str, risk_percent: float, stop_loss_pips: float, db: Session = Depends(get_db_dependency)):
    """Calculate position size based on risk parameters."""
    # In a real app, you'd get the user's balance from their authenticated session
    # For now, we'll use a default or fetch a default user.
    user = db.query(User).first()
    account_balance = user.account_balance if user else 10000.0 # Default balance

    calculation = await risk_service.calculate_position_size(
        account_balance=account_balance,
        risk_percent=risk_percent,
        stop_loss_pips=stop_loss_pips,
        pair=pair
    )
    if "error" in calculation:
        raise HTTPException(status_code=400, detail=calculation["error"])
    return calculation

# --- News and Calendar Endpoints ---
# @router.get("/news", response_model=List[Dict])
# async def get_forex_news():
#     """Fetch the latest forex news."""
#     news = news_service.get_forex_news()
#     if not news:
#         raise HTTPException(status_code=404, detail="Could not fetch forex news.")
#     return news
#
# @router.get("/calendar")
# async def get_economic_calendar():
#     """Placeholder for economic calendar."""
#     return {"message": "Economic calendar feature is coming soon!"}

# --- Strategy Endpoints ---
@router.get("/strategies")
async def get_strategies():
    """Placeholder for trading strategies."""
    return {
        "strategies": [
            "Trend Following", "Mean Reversion", "Breakout"
        ],
        "message": "Each signal uses one of these core strategies."
    }

# --- Trade History ---
@router.get("/trades")
async def get_trades(db: Session = Depends(get_db_dependency)):
    """Fetch user trades from the database."""
    # This should be authenticated to get trades for a specific user.
    trades = db.query(Trade).order_by(Trade.created_at.desc()).limit(20).all()
    return trades 

# --- User Balance Endpoint ---
@router.get("/balance", response_model=Dict)
async def get_user_balance(db: Session = Depends(get_db_dependency)):
    # TODO: Replace with real authentication to get the current user
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return {"balance": user.account_balance, "currency": "USD"}

# --- User Settings Endpoint ---
@router.get("/settings", response_model=Dict)
async def get_user_settings(telegram_id: int = Query(...), db: Session = Depends(get_db_dependency)):
    # Fetch user by telegram_id
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user or not user.settings:
        raise HTTPException(status_code=404, detail="User settings not found.")
    settings = user.settings
    return {
        "preferred_pairs": settings.preferred_pairs,
        "default_risk": settings.default_risk
    }

# --- Help/Support Endpoint ---
@router.get("/help", response_model=Dict)
async def get_help(telegram_id: int = Query(...)):
    # Optionally log or use telegram_id for support tracking
    return {
        "message": "For support, contact @YourSupportUsername or email support@example.com."
    } 