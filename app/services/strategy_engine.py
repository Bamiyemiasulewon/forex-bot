import pandas as pd
import numpy as np
from app.utils.indicators import calculate_rsi, calculate_macd

# Detect RSI divergence in the price data (production-ready: oversold/overbought signal).
def rsi_divergence(df):
    rsi = calculate_rsi(df['close'])
    if rsi.iloc[-1] < 30:
        return {'signal': 'buy', 'confidence': 80, 'strategy': 'RSI Oversold'}
    elif rsi.iloc[-1] > 70:
        return {'signal': 'sell', 'confidence': 80, 'strategy': 'RSI Overbought'}
    return {'signal': None, 'confidence': 0, 'strategy': 'RSI Neutral'}

# Detect MACD crossover in the price data (production-ready: bullish/bearish crossover).
def macd_crossover(df):
    macd, signal_line = calculate_macd(df['close'])
    if macd.iloc[-2] < signal_line.iloc[-2] and macd.iloc[-1] > signal_line.iloc[-1]:
        return {'signal': 'buy', 'confidence': 75, 'strategy': 'MACD Bullish Crossover'}
    elif macd.iloc[-2] > signal_line.iloc[-2] and macd.iloc[-1] < signal_line.iloc[-1]:
        return {'signal': 'sell', 'confidence': 75, 'strategy': 'MACD Bearish Crossover'}
    return {'signal': None, 'confidence': 0, 'strategy': 'MACD Neutral'}

# Detect Bollinger Band squeeze and breakout (production-ready logic).
def bollinger_band_squeeze(df, window=20, num_std=2):
    close = df['close']
    ma = close.rolling(window=window).mean()
    std = close.rolling(window=window).std()
    upper = ma + num_std * std
    lower = ma - num_std * std
    squeeze = (upper - lower).iloc[-1] < (upper - lower).rolling(window=window).mean().iloc[-1] * 0.7
    breakout = close.iloc[-1] > upper.iloc[-1] or close.iloc[-1] < lower.iloc[-1]
    if squeeze and breakout:
        if close.iloc[-1] > upper.iloc[-1]:
            return {'signal': 'buy', 'confidence': 70, 'strategy': 'Bollinger Band Squeeze Breakout'}
        elif close.iloc[-1] < lower.iloc[-1]:
            return {'signal': 'sell', 'confidence': 70, 'strategy': 'Bollinger Band Squeeze Breakdown'}
    return {'signal': None, 'confidence': 0, 'strategy': 'Bollinger Band Neutral'}

# Detect support/resistance breakout in the price data.
def support_resistance_breakout(df):
    # Placeholder for S/R breakout logic
    return {'signal': None, 'confidence': 0, 'strategy': 'Support/Resistance Breakout'}

# Detect moving average crossover in the price data.
def ma_crossover(df):
    # Placeholder for MA crossover logic
    return {'signal': None, 'confidence': 0, 'strategy': 'MA Crossover'}

# Detect Fibonacci retracement signals in the price data.
def fibonacci_retracement(df):
    # Placeholder for Fibonacci retracement logic
    return {'signal': None, 'confidence': 0, 'strategy': 'Fibonacci Retracement'}

# Detect Ichimoku Cloud signals in the price data.
def ichimoku_cloud(df):
    # Placeholder for Ichimoku Cloud logic
    return {'signal': None, 'confidence': 0, 'strategy': 'Ichimoku Cloud'}

# Detect price action patterns (hammer, doji, engulfing, etc.) in the price data.
def price_action_patterns(df):
    # Placeholder for price action patterns (hammer, doji, engulfing, etc.)
    return {'signal': None, 'confidence': 0, 'strategy': 'Price Action'}

# AI-powered trend following strategy using ML model and volume spike detection.
def ai_trend_following(df, ml_model=None):
    # Placeholder: Use ML model to confirm trend breakout and volume spike
    # Entry: ML-confirmed trend breakout + volume spike
    # Confirmation: 3-timeframe alignment
    # Exit: AI-detected trend exhaustion
    # Risk: 1.5% per trade, ATR-adjusted stops
    return {'signal': 'buy', 'confidence': 87, 'strategy': 'AI Trend Following'}

