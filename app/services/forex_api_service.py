import httpx
import logging
import time
from typing import Optional
from app.utils.config import config

logger = logging.getLogger(__name__)

class ForexAPIService:
    _instance = None
    _cache = {}
    _CACHE_TTL_SECONDS = 3600  # Cache for 1 hour

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ForexAPIService, cls).__new__(cls)
        return cls._instance

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = f"https://v6.exchangerate-api.com/v6/{self.api_key}"

    def _get_from_cache(self, key: str):
        if key in self._cache:
            data, timestamp = self._cache[key]
            if time.time() - timestamp < self._CACHE_TTL_SECONDS:
                logger.debug(f"Cache HIT for {key}")
                return data
        logger.debug(f"Cache MISS for {key}")
        return None

    def _set_in_cache(self, key: str, data):
        self._cache[key] = (data, time.time())

    async def _make_request(self, endpoint: str) -> Optional[dict]:
        if not self.api_key:
            logger.error("ExchangeRate-API key not configured.")
            return None
        
        url = f"{self.base_url}/{endpoint}"
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
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        return None

    async def get_exchange_rate(self, base_currency: str, target_currency: str) -> Optional[float]:
        cache_key = f"rate_{base_currency}_{target_currency}"
        cached_rate = self._get_from_cache(cache_key)
        if cached_rate:
            return cached_rate

        data = await self._make_request(f"pair/{base_currency}/{target_currency}")
        if data and "conversion_rate" in data:
            rate = float(data["conversion_rate"])
            self._set_in_cache(cache_key, rate)
            return rate
        return None

    async def get_pip_value_in_usd(self, pair: str, lot_size: float) -> Optional[float]:
        if len(pair) != 6:
            logger.error(f"Invalid currency pair format: {pair}")
            return None
            
        base_currency = pair[:3].upper()
        quote_currency = pair[3:].upper()
        
        # Standard pip size for most pairs
        pip_size = 0.0001
        # For JPY pairs, a pip is the second decimal place
        if "JPY" in quote_currency:
            pip_size = 0.01

        # Determine the value of one pip in the quote currency
        pip_value_in_quote_currency = pip_size * lot_size

        # If the quote currency is USD, no conversion is needed
        if quote_currency == "USD":
            return pip_value_in_quote_currency

        # If the quote currency is not USD, we need to convert it
        # We need the exchange rate between the quote currency and USD
        conversion_rate = await self.get_exchange_rate(quote_currency, "USD")
        
        if conversion_rate is None:
            logger.error(f"Could not get conversion rate from {quote_currency} to USD")
            return None
            
        return pip_value_in_quote_currency * conversion_rate


# Initialize the service with the key from config
forex_api_service = ForexAPIService(api_key=config.exchangerate_api_key) 