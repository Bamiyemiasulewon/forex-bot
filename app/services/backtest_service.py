import pandas as pd
from app.models.price_data import PriceData
from sqlalchemy.orm import Session

class BacktestService:
    # Initialize the backtest service with a database session.
    def __init__(self, db: Session):
        self.db = db

    # Run a backtest for a given symbol and strategy function over a date range.
    # symbol: Forex pair symbol
    # strategy_func: Function to generate signals
    # start_date, end_date: Date range for backtest
    def run_backtest(self, symbol: str, strategy_func, start_date, end_date):
        prices = self.db.query(PriceData).filter(
            PriceData.symbol == symbol,
            PriceData.timestamp >= start_date,
            PriceData.timestamp <= end_date
        ).order_by(PriceData.timestamp).all()
        if not prices:
            return {'error': 'No price data'}
        df = pd.DataFrame([{
            'close': p.close,
            'timestamp': p.timestamp
        } for p in prices])
        results = strategy_func(df)
        return results 