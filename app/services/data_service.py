import yfinance as yf
from app.models.price_data import PriceData
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.audit_log import AuditLog
from sqlalchemy.exc import SQLAlchemyError

class DataService:
    # Initialize the data service with a database session.
    def __init__(self, db: Session):
        self.db = db

    # Fetch price data from yfinance and store it in the database.
    # symbol: Forex pair symbol (e.g., 'EURUSD')
    # interval: Data interval (e.g., '1h')
    # period: Data period (e.g., '7d')
    def fetch_and_store_price_data(self, symbol: str, interval: str = '1h', period: str = '7d'):
        if not symbol.isalnum() or len(symbol) > 10:
            raise ValueError("Invalid symbol")
        try:
            data = yf.download(symbol, interval=interval, period=period)
            for idx, row in data.iterrows():
                price = PriceData(
                    symbol=symbol,
                    timestamp=idx.to_pydatetime() if hasattr(idx, 'to_pydatetime') else idx,
                    open=row['Open'],
                    high=row['High'],
                    low=row['Low'],
                    close=row['Close'],
                    volume=row['Volume']
                )
                self.db.merge(price)
            self.db.commit()
            self.db.add(AuditLog(user_id=None, action='fetch_and_store_price_data', details=f'symbol={symbol}'))
            self.db.commit()
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e 