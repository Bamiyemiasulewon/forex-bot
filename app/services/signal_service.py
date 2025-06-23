import pandas as pd
from app.models.signal import Signal
from app.models.price_data import PriceData
from sqlalchemy.orm import Session
from app.utils.indicators import calculate_rsi, calculate_macd
from datetime import datetime
from typing import List, Dict
from fastapi import Depends
from app.services.database_service import get_db_dependency

class SignalService:
    def __init__(self, db: Session):
        self.db = db

    def generate_signal(self, symbol: str):
        prices = self.db.query(PriceData).filter(PriceData.symbol == symbol).order_by(PriceData.timestamp.desc()).limit(100).all()
        if not prices:
            return None
        df = pd.DataFrame([{
            'close': p.close,
            'timestamp': p.timestamp
        } for p in prices])
        rsi = calculate_rsi(df['close'])
        macd, signal_line = calculate_macd(df['close'])
        # Example logic
        if rsi[-1] < 30 and macd[-1] > signal_line[-1]:
            signal_type = 'buy'
            confidence = 0.8
        elif rsi[-1] > 70 and macd[-1] < signal_line[-1]:
            signal_type = 'sell'
            confidence = 0.8
        else:
            signal_type = 'hold'
            confidence = 0.5
        signal = Signal(symbol=symbol, signal_type=signal_type, confidence=confidence)
        self.db.add(signal)
        self.db.commit()
        return signal

    def generate_signals(self) -> List[Dict]:
        """
        Generates a list of trading signals.
        
        This is a placeholder implementation. In a real application, this would
        involve complex logic, data analysis, and potentially machine learning models.
        """
        # Mock data representing real signals
        signals = [
            {
                "signal_id": "SIG_2847",
                "pair": "EURUSD",
                "strategy": "Trend Breakout",
                "entry_range": "1.0850-1.0860",
                "stop_loss": 1.0830,
                "take_profit": 1.0900,
                "risk_reward_ratio": "1:2.5",
                "confidence": "87%",
                "valid_for_hours": 4
            },
            {
                "signal_id": "SIG_2848",
                "pair": "GBPJPY",
                "strategy": "Mean Reversion",
                "entry_range": "198.20-198.30",
                "stop_loss": 198.70,
                "take_profit": 197.50,
                "risk_reward_ratio": "1:1.4",
                "confidence": "92%",
                "valid_for_hours": 2
            }
        ]
        return signals

def get_signal_service(db: Session = Depends(get_db_dependency)) -> SignalService:
    return SignalService(db) 