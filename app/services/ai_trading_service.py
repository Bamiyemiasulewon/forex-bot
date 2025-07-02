# forex-bot/app/services/ai_trading_service.py
import asyncio
import logging
import pandas as pd
import pandas_ta as ta
import datetime
from typing import Dict

from .ai_config import AIConfig
from .ai_risk_manager import AIRiskManager
from .mt5_service import MT5Service
from .telegram_notifier import AITelegramNotifier # We will create this next
from app.services.market_structure_strategy import market_structure_strategy
from app.services.signal_service import signal_service
from app.services.market_service import market_service

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
        
        # Initialize services
        self.signal_service = signal_service
        self.market_service = market_service

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
        """Main trading cycle that runs continuously."""
        while self.is_running:
            try:
                # Check if it's a trading day (Monday to Friday)
                now = await self.mt5.get_server_time()
                if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
                    logger.info("Weekend detected. AI trading paused.")
                    await asyncio.sleep(3600)  # Sleep for 1 hour
                    continue

                # Restrict trading to 7am-8pm only (server/broker time)
                if not (7 <= now.hour <= 20):
                    logger.info("Outside allowed trading hours (7:00-20:59). AI trading paused.")
                    await asyncio.sleep(600)  # Sleep for 10 minutes
                    continue

                # Check and close existing trades based on Market Structure signals
                await self._check_and_close_trades()

                # Get all available pairs
                pairs = self.risk_manager.get_all_pairs()
                
                # Filter pairs that haven't been traded today
                available_pairs = [pair for pair in pairs if self.risk_manager.can_trade_pair_today(pair)]
                
                if not available_pairs:
                    logger.info("All pairs have been traded today. Waiting for next trading day.")
                    await asyncio.sleep(300)  # Sleep for 5 minutes
                    continue

                # Check daily trade limit
                if self.risk_manager.daily_trade_count >= self.config.MAX_DAILY_TRADES:
                    logger.info(f"Daily trade limit of {self.config.MAX_DAILY_TRADES} reached. Waiting for next trading day.")
                    await asyncio.sleep(300)  # Sleep for 5 minutes
                    continue

                # Analyze and trade available pairs
                for symbol in available_pairs:
                    if not self.is_running:
                        break
                    
                    await self._analyze_and_trade(symbol)
                    await asyncio.sleep(30)  # Wait 30 seconds between pairs

                # Wait before next cycle
                await asyncio.sleep(60)  # 1 minute between cycles

            except Exception as e:
                logger.error(f"Error in AI trading cycle: {e}", exc_info=True)
                await asyncio.sleep(60)

    async def _analyze_and_trade(self, symbol: str):
        """Analyzes a single symbol and executes a trade if conditions are met, using the custom Market Structure strategy only."""
        logger.info(f"Analyzing {symbol} with Market Structure strategy...")
        now = datetime.datetime.now()
        # News event filter
        if self._is_major_news_event(symbol, now=now):
            logger.info(f"Major news event detected for {symbol}. Skipping trade.")
            return
        # Friday after 18:00 restriction
        if now.weekday() == 4 and now.hour >= 18:
            logger.info("Friday after 18:00. No trading allowed.")
            return
        # Trading hours restriction
        if not (7 <= now.hour <= 20):
            logger.info("Outside allowed trading hours (7:00-20:00). Skipping trade.")
            return
        # Spread/slippage/volatility checks (placeholders)
        spread = self._get_spread(symbol)
        if spread is not None and spread > 2.0:
            logger.info(f"Spread too wide for {symbol}: {spread} pips. Skipping trade.")
            return
        # Only one trade per pair per day
        if not self.risk_manager.can_trade_pair_today(symbol):
            logger.info(f"Pair {symbol} already traded today. Skipping.")
            return
        # Drawdown and consecutive loss checks
        if self.risk_manager.get_drawdown() > 0.05:
            logger.info("Account drawdown exceeds 5%. Skipping trade.")
            return
        if self.risk_manager.get_consecutive_losses() >= 2:
            logger.info("2 consecutive losses. Skipping trade for the day.")
            return
        # Per-pair daily loss prevention
        balance_info = await self.mt5.get_balance()
        if not balance_info:
            logger.warning("Could not fetch balance info for risk check.")
            return
        balance = balance_info.get('balance', 0)
        daily_pair_loss = self.risk_manager.daily_pair_pnl.get(symbol, 0)
        max_daily_loss_per_pair = balance * 0.02  # 2% of balance
        if daily_pair_loss < -max_daily_loss_per_pair:
            logger.warning(f"Daily loss limit reached for {symbol}. Skipping trade.")
            return
        # 1. Fetch Market Data for all required timeframes
        df_m15 = await self.signal_service.fetch_ohlcv(symbol, interval='15min', outputsize='compact')
        df_h1 = await self.signal_service.fetch_ohlcv(symbol, interval='60min', outputsize='compact')
        df_m5 = await self.signal_service.fetch_ohlcv(symbol, interval='5min', outputsize='compact')
        df_m1 = await self.signal_service.fetch_ohlcv(symbol, interval='1min', outputsize='compact')
        try:
            df_m3 = await self.signal_service.fetch_ohlcv(symbol, interval='3min', outputsize='compact')
        except Exception:
            df_m3 = None
        df_for_analysis = df_m1 if df_m1 is not None and len(df_m1) >= 50 else df_m15
        if df_for_analysis is None or len(df_for_analysis) < 50:
            logger.warning(f"Insufficient market data for {symbol}")
            return
        # 2. Market Structure Analysis (uses all timeframes internally)
        market_structure_signal = market_structure_strategy.analyze_pair(df_for_analysis, symbol)
        if not market_structure_signal:
            logger.info(f"No Market Structure signal for {symbol}")
            return
        signal_type = market_structure_signal.get('signal')
        if not signal_type:
            logger.warning(f"No valid signal type for {symbol}")
            return
        # 3. Risk Management Check
        if not self.risk_manager.can_trade():
            logger.warning(f"Risk management blocked trade for {symbol}")
            return
        # 4. Position Size Calculation
        entry_price = market_structure_signal.get('entry_price')
        stop_loss = market_structure_signal.get('stop_loss')
        if not entry_price or not stop_loss:
            logger.warning(f"Missing entry or stop loss price for {symbol}")
            return
        # Calculate position size based on risk
        risk_amount = balance * self.config.RISK_PER_TRADE
        pip_value = await self.market_service.get_pip_value_in_usd(symbol, 0.01)  # 0.01 lot
        stop_loss_pips = abs(entry_price - stop_loss) / 0.0001  # Convert to pips
        if pip_value <= 0 or stop_loss_pips <= 0:
            logger.warning(f"Invalid pip value or stop loss for {symbol}")
            return
        position_size = risk_amount / (pip_value * stop_loss_pips)
        position_size = min(position_size, self.config.MAX_POSITION_SIZE)
        position_size = max(position_size, self.config.MIN_POSITION_SIZE)
        # Final pre-trade checklist
        checklist = [
            (7 <= now.hour <= 20),
            self.risk_manager.can_trade_pair_today(symbol),
            market_structure_signal.get('trend') in ['bullish', 'bearish'],
            market_structure_signal.get('order_blocks_count', 0) > 0,
            market_structure_signal.get('inducement_detected'),
            position_size > 0,
            market_structure_signal.get('take_profit') is not None,
            not self._is_major_news_event(symbol, now=now),
            self.risk_manager.get_drawdown() <= 0.05,
            spread is None or spread <= 2.0
        ]
        if not all(checklist):
            logger.info(f"Final checklist failed for {symbol}. Skipping trade.")
            return
        # 5. Execute Trade
        try:
            order_type = "buy" if signal_type == "BUY" else "sell"
            take_profit = market_structure_signal.get('take_profit')
            sl_pips = abs(entry_price - stop_loss) / 0.0001
            tp_pips = abs(entry_price - take_profit) / 0.0001 if take_profit else None
            result = await self.mt5.place_order(
                symbol=symbol,
                order_type=order_type,
                lot=position_size,
                sl_pips=sl_pips,
                tp_pips=tp_pips
            )
            if result.get('success'):
                logger.info(f"Trade placed for {symbol}: {order_type} {position_size} lots at {entry_price}")
                await self._send_trade_notification(symbol, order_type, position_size, entry_price, stop_loss, take_profit, market_structure_signal)
                if hasattr(self, 'notifier') and self.notifier:
                    trade_info = {
                        'symbol': symbol,
                        'type': order_type,
                        'lot_size': position_size,
                        'entry_price': entry_price,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'risk_amount': risk_amount,
                        'balance': balance,
                        'profit_target': market_structure_signal.get('take_profit', 0)
                    }
                    await self.notifier.send_trade_opened_notification(trade_info)
            else:
                logger.error(f"Failed to place trade for {symbol}: {result}")
        except Exception as e:
            logger.error(f"Error placing trade for {symbol}: {e}")

    def _get_spread(self, symbol):
        """Placeholder: Returns the current spread in pips for the symbol. Replace with real implementation."""
        return 1.5  # Example: always 1.5 pips

    async def _check_and_close_trades(self):
        """Check existing trades and close them based on Market Structure strategy signals."""
        try:
            positions = await self.mt5.get_positions()
            if not positions:
                return

            for position in positions:
                symbol = position.get('symbol')
                if not symbol:
                    continue

                # Fetch current market data
                df = await self.signal_service.fetch_ohlcv(symbol, interval='15min', outputsize='compact')
                if df is None or len(df) < 50:
                    continue

                # Get current Market Structure signal
                current_signal = market_structure_strategy.analyze_pair(df, symbol)
                if not current_signal:
                    continue

                current_signal_type = current_signal.get('signal')
                position_type = position.get('type', '').lower()

                # Check if we should close the position based on signal reversal
                should_close = False
                close_reason = ""

                if position_type == 'buy' and current_signal_type == 'SELL':
                    should_close = True
                    close_reason = "Market Structure signal reversal to SELL"
                elif position_type == 'sell' and current_signal_type == 'BUY':
                    should_close = True
                    close_reason = "Market Structure signal reversal to BUY"

                # Additional close conditions based on Market Structure
                if current_signal.get('trend') == 'ranging':
                    # Close if market structure shows ranging (no clear trend)
                    should_close = True
                    close_reason = "Market structure shows ranging conditions"

                if should_close:
                    ticket = position.get('ticket')
                    if ticket:
                        close_result = await self.mt5.close_position(ticket)
                        if close_result.get('success'):
                            logger.info(f"✅ AI closed {symbol} position: {close_reason}")
                            await self._send_close_notification(symbol, close_reason, position)
                        else:
                            logger.error(f"❌ Failed to close {symbol} position: {close_result}")

        except Exception as e:
            logger.error(f"Error in trade close check: {e}", exc_info=True)

    async def _send_close_notification(self, symbol: str, reason: str, position: Dict):
        """Send notification when AI closes a trade."""
        try:
            message = f"🤖 **AI Trade Closed**\n"
            message += f"📊 **Symbol:** {symbol}\n"
            message += f"📝 **Reason:** {reason}\n"
            message += f"💰 **Profit/Loss:** {position.get('profit', 'N/A')}\n"
            message += f"📅 **Time:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Send to Telegram if notifier is available
            if hasattr(self, 'notifier') and self.notifier:
                await self.notifier.send_message(message)
        except Exception as e:
            logger.error(f"Error sending close notification: {e}")

    async def _send_trade_notification(self, symbol: str, order_type: str, position_size: float, entry_price: float, stop_loss: float, take_profit: float, market_structure_signal: Dict):
        """Send notification when AI places a trade."""
        try:
            message = f"🤖 **AI Trade Placed**\n"
            message += f"📊 **Symbol:** {symbol}\n"
            message += f"📝 **Order Type:** {order_type.upper()}\n"
            message += f"💰 **Position Size:** {position_size}\n"
            message += f"📅 **Entry Price:** {entry_price}\n"
            message += f"📅 **Stop Loss:** {stop_loss}\n"
            message += f"📅 **Take Profit:** {take_profit}\n"
            message += f"📊 **Market Structure Signal:** {market_structure_signal}"
            
            # Send to Telegram if notifier is available
            if hasattr(self, 'notifier') and self.notifier:
                await self.notifier.send_message(message)
        except Exception as e:
            logger.error(f"Error sending trade notification: {e}")

    def reset_user_history(self, user_id=None):
        """Reset all AI trade/PNL state for a new account login."""
        self.risk_manager.reset_all_state()
        logger.info("AITradingService: User/AI history reset due to new account login.")

    def _is_major_news_event(self, symbol, now=None):
        """Placeholder: Returns True if a major news event is within 30 minutes before/after now."""
        # TODO: Integrate with real economic calendar/news API
        # For now, always return False (no news event)
        return False

    def _get_spread(self, symbol):
        """Placeholder: Returns the current spread in pips for the symbol. Replace with real implementation."""
        return 1.5  # Example: always 1.5 pips 