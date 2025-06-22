import httpx
import logging
import time
import yfinance as yf
from typing import Optional, Dict, Any
from app.utils.config import config

logger = logging.getLogger(__name__)

class MarketService:
    _instance = None
    _cache = {}
    _CACHE_TTL_SECONDS = 60  # Cache for 1 minute for market data

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(MarketService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self.exchangerate_api_key = config.exchangerate_api_key
        self.exchangerate_base_url = f"https://v6.exchangerate-api.com/v6/{self.exchangerate_api_key}"

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

    async def _make_exchangerate_request(self, endpoint: str) -> Optional[Dict]:
        if not self.exchangerate_api_key:
            logger.error("ExchangeRate-API key not configured.")
            return None
        
        url = f"{self.exchangerate_base_url}/{endpoint}"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                if data.get("result") == "success":
                    return data
                else:
                    error_type = data.get("error-type", "unknown_error")
                    logger.error(f"ExchangeRate-API error: {error_type}")
                    return None
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching data: {e.response.status_code} for URL {e.request.url}")
        except httpx.RequestError as e:
            logger.error(f"Request error fetching data: {e}")
        return None

    async def get_exchange_rate(self, base_currency: str, target_currency: str) -> Optional[float]:
        cache_key = f"rate_{base_currency}_{target_currency}"
        cached_rate = self._get_from_cache(cache_key)
        if cached_rate:
            return cached_rate

        data = await self._make_exchangerate_request(f"pair/{base_currency}/{target_currency}")
        if data and "conversion_rate" in data:
            rate = float(data["conversion_rate"])
            self._set_in_cache(cache_key, rate)
            return rate
        return None
        
    async def get_pip_value_in_usd(self, pair: str, trade_size: float) -> Optional[float]:
        if len(pair) != 6:
            logger.error(f"Invalid currency pair format: {pair}")
            return None
            
        base_currency = pair[:3].upper()
        quote_currency = pair[3:].upper()
        
        pip_size = 0.0001
        if "JPY" in quote_currency.upper():
            pip_size = 0.01

        pip_value_in_quote = pip_size * trade_size

        if quote_currency.upper() == "USD":
            return pip_value_in_quote

        conversion_rate = await self.get_exchange_rate(quote_currency, "USD")
        
        if conversion_rate is None:
            logger.error(f"Could not get conversion rate from {quote_currency} to USD")
            return None
            
        return pip_value_in_quote * conversion_rate

    async def get_market_data(self, pair: str) -> Optional[Dict]:
        """Fetches detailed market data for a pair using yfinance."""
        cache_key = f"market_data_{pair}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data

        try:
            ticker_pair = f"{pair.upper()}=X"
            ticker = yf.Ticker(ticker_pair)
            info = ticker.info

            price = info.get('regularMarketPrice') or info.get('previousClose')
            if not price:
                 logger.warning(f"yfinance data for {pair} is missing price. Data: {info}")
                 return None

            data = {
                'price': price,
                'high': info.get('dayHigh'),
                'low': info.get('dayLow'),
                'open': info.get('regularMarketOpen'),
                'high_52wk': info.get('fiftyTwoWeekHigh'),
                'low_52wk': info.get('fiftyTwoWeekLow'),
                'volume': info.get('regularMarketVolume', 0),
                'pair': pair
            }
            self._set_in_cache(cache_key, data)
            return data
        except Exception as e:
            logger.error(f"yfinance error fetching market data for {pair}: {e}", exc_info=True)
            return None

# Singleton instance
market_service = MarketService() 