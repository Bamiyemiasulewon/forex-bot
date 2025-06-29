import pandas as pd
import numpy as np
import logging
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple, List
from app.utils.indicators import (
    calculate_rsi, calculate_fibonacci_levels, detect_break_of_structure,
    find_order_block, calculate_atr, is_at_fibonacci_level
)

logger = logging.getLogger(__name__)

class OrderBlockRSIFibStrategy:
    """
    Order Block + RSI + Fibonacci Strategy Implementation
    
    Strategy Conditions:
    - Break of structure (BOS)
    - Order Block identification
    - Fibonacci retracement alignment (38.2%, 50%, 61.8%)
    - RSI confirmation (oversold < 30, overbought > 70)
    - Risk management: 10% per trade, max 3 trades per day, 10% daily loss limit
    """
    
    def __init__(self):
        # Strategy parameters
        self.rsi_period = 14
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        self.fib_levels = [0.382, 0.5, 0.618]
        self.lookback_period = 20
        self.atr_period = 14
        
        # Risk management parameters
        self.risk_per_trade = 0.10  # 10%
        self.max_trades_per_day = 3
        self.max_daily_loss = 0.10  # 10%
        self.stop_trading_on_drawdown = True
        
        # Trading session times (GMT)
        self.london_session = {
            'start': 7,  # 7 AM GMT
            'end': 11    # 11 AM GMT
        }
        self.ny_session = {
            'start': 12,  # 12 PM GMT
            'end': 16     # 4 PM GMT
        }
        
        # Daily tracking
        self.daily_trades = 0
        self.daily_pnl = 0.0
        self.last_reset_date = None
        
    def reset_daily_counters(self):
        """Reset daily trade counters if it's a new day."""
        current_date = datetime.now(timezone.utc).date()
        if self.last_reset_date != current_date:
            self.daily_trades = 0
            self.daily_pnl = 0.0
            self.last_reset_date = current_date
            logger.info("Daily counters reset for new trading day")
    
    def is_trading_session(self) -> bool:
        """
        Check if current time is within London or New York trading sessions.
        
        Returns:
            True if within trading session, False otherwise
        """
        current_hour = datetime.now(timezone.utc).hour
        
        # London session: 7 AM - 11 AM GMT
        london_active = self.london_session['start'] <= current_hour < self.london_session['end']
        
        # New York session: 12 PM - 4 PM GMT
        ny_active = self.ny_session['start'] <= current_hour < self.ny_session['end']
        
        return london_active or ny_active
    
    def can_trade(self, account_balance: float, current_pnl: float = 0.0) -> Tuple[bool, str]:
        """
        Check if trading is allowed based on risk management rules.
        
        Args:
            account_balance: Current account balance
            current_pnl: Current day's P&L
            
        Returns:
            Tuple of (can_trade, reason)
        """
        self.reset_daily_counters()
        
        # Check daily trade limit
        if self.daily_trades >= self.max_trades_per_day:
            return False, f"Daily trade limit reached ({self.max_trades_per_day})"
        
        # Check daily loss limit
        daily_loss_percent = abs(current_pnl) / account_balance if account_balance > 0 else 0
        if daily_loss_percent >= self.max_daily_loss:
            return False, f"Daily loss limit reached ({daily_loss_percent:.2%})"
        
        # Check trading session
        if not self.is_trading_session():
            return False, "Outside trading session (London: 7-11 AM GMT, NY: 12-4 PM GMT)"
        
        return True, "Trading allowed"
    
    def analyze_buy_setup(self, df: pd.DataFrame) -> Optional[Dict]:
        """
        Analyze for buy setup conditions.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Signal dictionary if conditions met, None otherwise
        """
        if len(df) < 50:
            return None
        
        # 1. Check for break of structure to the upside
        bos_up, bos_idx = detect_break_of_structure(df, 'up', self.lookback_period)
        if not bos_up:
            return None
        
        # 2. Find bullish order block (last bearish candle before bullish move)
        ob_idx, ob_zone = find_order_block(df.iloc[:bos_idx+1], 'bullish', self.lookback_period)
        if ob_zone is None:
            return None
        
        # 3. Calculate Fibonacci levels from swing low to high
        swing_low = df['low'].iloc[-30:-10].min()
        swing_high = df['high'].iloc[-30:-10].max()
        fib_levels = calculate_fibonacci_levels(swing_low, swing_high)
        
        # 4. Check if OB aligns with Fibonacci levels
        ob_aligned = False
        aligned_level = None
        aligned_price = None
        
        for level in self.fib_levels:
            if level in fib_levels:
                fib_price = fib_levels[level]
                if ob_zone['low'] <= fib_price <= ob_zone['high']:
                    ob_aligned = True
                    aligned_level = level
                    aligned_price = fib_price
                    break
        
        if not ob_aligned:
            return None
        
        # 5. Check RSI oversold condition
        rsi = calculate_rsi(df['close'], self.rsi_period)
        if rsi.iloc[-1] >= self.rsi_oversold:
            return None
        
        # 6. Calculate entry, stop loss, and take profit
        current_price = df['close'].iloc[-1]
        atr = calculate_atr(df, self.atr_period).iloc[-1]
        
        # Entry at OB zone (use aligned Fibonacci level)
        entry_price = aligned_price
        
        # Stop loss just beyond the order block
        stop_loss = ob_zone['low'] - (atr * 0.5)
        
        # Take profit at 1:2 risk-reward ratio
        risk = entry_price - stop_loss
        take_profit = entry_price + (risk * 2)
        
        return {
            'signal': 'buy',
            'confidence': 90,
            'strategy': 'Order Block + RSI + Fibonacci',
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'risk_reward_ratio': '1:2',
            'order_block': ob_zone,
            'fibonacci_level': aligned_level,
            'rsi_value': rsi.iloc[-1],
            'break_of_structure': True,
            'reasoning': f"BOS up, OB at {aligned_level:.1%} Fib, RSI oversold ({rsi.iloc[-1]:.1f})"
        }
    
    def analyze_sell_setup(self, df: pd.DataFrame) -> Optional[Dict]:
        """
        Analyze for sell setup conditions.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Signal dictionary if conditions met, None otherwise
        """
        if len(df) < 50:
            return None
        
        # 1. Check for break of structure to the downside
        bos_down, bos_idx = detect_break_of_structure(df, 'down', self.lookback_period)
        if not bos_down:
            return None
        
        # 2. Find bearish order block (last bullish candle before bearish move)
        ob_idx, ob_zone = find_order_block(df.iloc[:bos_idx+1], 'bearish', self.lookback_period)
        if ob_zone is None:
            return None
        
        # 3. Calculate Fibonacci levels from swing high to low
        swing_high = df['high'].iloc[-30:-10].max()
        swing_low = df['low'].iloc[-30:-10].min()
        fib_levels = calculate_fibonacci_levels(swing_low, swing_high)
        
        # 4. Check if OB aligns with Fibonacci levels
        ob_aligned = False
        aligned_level = None
        aligned_price = None
        
        for level in self.fib_levels:
            if level in fib_levels:
                fib_price = fib_levels[level]
                if ob_zone['low'] <= fib_price <= ob_zone['high']:
                    ob_aligned = True
                    aligned_level = level
                    aligned_price = fib_price
                    break
        
        if not ob_aligned:
            return None
        
        # 5. Check RSI overbought condition
        rsi = calculate_rsi(df['close'], self.rsi_period)
        if rsi.iloc[-1] <= self.rsi_overbought:
            return None
        
        # 6. Calculate entry, stop loss, and take profit
        current_price = df['close'].iloc[-1]
        atr = calculate_atr(df, self.atr_period).iloc[-1]
        
        # Entry at OB zone (use aligned Fibonacci level)
        entry_price = aligned_price
        
        # Stop loss just beyond the order block
        stop_loss = ob_zone['high'] + (atr * 0.5)
        
        # Take profit at 1:2 risk-reward ratio
        risk = stop_loss - entry_price
        take_profit = entry_price - (risk * 2)
        
        return {
            'signal': 'sell',
            'confidence': 90,
            'strategy': 'Order Block + RSI + Fibonacci',
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'risk_reward_ratio': '1:2',
            'order_block': ob_zone,
            'fibonacci_level': aligned_level,
            'rsi_value': rsi.iloc[-1],
            'break_of_structure': True,
            'reasoning': f"BOS down, OB at {aligned_level:.1%} Fib, RSI overbought ({rsi.iloc[-1]:.1f})"
        }
    
    def analyze_pair(self, df: pd.DataFrame) -> Optional[Dict]:
        """
        Analyze a pair for both buy and sell setups.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Signal dictionary if conditions met, None otherwise
        """
        # Try buy setup first
        buy_signal = self.analyze_buy_setup(df)
        if buy_signal:
            return buy_signal
        
        # Try sell setup
        sell_signal = self.analyze_sell_setup(df)
        if sell_signal:
            return sell_signal
        
        return None
    
    def update_daily_stats(self, trade_result: float):
        """
        Update daily trading statistics.
        
        Args:
            trade_result: P&L from the trade
        """
        self.daily_trades += 1
        self.daily_pnl += trade_result
        logger.info(f"Daily stats updated: trades={self.daily_trades}, pnl={self.daily_pnl:.2f}")
    
    def get_strategy_info(self) -> Dict:
        """
        Get strategy information and current status.
        
        Returns:
            Dictionary with strategy information
        """
        return {
            'strategy_name': 'Order Block + RSI + Fibonacci',
            'timeframe': 'M5',
            'risk_per_trade': f"{self.risk_per_trade:.1%}",
            'max_trades_per_day': self.max_trades_per_day,
            'max_daily_loss': f"{self.max_daily_loss:.1%}",
            'trading_sessions': {
                'london': f"{self.london_session['start']:02d}:00-{self.london_session['end']:02d}:00 GMT",
                'new_york': f"{self.ny_session['start']:02d}:00-{self.ny_session['end']:02d}:00 GMT"
            },
            'daily_trades': self.daily_trades,
            'daily_pnl': self.daily_pnl,
            'in_session': self.is_trading_session()
        }

# Singleton instance
order_block_strategy = OrderBlockRSIFibStrategy() 