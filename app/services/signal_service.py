import pandas as pd
from app.utils.indicators import calculate_rsi
from typing import List, Dict, Optional
from app.services.market_service import market_service
from app.services.order_block_strategy import order_block_strategy
import asyncio
import logging
import httpx
from app.utils.secrets import ALPHA_VANTAGE_API_KEY
import time

logger = logging.getLogger(__name__)

class SignalService:
    def __init__(self):
        # Expanded list of major forex pairs to generate signals for (no slashes)
        self.pairs_to_scan = [
            "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "NZDUSD", "USDCAD",
            "EURGBP", "EURJPY", "GBPJPY", "AUDJPY", "EURCHF"
        ]
        self.alpha_vantage_api_key = ALPHA_VANTAGE_API_KEY
        self.base_url = "https://www.alphavantage.co/query"
        self._last_signals_cache = None
        self._last_signals_time = 0
        self._lock = asyncio.Lock()  # For throttling and concurrency
        self._pair_signal_cache = {}  # {pair: (signal, timestamp)}

    async def fetch_ohlcv(self, pair: str, interval: str = '60min', outputsize: str = 'compact') -> Optional[pd.DataFrame]:
        """Fetch historical OHLCV data for a forex pair from Alpha Vantage."""
        if pair == 'XAUUSD':
            # Use TIME_SERIES_DAILY for gold (XAUUSD)
            params = {
                "function": "TIME_SERIES_DAILY",
                "symbol": "XAUUSD",
                "outputsize": outputsize,
                "apikey": self.alpha_vantage_api_key
            }
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(self.base_url, params=params, timeout=10)
                    resp.raise_for_status()
                    data = resp.json()
                    time_series = data.get("Time Series (Daily)", {})
                    if not time_series:
                        logger.warning(f"No OHLCV data for {pair}")
                        return None
                    df = pd.DataFrame.from_dict(time_series, orient='index')
                    df = df.rename(columns={
                        '1. open': 'open',
                        '2. high': 'high',
                        '3. low': 'low',
                        '4. close': 'close',
                        '5. volume': 'volume'
                    })
                    df = df.astype(float)
                    df = df.sort_index()  # Oldest first
                    return df
            except Exception as e:
                logger.error(f"Error fetching OHLCV for {pair} from Alpha Vantage: {e}", exc_info=True)
                return None
        # Default FX logic
        from_symbol, to_symbol = pair[:3], pair[3:]
        params = {
            "function": "FX_INTRADAY",
            "from_symbol": from_symbol,
            "to_symbol": to_symbol,
            "interval": interval,
            "outputsize": outputsize,
            "apikey": self.alpha_vantage_api_key
        }
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(self.base_url, params=params, timeout=10)
                resp.raise_for_status()
                data = resp.json()
                # Alpha Vantage rate limit error detection
                if any("Thank you for using Alpha Vantage" in str(v) for v in data.values()):
                    logger.warning(f"Alpha Vantage rate limit hit for {pair}")
                    raise RuntimeError("rate_limited")
                time_series = data.get(f"Time Series FX ({interval})", {})
                if not time_series:
                    logger.warning(f"No OHLCV data for {pair}")
                    return None
                df = pd.DataFrame.from_dict(time_series, orient='index')
                df = df.rename(columns={
                    '1. open': 'open',
                    '2. high': 'high',
                    '3. low': 'low',
                    '4. close': 'close'
                })
                df = df.astype(float)
                df = df.sort_index()  # Oldest first
                return df
        except RuntimeError as e:
            if str(e) == "rate_limited":
                raise
            logger.error(f"Error fetching OHLCV for {pair} from Alpha Vantage: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Error fetching OHLCV for {pair} from Alpha Vantage: {e}", exc_info=True)
            return None

    async def generate_signals(self) -> List[Dict]:
        """
        Generates a list of real trading signals based on both RSI and Order Block + RSI + Fibonacci strategies.
        Throttles requests to Alpha Vantage to 1 every 12 seconds (5 per minute).
        Caches last successful signals as fallback if rate-limited.
        """
        async with self._lock:
            now = time.time()
            # If last signals were generated less than 12 seconds ago, return cached
            if self._last_signals_cache and now - self._last_signals_time < 12:
                logger.info("Returning cached signals due to throttling.")
                return self._last_signals_cache
            signals = []
            for i, pair in enumerate(self.pairs_to_scan):
                try:
                    # Throttle: 1 request every 12 seconds
                    if i > 0:
                        await asyncio.sleep(12)
                    signal = await self.analyze_pair_for_signal(pair)
                    if signal:
                        signals.append(signal)
                except RuntimeError as e:
                    if str(e) == "rate_limited":
                        logger.warning("Alpha Vantage rate limit hit. Returning cached signals if available.")
                        if self._last_signals_cache:
                            # Return cached signals with a warning
                            warning = {"warning": "⚠️ Data provider rate limit hit. Showing last available signals."}
                            return [warning] + self._last_signals_cache
                        else:
                            # Return a user-friendly error message
                            return [{"error": "⚠️ Signal generation is temporarily limited by our data provider. Please try again in a minute."}]
                except Exception as e:
                    logger.error(f"Error generating signal for {pair}: {e}", exc_info=True)
            if signals:
                self._last_signals_cache = signals
                self._last_signals_time = time.time()
            return signals

    async def analyze_pair_for_signal(self, pair: str) -> Optional[Dict]:
        """Analyzes a single pair and returns a signal if conditions are met for either strategy."""
        try:
            # Fetch historical data (e.g., 1-hour timeframe for the last 100 hours)
            df = await self.fetch_ohlcv(pair, interval='60min', outputsize='compact')
            if df is None or len(df) < 50:
                logger.info(f"Not enough historical data for {pair}, skipping.")
                return None
            
            # Get current price for signal details
            ticker = await market_service.get_market_data(pair)
            if not ticker or not ticker.get('price'):
                logger.warning(f"Could not fetch ticker data for {pair}, skipping.")
                return None
            current_price = ticker['price']
            
            # Try Order Block + RSI + Fibonacci strategy first (higher priority)
            order_block_signal = order_block_strategy.analyze_pair(df)
            if order_block_signal:
                # Add current price and pair info
                order_block_signal.update({
                    'pair': pair,
                    'current_price': current_price,
                    'priority': 'high'
                })
                logger.info(f"Order Block signal generated for {pair}: {order_block_signal['signal']}")
                return order_block_signal
            
            # Fallback to RSI strategy if no Order Block signal
            rsi_signal = await self._analyze_rsi_strategy(df, pair, current_price)
            if rsi_signal:
                rsi_signal['priority'] = 'medium'
                return rsi_signal
            
            return None
        except RuntimeError as e:
            if str(e) == "rate_limited":
                raise
            logger.error(f"Could not generate signal for {pair}: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Could not generate signal for {pair}: {e}", exc_info=True)
            return None

    async def _analyze_rsi_strategy(self, df: pd.DataFrame, pair: str, current_price: float) -> Optional[Dict]:
        """Analyze pair using RSI strategy (fallback method)."""
        # Calculate RSI
        rsi = calculate_rsi(df['close'])
        last_rsi = rsi.iloc[-1]
        
        # Dynamic stop-loss based on recent volatility (e.g., Average True Range)
        df['tr'] = pd.DataFrame([
            df['high'] - df['low'],
            abs(df['high'] - df['close'].shift()),
            abs(df['low'] - df['close'].shift())
        ]).max()
        atr = df['tr'].rolling(14).mean().iloc[-1]
        stop_loss = atr * 1.5  # Example: 1.5 * ATR
        
        signal = None
        # Overbought/Oversold thresholds can be fine-tuned
        if last_rsi > 75:  # Overbought condition
            signal = {
                "pair": pair, 
                "strategy": "RSI Overbought",
                "entry_range": f"{current_price:.5f} - {current_price - atr*0.5:.5f}",
                "stop_loss": round(current_price + stop_loss, 5),
                "take_profit": round(current_price - (stop_loss * 2), 5),  # 1:2 R:R
                "confidence": f"{min(95, int(last_rsi) + 20)}%",
                "risk_reward_ratio": "1:2",
                "rsi_value": last_rsi
            }
        elif last_rsi < 25:  # Oversold condition
            signal = {
                "pair": pair, 
                "strategy": "RSI Oversold",
                "entry_range": f"{current_price:.5f} - {current_price + atr*0.5:.5f}",
                "stop_loss": round(current_price - stop_loss, 5),
                "take_profit": round(current_price + (stop_loss * 2), 5),  # 1:2 R:R
                "confidence": f"{min(95, int(100 - last_rsi) + 20)}%",
                "risk_reward_ratio": "1:2",
                "rsi_value": last_rsi
            }
        
        return signal

    def get_strategy_status(self) -> Dict:
        """Get status of all available strategies."""
        return {
            "order_block_strategy": order_block_strategy.get_strategy_info(),
            "rsi_strategy": {
                "name": "RSI Overbought/Oversold",
                "timeframe": "1H",
                "conditions": "RSI > 75 (sell) or RSI < 25 (buy)",
                "risk_reward": "1:2"
            }
        }

    async def get_signal_for_pair(self, pair: str) -> Optional[Dict]:
        """Get a signal for a specific pair, with rate limit fallback to cached signal."""
        cache_duration = 60  # seconds
        now = time.time()
        # Check per-pair cache first
        cached = self._pair_signal_cache.get(pair)
        if cached and now - cached[1] < cache_duration:
            return cached[0]
        try:
            signal = await self.analyze_pair_for_signal(pair)
            if signal:
                self._pair_signal_cache[pair] = (signal, now)
                return signal
        except RuntimeError as e:
            if str(e) == "rate_limited":
                # Try to return cached signal for this pair
                if cached and now - cached[1] < cache_duration:
                    return {"warning": "\u26a0\ufe0f Data provider rate limit hit. Showing last available signal.", **cached[0]}
                return {"error": "\u26a0\ufe0f Signal temporarily unavailable due to data provider rate limit. Please try again in a minute."}
        except Exception as e:
            logger.error(f"Error in get_signal_for_pair for {pair}: {e}", exc_info=True)
            return {"error": f"Error fetching signal for {pair}: {e}"}
        return {"error": f"No signal available for {pair} at this time."}

signal_service = SignalService() 