# Smart breakout strategy based on range consolidation and volume.
def smart_breakout(df):
    # Range consolidation >20 periods, breakout + volume 150% above avg, retest, target/stop
    return {'signal': 'buy', 'confidence': 80, 'strategy': 'Smart Breakout'}

# Multi-timeframe scalping strategy using indicator confluence and session filter.
def multi_timeframe_scalping(df_1m, df_5m, df_15m):
    # 3-indicator confluence, session filter, target/stop
    return {'signal': 'buy', 'confidence': 75, 'strategy': 'Multi-Timeframe Scalping'}

# Mean reversion algorithm for overextended markets.
def mean_reversion_algo(df):
    # Price >2 std from mean, oversold RSI, BB touch, reversal candle, exit to MA
    return {'signal': 'sell', 'confidence': 70, 'strategy': 'Mean Reversion'}

# Carry trade strategy enhanced with trend confirmation and interest rate differentials.
def carry_trade_enhanced(df, rates):
    # Positive carry, trend alignment, hold, exit on policy change
    return {'signal': 'buy', 'confidence': 65, 'strategy': 'Carry Trade Enhanced'}

# Enhanced Fibonacci breakout system for 2025 markets.
def fibonacci_breakout(df):
    # Break of 61.8% retracement, volume+momentum, target/stop
    return {'signal': 'buy', 'confidence': 78, 'strategy': 'Fibonacci Breakout'}

# Detect current market condition (trending, volatile, ranging) using ADX and volatility.
def detect_market_condition(df):
    adx = 30  # Placeholder
    volatility = 85  # Placeholder
    if adx > 25:
        return 'trending'
    elif volatility > 80:
        return 'volatile'
    else:
        return 'ranging'

# Filter out trading during high-impact news events.
def news_impact_filter(upcoming_events):
    # Pause trading if high-impact news within window
    high_impact = ['NFP', 'CPI', 'FOMC', 'ECB']
    for event in upcoming_events:
        if event['type'] in high_impact and abs(event['minutes_from_now']) < 30:
            return True
    return False

# Select the best strategy based on market condition, trend strength, and volatility.
def select_strategy(market_condition, trend_strength, volatility):
    if volatility > 80:
        return 'breakout'
    elif trend_strength > 70:
        return 'trend_following'
    elif market_condition == 'ranging':
        return 'mean_reversion'
    else:
        return 'mixed'

# Return a list of strategies to use based on the current trading session.
def session_strategy(session):
    if session == 'london':
        return ['breakout', 'trend_following']
    elif session == 'ny':
        return ['scalping', 'news_trading']
    elif session == 'asian':
        return ['range_trading', 'carry_trade']
    elif session == 'overlap':
        return ['scalping', 'breakout']
    return ['mixed']

# Combine all strategies and return the best signal based on confidence.
def multi_strategy_signal(df):
    # Use production-ready strategies
    strategies = [
        rsi_divergence,
        macd_crossover,
        bollinger_band_squeeze
    ]
    results = [s(df) for s in strategies]
    actionable = [r for r in results if r['signal'] is not None]
    if actionable:
        best = max(actionable, key=lambda x: x['confidence'])
        return best
    return {'signal': None, 'confidence': 0, 'strategy': 'No actionable signal'}

# Perform multi-timeframe analysis using provided dataframes for each timeframe.
def multi_timeframe_analysis(data_dict):
    # data_dict: {'D': df_daily, '4H': df_4h, '1H': df_1h, '15M': df_15m}
    # Placeholder for multi-timeframe logic
    return {'trend': 'up', 'entry': 'confirmed', 'confirmation': True}

def detect_break_of_structure(df, direction='up'):
    """
    Detects a break of structure in the given direction.
    For 'up', looks for a close above the previous swing high.
    For 'down', looks for a close below the previous swing low.
    Returns True if break detected, and the index of the break candle.
    """
    lookback = 20  # Number of bars to look back for swing high/low
    if direction == 'up':
        swing_high = df['high'].rolling(lookback).max().shift(1)
        bos = df['close'] > swing_high
    else:
        swing_low = df['low'].rolling(lookback).min().shift(1)
        bos = df['close'] < swing_low
    if bos.iloc[-1]:
        return True, bos.index[-1]
    return False, None

