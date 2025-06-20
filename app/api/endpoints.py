from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.signal import Signal
from app.models.trade import Trade
from app.models.price_data import PriceData
from typing import List
from app.api.auth import router as auth_router

router = APIRouter()
router.include_router(auth_router, prefix='/auth')

@router.get('/users', response_model=List[dict])
def list_users():
    # Placeholder: return list of users
    return []

@router.get('/signals', response_model=List[dict])
def list_signals():
    # Placeholder: return list of signals
    return []

@router.get('/trades', response_model=List[dict])
def list_trades():
    # Placeholder: return list of trades
    return []

@router.get('/price-data', response_model=List[dict])
def list_price_data():
    # Placeholder: return list of price data
    return [] 