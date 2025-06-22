import os
import httpx
import logging
import time
import asyncio
from alpha_vantage.foreignexchange import ForeignExchange

logger = logging.getLogger(__name__)

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
BASE_URL = "https://www.alphavantage.co/query"

class ForexAPIService:
    _instance = None
    _cache = {}
    _CACHE_TTL_SECONDS = 300  # Cache for 5 minutes

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ForexAPIService, cls).__new__(cls)
        return cls._instance

    def __init__(self, api_key: str):
        if not api_key:
            logger.warning("ALPHA_VANTAGE_API_KEY is not set. Forex data commands will not work.")
            self.fe = None
        else:
            try:
                self.fe = ForeignExchange(key=api_key, output_format='json')
            except Exception as e:
                logger.error(f"Failed to initialize Alpha Vantage client: {e}")
                self.fe = None
        self.api_key = api_key

    def _get_from_cache(self, key: str):
        if key in self._cache:
            data, timestamp = self._cache[key]
            if time.time() - timestamp < self._CACHE_TTL_SECONDS:
                logger.debug(f"Cache HIT for {key}")
                return data
            else:
                logger.debug(f"Cache EXPIRED for {key}")
                del self._cache[key]
        logger.debug(f"Cache MISS for {key}")
        return None

    def _set_in_cache(self, key: str, data):
        self._cache[key] = (data, time.time())

    async def get_live_quote(self, from_currency: str, to_currency: str) -> float | None:
        """Gets a live exchange rate for a currency pair."""
        cache_key = f"quote_{from_currency}_{to_currency}"
        cached_rate = self._get_from_cache(cache_key)
        if cached_rate:
            return cached_rate

        if not self.fe:
            logger.error("Forex API client not initialized.")
            return None
        
        try:
            # Alpha Vantage API call is blocking, run in thread to not block asyncio event loop
            loop = asyncio.get_event_loop()
            data, _ = await loop.run_in_executor(
                None, self.fe.get_currency_exchange_rate, from_currency, to_currency
            )
            rate = float(data['5. Exchange Rate'])
            self._set_in_cache(cache_key, rate)
            return rate
        except Exception as e:
            logger.error(f"Error fetching quote for {from_currency}/{to_currency}: {e}")
            return None

    async def get_technical_analysis(self, symbol: str) -> dict | None:
        """Gets technical analysis for a symbol."""
        if not self.api_key: return None
        # Placeholder
        logger.info(f"Fetching technical analysis for {symbol}")
        return {"symbol": symbol, "trend": "Uptrend", "support": "1.0800", "resistance": "1.1000"}

    async def get_forex_news(self) -> list[dict] | None:
        """Gets the latest forex news."""
        if not self.api_key: return None
        # Placeholder
        logger.info("Fetching forex news")
        return [
            {"title": "Fed Chair Hints at Future Rate Cuts", "source": "Reuters"},
            {"title": "ECB Holds Rates Steady Amid Inflation Concerns", "source": "Bloomberg"}
        ]

    async def get_economic_calendar(self) -> list[dict] | None:
        """Gets upcoming economic events."""
        if not self.api_key: return None
        # Placeholder
        logger.info("Fetching economic calendar")
        return [
            {"event": "US Non-Farm Payrolls", "impact": "High", "time": "Tomorrow 8:30 AM EST"},
            {"event": "Eurozone CPI", "impact": "Medium", "time": "Friday 5:00 AM EST"}
        ]

forex_api_service = ForexAPIService(api_key=ALPHA_VANTAGE_API_KEY) 