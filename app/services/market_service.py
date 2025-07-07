import httpx
import logging
import time
from typing import Optional, Dict, Any
# Remove Alpha Vantage imports and API key usage
import asyncio
import atexit

logger = logging.getLogger(__name__)

# List of supported major/minor forex pairs (expand as needed)
SUPPORTED_FOREX_PAIRS = [
    'EURUSD', 'USDJPY', 'GBPUSD', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD',
    'EURJPY', 'GBPJPY', 'EURGBP', 'EURCHF', 'AUDJPY', 'CHFJPY', 'EURAUD',
    'EURCAD', 'GBPCAD', 'GBPAUD', 'AUDCAD', 'AUDNZD', 'NZDCAD', 'NZDJPY',
    'CADJPY', 'CADCHF', 'AUDCHF', 'NZDCHF', 'XAUUSD'
]

class MarketService:
    def __init__(self):
        # Remove Alpha Vantage imports and API key usage
        self._cache = {}
        self._CACHE_TTL_SECONDS = 30
        self._lock = asyncio.Lock()
        self._last_market_time = 0
        self._last_market_cache = {}

    def _get_from_cache(self, key: str) -> Any:
        if key in self._cache:
            data, timestamp = self._cache[key]
            if time.time() - timestamp < self._CACHE_TTL_SECONDS:
                logger.debug(f"Cache HIT for {key}")
                return data
        logger.debug(f"Cache MISS for {key}")
        return None

    def _set_in_cache(self, key: str, data: Any):
        self._cache[key] = (data, time.time())

    def _is_supported_pair(self, pair: str) -> bool:
        return pair.upper() in SUPPORTED_FOREX_PAIRS

    # Remove get_market_data and any Alpha Vantage logic
    async def get_pip_value_in_usd(self, pair: str, trade_size: float) -> float:
        pair = pair.upper()
        if pair == 'XAUUSD':
            # Gold: 1 pip = 0.01, contract size = 100 oz, pip value = contract_size * pip_size * lots
            pip_size = 0.01
            contract_size = 100
            pip_value = contract_size * pip_size * trade_size
            return pip_value
        elif pair.endswith('JPY'):
            pip_size = 0.01
            contract_size = 100000
        else:
            pip_size = 0.0001
            contract_size = 100000
        pip_value = contract_size * pip_size * trade_size
        return pip_value

# Create a single instance
market_service = MarketService()

# No exchange connection to close, but keep shutdown_event for compatibility
def shutdown_event():
    pass
atexit.register(shutdown_event) 