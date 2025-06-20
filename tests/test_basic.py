import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.strategy_engine import multi_strategy_signal
import pandas as pd
import logging

client = TestClient(app)

def test_root():
    response = client.get('/')
    assert response.status_code == 200
    assert 'Forex Trading Bot API' in response.json()['message']

def test_health():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'

def test_multi_strategy_signal():
    # Test with bullish data
    df = pd.DataFrame({'close': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]})
    result = multi_strategy_signal(df)
    assert isinstance(result, dict)
    assert 'signal' in result

def test_error_logging():
    try:
        raise ValueError("Test error")
    except Exception as e:
        logging.error("Test error caught", exc_info=e) 