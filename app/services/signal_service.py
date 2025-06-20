import pandas as pd
from app.models.signal import Signal
from app.models.price_data import PriceData
from sqlalchemy.orm import Session
from app.utils.indicators import calculate_rsi, calculate_macd
from datetime import datetime

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