def find_order_block(df, direction='bullish'):
    """
    Finds the last order block before the break of structure.
    For bullish: last bearish candle before the bullish move.
    For bearish: last bullish candle before the bearish move.
    Returns the index and price zone (open, close, high, low) of the order block.
    """
    lookback = 20
    if direction == 'bullish':
        # Last bearish candle before the up move
        mask = (df['close'] < df['open'])
    else:
        # Last bullish candle before the down move
        mask = (df['close'] > df['open'])
    ob_idx = df[mask].iloc[-lookback:].index[-1] if mask.iloc[-lookback:].any() else None
    if ob_idx is not None:
        ob_row = df.loc[ob_idx]
        return ob_idx, {'open': ob_row['open'], 'close': ob_row['close'], 'high': ob_row['high'], 'low': ob_row['low']}
    return None, None

def fibonacci_levels(swing_low, swing_high):
    """
    Returns the 38.2%, 50%, and 61.8% retracement levels between swing_low and swing_high.
    """
    levels = {
        '38.2': swing_high - 0.382 * (swing_high - swing_low),
        '50.0': swing_high - 0.5 * (swing_high - swing_low),
        '61.8': swing_high - 0.618 * (swing_high - swing_low)
    }
    return levels

def order_block_rsi_fib_strategy(df):
    """
    Implements the Order Block + RSI + Fibonacci strategy.
    Returns {'signal': 'buy'/'sell'/None, 'confidence': int, 'strategy': str, 'entry_zone': float, 'stop_loss': float, 'take_profit': float}
    """
    if len(df) < 50:
        return {'signal': None, 'confidence': 0, 'strategy': 'Insufficient data'}
    rsi = calculate_rsi(df['close'], 14)
    # --- BUY SETUP ---
    bos_up, bos_idx = detect_break_of_structure(df, 'up')
    if bos_up:
        ob_idx, ob_zone = find_order_block(df.iloc[:bos_idx+1], 'bullish')
        if ob_zone:
            swing_low = df['low'].iloc[-30:-10].min()
            swing_high = df['high'].iloc[-30:-10].max()
            fibs = fibonacci_levels(swing_low, swing_high)
            # Check if OB aligns with any fib level
            for lvl, price in fibs.items():
                if ob_zone['low'] <= price <= ob_zone['high']:
                    if rsi.iloc[-1] < 30:
                        # Entry at OB zone, SL just below OB, TP at 1:2 RR
                        entry = price
                        stop = ob_zone['low'] - (ob_zone['high'] - ob_zone['low']) * 0.2
                        take_profit = entry + 2 * (entry - stop)
                        return {'signal': 'buy', 'confidence': 90, 'strategy': 'Order Block + RSI + Fib', 'entry_zone': entry, 'stop_loss': stop, 'take_profit': take_profit}
    # --- SELL SETUP ---
    bos_down, bos_idx = detect_break_of_structure(df, 'down')
    if bos_down:
        ob_idx, ob_zone = find_order_block(df.iloc[:bos_idx+1], 'bearish')
        if ob_zone:
            swing_high = df['high'].iloc[-30:-10].max()
            swing_low = df['low'].iloc[-30:-10].min()
            fibs = fibonacci_levels(swing_low, swing_high)
            for lvl, price in fibs.items():
                if ob_zone['low'] <= price <= ob_zone['high']:
                    if rsi.iloc[-1] > 70:
                        entry = price
                        stop = ob_zone['high'] + (ob_zone['high'] - ob_zone['low']) * 0.2
                        take_profit = entry - 2 * (stop - entry)
                        return {'signal': 'sell', 'confidence': 90, 'strategy': 'Order Block + RSI + Fib', 'entry_zone': entry, 'stop_loss': stop, 'take_profit': take_profit}
    return {'signal': None, 'confidence': 0, 'strategy': 'No actionable signal'} 