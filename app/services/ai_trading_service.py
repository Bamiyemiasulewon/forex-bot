# forex-bot/app/services/ai_trading_service.py
import asyncio
import logging
import pandas as pd
import pandas_ta as ta
import datetime

from .ai_config import AIConfig
from .ai_risk_manager import AIRiskManager
from .mt5_service import MT5Service
from .telegram_notifier import AITelegramNotifier # We will create this next

logger = logging.getLogger(__name__)

class AITradingService:
    """
    The core AI Trading Bot service that analyzes market data and executes trades.
    """
    def __init__(self, config: AIConfig, risk_manager: AIRiskManager, mt5_service: MT5Service, notifier: AITelegramNotifier):
        self.config = config
        self.risk_manager = risk_manager
        self.mt5 = mt5_service
        self.notifier = notifier
        self.is_running = False
        self.active_symbols = {} # To store dataframes
        self.mt5_alert_sent = False  # Track if MT5 not connected alert was sent

    async def start(self):
        """Starts the AI trading bot main loop."""
        if self.is_running:
            logger.warning("AI service is already running.")
            return
        self.is_running = True
        logger.info("🤖 AI Trading Service started.")
        # Start daily reset task
        asyncio.create_task(self._daily_reset_task())
        # This method will now run until self.is_running is False.
        await self._run_cycle()

    def stop(self):
        """Stops the AI trading bot main loop."""
        self.is_running = False
        logger.info("🛑 AI Trading Service stopped.")

    async def _daily_reset_task(self):
        """Background task to reset daily counters at midnight broker/server time, Monday to Friday."""
        while self.is_running:
            now = await self.mt5.get_server_time()
            # Calculate seconds until next midnight
            next_midnight = (now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            seconds_until_midnight = (next_midnight - now).total_seconds()
            await asyncio.sleep(seconds_until_midnight)
            # Only reset if it's a weekday (Monday=0, ..., Friday=4)
            weekday = next_midnight.weekday()
            if weekday < 5:
                try:
                    self.risk_manager.reset_daily_counters()
                    logger.info("Daily trade counters reset at midnight broker/server time.")
                except Exception as e:
                    logger.error(f"Failed to reset daily counters: {e}")

    async def _run_cycle(self):
        """The main trading loop that runs periodically."""
        while self.is_running:
            try:
                # Only trade Monday to Friday (broker/server time)
                now = await self.mt5.get_server_time()
                if now.weekday() >= 5:  # 5=Saturday, 6=Sunday
                    logger.info("Weekend detected (broker/server time). AI trading paused.")
                    await asyncio.sleep(self.config.LOOP_INTERVAL_SECONDS)
                    continue
                logger.info("AI cycle starting...")
                if not self.mt5.connected:
                    logger.warning("MT5 not connected, skipping cycle.")
                    if not self.mt5_alert_sent:
                        await self.notifier.send_error_notification("MT5 is not connected. AI trading is paused.")
                        self.mt5_alert_sent = True
                    await asyncio.sleep(self.config.LOOP_INTERVAL_SECONDS)
                    continue
                # Reset alert flag if MT5 is now connected
                if self.mt5_alert_sent:
                    self.mt5_alert_sent = False
                for symbol in self.config.SYMBOLS:
                    await self._analyze_and_trade(symbol)
                logger.info(f"AI cycle finished. Waiting for {self.config.LOOP_INTERVAL_SECONDS} seconds.")
                await asyncio.sleep(self.config.LOOP_INTERVAL_SECONDS)
            except Exception as e:
                logger.error(f"An error occurred in the AI trading cycle: {e}", exc_info=True)
                await self.notifier.send_error_notification(f"AI cycle failed: {e}")
                await asyncio.sleep(60) # Wait longer after an error

    async def _analyze_and_trade(self, symbol: str):
        """Analyzes a single symbol and executes a trade if conditions are met."""
        logger.info(f"Analyzing {symbol}...")
        
        # 0. Coexistence & Safety Checks
        all_positions = await self.mt5.get_positions()
        if len(all_positions) >= self.config.MAX_TOTAL_OPEN_TRADES:
            logger.warning(f"Maximum total trades of {self.config.MAX_TOTAL_OPEN_TRADES} reached. AI is pausing.")
            return

        # Per-pair daily loss prevention
        balance_info = await self.mt5.get_balance()
        if not balance_info:
            logger.error("Could not fetch account balance. Cannot execute trade.")
            return
        balance = balance_info['balance']
        # Set per-pair daily loss threshold (e.g., 2% of balance)
        pair_loss_limit = balance * 0.02
        pair_loss = self.risk_manager.daily_pair_pnl.get(symbol, 0.0)
        if pair_loss < 0 and abs(pair_loss) >= pair_loss_limit:
            logger.warning(f"Daily loss limit reached for {symbol}: {pair_loss:.2f} >= {pair_loss_limit:.2f}. No more trades for this pair today.")
            return

        if self.config.AVOID_OPPOSING_MANUAL_TRADES:
            manual_positions_on_symbol = await self.mt5.get_positions(symbol=symbol, magic_number=self.config.MANUAL_MAGIC_NUMBER)
            if manual_positions_on_symbol:
                logger.info(f"Detected manual trade on {symbol}. AI will not trade this symbol to avoid conflict.")
                return

        # 1. Fetch Market Data
        df = await self.mt5.get_candles(symbol, self.config.TIMEFRAME, self.config.CANDLE_COUNT)
        if df is None or df.empty:
            logger.warning(f"Could not fetch data for {symbol}.")
            return

        # 2. Calculate Indicators
        df.ta.rsi(length=self.config.RSI_PERIOD, append=True)
        df.ta.macd(fast=self.config.MA_FAST_PERIOD, slow=self.config.MA_SLOW_PERIOD, signal=self.config.MACD_SIGNAL_PERIOD, append=True)
        
        # 3. Generate Signal (Simplified logic for now)
        # In a real scenario, this logic would be much more complex, using the AI Decision Matrix.
        last_candle = df.iloc[-1]
        signal = None
        if last_candle[f'RSI_{self.config.RSI_PERIOD}'] < 30 and last_candle[f'MACD_12_26_9'] > last_candle[f'MACDs_12_26_9']:
            signal = "BUY"
        elif last_candle[f'RSI_{self.config.RSI_PERIOD}'] > 70 and last_candle[f'MACD_12_26_9'] < last_candle[f'MACDs_12_26_9']:
            signal = "SELL"
        
        if not signal:
            logger.info(f"No clear signal for {symbol}.")
            return

        # 4. Execute Trade
        logger.info(f"Signal '{signal}' generated for {symbol}. Proceeding to execution.")
        
        balance_info = await self.mt5.get_balance()
        if not balance_info:
            logger.error("Could not fetch account balance. Cannot execute trade.")
            return

        position_size = await self.risk_manager.calculate_position_size(balance_info['balance'], symbol)
        if position_size <= 0:
            logger.warning(f"Position size is 0 for {symbol}. Skipping trade.")
            return

        sl_pips = self.config.get_stop_loss(symbol)
        tp_pips = self.config.get_take_profit(symbol)

        # 5. Handle Shadow Mode
        if self.config.SHADOW_MODE:
            logger.info(f"[SHADOW MODE] Would place {signal} order for {symbol} at {position_size} lots.")
            await self.notifier.send_shadow_trade_notification({
                "symbol": symbol, "type": signal, "lot_size": position_size
            })
            return # Do not proceed to actual trade placement

        # 6. Execute Live Trade
        result = await self.mt5.place_order(
            symbol=symbol,
            lot=position_size,
            order_type=signal.lower(),
            sl_pips=sl_pips,
            tp_pips=tp_pips,
            magic_number=self.config.AI_MAGIC_NUMBER
        )

        if result and result.get("success"):
            self.risk_manager.record_trade_opened(pair=symbol)
            trade_info = {
                "symbol": symbol,
                "type": signal,
                "balance": balance_info['balance'],
                "risk_amount": balance_info['balance'] * (self.config.RISK_PER_TRADE_PERCENT / 100),
                "profit_target": balance_info['balance'] * (self.config.RISK_PER_TRADE_PERCENT / 100) * self.config.RISK_REWARD_RATIO,
                "ticket": result.get("ticket")
            }
            await self.notifier.send_trade_opened_notification(trade_info)
        else:
            error_msg = result.get("error", "Unknown error")
            logger.error(f"Failed to place order for {symbol}: {error_msg}")
            await self.notifier.send_error_notification(f"Trade failed for {symbol}: {error_msg}") 