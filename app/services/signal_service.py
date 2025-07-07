import pandas as pd
from app.utils.indicators import calculate_rsi
from typing import List, Dict, Optional
from app.services.market_service import market_service
from app.services.market_structure_strategy import market_structure_strategy
import asyncio
import logging
import time
from app.services.mt5_service import mt5_service

logger = logging.getLogger(__name__)

class SignalService:
    def __init__(self):
        # Expanded list of major forex pairs to generate signals for (no slashes)
        self.pairs_to_scan = [
            "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "NZDUSD", "USDCAD",
            "EURGBP", "EURJPY", "GBPJPY", "AUDJPY", "EURCHF", "XAUUSD"
        ]
        self._lock = asyncio.Lock()  # For throttling and concurrency
        self._pair_signal_cache = {}  # {pair: (signal, timestamp)}

    async def fetch_ohlcv(self, pair: str, interval: str = '15min', outputsize: str = 'compact'):
        """
        Fetch OHLCV (candlestick) data for a forex pair from the connected MT5 terminal.
        Args:
            pair: Symbol, e.g. 'EURUSD'
            interval: Timeframe string, e.g. '15min', '1h', '1d'
            outputsize: Only affects number of candles returned (for compatibility with old code)
        Returns:
            pd.DataFrame or None
        """
        # Map interval to MT5Service timeframe
        interval_map = {
            '1min': '1m', '5min': '5m', '15min': '15m', '30min': '30m',
            '1h': '1h', '4h': '4h', '1d': '1d',
            'M1': '1m', 'M5': '5m', 'M15': '15m', 'M30': '30m',
            'H1': '1h', 'H4': '4h', 'D1': '1d',
        }
        tf = interval_map.get(interval.lower(), '15m')
        count = 1000 if outputsize == 'full' else 100
        # Only fetch from MT5, never raise rate limit errors
        return await mt5_service.get_candles(pair, tf, count)

    async def generate_signals(self) -> List[Dict]:
        """
        Generates a list of real trading signals based on both RSI and Market Structure strategies.
        Uses only MT5 data. No external API or rate limit logic.
        """
        async with self._lock:
            signals = []
            for pair in self.pairs_to_scan:
                try:
                    signal = await self.analyze_pair_for_signal(pair)
                    if signal:
                        signals.append(signal)
                except Exception as e:
                    logger.error(f"Error generating signal for {pair}: {e}", exc_info=True)
            return signals

    async def analyze_pair_for_signal(self, pair: str) -> Optional[Dict]:
        """Analyzes a single pair and returns a signal if conditions are met for Market Structure strategy. Uses only MT5 data."""
        try:
            df = await self.fetch_ohlcv(pair, interval='15min', outputsize='compact')
            if df is None or len(df) < 50:
                logger.info(f"Not enough historical data for {pair}, skipping.")
                return None
            ticker = await market_service.get_market_data(pair)
            if not ticker or not ticker.get('price'):
                logger.warning(f"Could not fetch ticker data for {pair}, skipping.")
                return None
            current_price = ticker['price']
            market_structure_signal = market_structure_strategy.analyze_pair(df, pair)
            if market_structure_signal:
                market_structure_signal.update({
                    'pair': pair,
                    'current_price': current_price,
                    'priority': 'high'
                })
                logger.info(f"Market Structure signal generated for {pair}: {market_structure_signal['signal']}")
                return market_structure_signal
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
            "market_structure_strategy": market_structure_strategy.get_strategy_info(),
            "description": "Market Structure Strategy using multiple timeframes for trend analysis, POI detection, inducement identification, and FVG-based exits."
        }

    async def get_signal_for_pair(self, pair: str) -> Optional[Dict]:
        """Get a signal for a specific pair. Uses only MT5 data."""
        cache_duration = 60  # seconds
        now = time.time()
        cached = self._pair_signal_cache.get(pair)
        if cached and now - cached[1] < cache_duration:
            return cached[0]
        try:
            signal = await self.analyze_pair_for_signal(pair)
            if signal:
                self._pair_signal_cache[pair] = (signal, now)
                return signal
        except Exception as e:
            logger.error(f"Error in get_signal_for_pair for {pair}: {e}", exc_info=True)
            return {"error": f"Error fetching signal for {pair}: {e}"}
        return {"error": f"No signal available for {pair} at this time."}

    def clear_trade_history(self, user_id=None):
        """Clear trade history for the user (stub, implement as needed)."""
        # If you cache trade history per user, clear it here.
        pass

signal_service = SignalService() 