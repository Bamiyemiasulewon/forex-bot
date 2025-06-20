from app.models.trade import Trade
from app.models.user import User
from app.models.signal import Signal
from sqlalchemy.orm import Session
from datetime import datetime

class TradeService:
    def __init__(self, db: Session):
        self.db = db

    def execute_trade(self, user_id: int, signal_id: int, symbol: str, order_type: str, amount: float, price: float):
        trade = Trade(
            user_id=user_id,
            signal_id=signal_id,
            symbol=symbol,
            order_type=order_type,
            amount=amount,
            price=price,
            status='executed'
        )
        self.db.add(trade)
        self.db.commit()
        return trade 