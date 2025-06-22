from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any

from app.services.market_service import market_service
from app.services.risk_service import risk_service
from app.services.signal_service import SignalService, get_signal_service
from app.services.database_service import get_db, User, Trade
from sqlalchemy.orm import Session


router = APIRouter()

# --- Signal Endpoints ---
@router.get("/signals", response_model=List[Dict])
async def get_trading_signals(signal_service: SignalService = Depends(get_signal_service)):
    """Generate and return AI trading signals."""
    signals = signal_service.generate_signals()
    if not signals:
        raise HTTPException(status_code=404, detail="No signals available at the moment.")
    return signals

# --- Calculator Endpoints ---
@router.get("/pipcalc/{pair}/{trade_size}")
async def get_pip_value(pair: str, trade_size: float):
    """Calculate the value of a single pip in USD."""
    value = await market_service.get_pip_value_in_usd(pair, trade_size)
    if value is None:
        raise HTTPException(status_code=400, detail=f"Could not calculate pip value for {pair}.")
    return {"pair": pair, "trade_size": trade_size, "pip_value_usd": value}

@router.get("/risk/{pair}/{risk_percent}/{stop_loss_pips}")
async def get_risk_calculation(pair: str, risk_percent: float, stop_loss_pips: float, db: Session = Depends(get_db)):
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
async def get_trades(db: Session = Depends(get_db)):
    """Fetch user trades from the database."""
    # This should be authenticated to get trades for a specific user.
    trades = db.query(Trade).order_by(Trade.created_at.desc()).limit(20).all()
    return trades 