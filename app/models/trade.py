from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Trade(Base):
    __tablename__ = 'trades'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    signal_id = Column(Integer, ForeignKey('signals.id'), nullable=True)
    symbol = Column(String, nullable=False)
    order_type = Column(String, nullable=False)  # 'buy' or 'sell'
    amount = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    status = Column(String, default='pending')
    created_at = Column(DateTime(timezone=True), server_default=func.now()) 