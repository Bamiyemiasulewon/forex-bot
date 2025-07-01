import httpx
import logging
import time
from typing import Optional, Dict, Any
from app.utils.secrets import ALPHA_VANTAGE_API_KEY
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
        self.alpha_vantage_api_key = ALPHA_VANTAGE_API_KEY
        self.base_url = "https://www.alphavantage.co/query"
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

    async def get_market_data(self, pair: str) -> Optional[Dict]:
        """Fetches real-time forex market data for a given pair using Alpha Vantage."""
        pair = pair.upper()
        if not self._is_supported_pair(pair):
            logger.warning(f"Unsupported forex pair requested: {pair}")
            return {"error": f"Pair {pair} is not supported. Please use a major forex pair like EURUSD."}
        cache_key = f"market_data_{pair}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data
        # Special handling for Gold (XAUUSD)
        if pair == "XAUUSD":
            from_symbol, to_symbol = "XAU", "USD"
        else:
            from_symbol, to_symbol = pair[:3], pair[3:]
        params = {
            "function": "CURRENCY_EXCHANGE_RATE",
            "from_currency": from_symbol,
            "to_currency": to_symbol,
            "apikey": self.alpha_vantage_api_key
        }
        async with self._lock:
            now = time.time()
            # Throttle: 1 request every 12 seconds
            if self._last_market_time and now - self._last_market_time < 12:
                logger.info("Throttling market data request, returning last cache if available.")
                if cache_key in self._last_market_cache:
                    return self._last_market_cache[cache_key]
        try:
            async with httpx.AsyncClient() as client:
                    resp = await client.get(self.base_url, params=params, timeout=10)
                    resp.raise_for_status()
                    data = resp.json()
                    # Alpha Vantage rate limit error detection
                    if any("Thank you for using Alpha Vantage" in str(v) for v in data.values()):
                        logger.warning(f"Alpha Vantage rate limit hit for {pair}")
                        return {"error": "⚠️ The system is temporarily rate-limited by our data provider. Please wait a moment and try again."}
                    rate_info = data.get("Realtime Currency Exchange Rate", {})
                    if not rate_info or "5. Exchange Rate" not in rate_info:
                        logger.warning(f"No rate info for {pair}")
                        return {"error": f"No market data available for {pair} at this time."}
                    result = {
                        "pair": pair,
                        "price": float(rate_info["5. Exchange Rate"]),
                        "timestamp": rate_info.get("6. Last Refreshed", "N/A")
                    }
                    self._set_in_cache(cache_key, result)
                    self._last_market_cache[cache_key] = result
                    self._last_market_time = time.time()
                    return result
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching market data for {pair}: {e.response.status_code}")
            return {"error": f"HTTP error fetching market data for {pair}. Please try again later."}
        except httpx.RequestError as e:
            logger.error(f"Network error fetching market data for {pair}: {e}")
            return {"error": f"Network error fetching market data for {pair}. Please check your connection and try again."}
        except Exception as e:
            logger.error(f"Unexpected error fetching market data for {pair}: {e}", exc_info=True)
            return {"error": f"An unexpected error occurred while fetching market data for {pair}. Please try again later."}

# Create a single instance
market_service = MarketService()

# No exchange connection to close, but keep shutdown_event for compatibility
def shutdown_event():
    pass
atexit.register(shutdown_event) 