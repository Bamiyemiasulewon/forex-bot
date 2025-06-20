from app.models.trade import Trade
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

class PerformanceService:
    def __init__(self, db: Session):
        self.db = db

    def daily_performance(self, date=None):
        if date is None:
            date = datetime.utcnow().date()
        start = datetime.combine(date, datetime.min.time())
        end = datetime.combine(date, datetime.max.time())
        trades = self.db.query(Trade).filter(Trade.created_at >= start, Trade.created_at <= end).all()
        signals = len(trades)
        targets_hit = sum(1 for t in trades if t.status == 'target_hit')
        stops = sum(1 for t in trades if t.status == 'stopped')
        win_rate = (targets_hit / signals) * 100 if signals else 0
        pips = sum(getattr(t, 'pips', 0) for t in trades)
        rr = sum(getattr(t, 'rr', 0) for t in trades) / signals if signals else 0
        score = min(10, win_rate / 10)
        return {
            'signals': signals,
            'targets_hit': targets_hit,
            'stops': stops,
            'win_rate': win_rate,
            'pips': pips,
            'rr': rr,
            'score': score
        } 