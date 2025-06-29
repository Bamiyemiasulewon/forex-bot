import pandas as pd
import numpy as np

# Calculate the Relative Strength Index (RSI) for a price series.
def calculate_rsi(series: pd.Series, period: int = 14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(0)

# Calculate the Moving Average Convergence Divergence (MACD) and its signal line for a price series.
def calculate_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    exp1 = series.ewm(span=fast, adjust=False).mean()
    exp2 = series.ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    return macd, signal_line

# Calculate Fibonacci retracement levels
def calculate_fibonacci_levels(swing_low: float, swing_high: float) -> dict:
    """
    Calculate Fibonacci retracement levels between swing low and swing high.
    
    Args:
        swing_low: The swing low price
        swing_high: The swing high price
        
    Returns:
        Dictionary with Fibonacci levels (0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0)
    """
    price_range = swing_high - swing_low
    levels = {
        0.0: swing_low,
        0.236: swing_low + 0.236 * price_range,
        0.382: swing_low + 0.382 * price_range,
        0.5: swing_low + 0.5 * price_range,
        0.618: swing_low + 0.618 * price_range,
        0.786: swing_low + 0.786 * price_range,
        1.0: swing_high
    }
    return levels

# Detect swing highs and lows
def detect_swing_points(df: pd.DataFrame, window: int = 10) -> tuple:
    """
    Detect swing highs and lows in the price data.
    
    Args:
        df: DataFrame with OHLC data
        window: Window size for swing detection
        
    Returns:
        Tuple of (swing_highs, swing_lows) as pandas Series
    """
    swing_highs = df['high'].rolling(window=window, center=True).max()
    swing_lows = df['low'].rolling(window=window, center=True).min()
    
    # Identify actual swing points
    swing_high_mask = (df['high'] == swing_highs) & (df['high'] > df['high'].shift(1)) & (df['high'] > df['high'].shift(-1))
    swing_low_mask = (df['low'] == swing_lows) & (df['low'] < df['low'].shift(1)) & (df['low'] < df['low'].shift(-1))
    
    return swing_high_mask, swing_low_mask

# Detect break of structure
def detect_break_of_structure(df: pd.DataFrame, direction: str = 'up', lookback: int = 20) -> tuple:
    """
    Detect a break of structure in the given direction.
    
    Args:
        df: DataFrame with OHLC data
        direction: 'up' or 'down'
        lookback: Number of bars to look back for swing high/low
        
    Returns:
        Tuple of (break_detected, break_index)
    """
    if direction == 'up':
        # Look for close above previous swing high
        swing_high = df['high'].rolling(lookback).max().shift(1)
        bos = (df['close'] > swing_high) & (df['close'] > df['open'])  # Bullish candle
    else:
        # Look for close below previous swing low
        swing_low = df['low'].rolling(lookback).min().shift(1)
        bos = (df['close'] < swing_low) & (df['close'] < df['open'])  # Bearish candle
    
    if bos.iloc[-1]:
        return True, bos.index[-1]
    return False, None

# Find order blocks
def find_order_block(df: pd.DataFrame, direction: str = 'bullish', lookback: int = 20) -> tuple:
    """
    Find the last order block before the break of structure.
    
    Args:
        df: DataFrame with OHLC data
        direction: 'bullish' or 'bearish'
        lookback: Number of bars to look back
        
    Returns:
        Tuple of (order_block_index, order_block_zone)
    """
    if direction == 'bullish':
        # Last bearish candle before the up move
        mask = (df['close'] < df['open']) & (df['volume'] > df['volume'].rolling(10).mean())
    else:
        # Last bullish candle before the down move
        mask = (df['close'] > df['open']) & (df['volume'] > df['volume'].rolling(10).mean())
    
    # Look for order blocks in the recent data
    recent_data = df.iloc[-lookback:]
    mask_aligned = mask.iloc[-lookback:]
    ob_candidates = recent_data[mask_aligned]
    
    if len(ob_candidates) > 0:
        # Get the most recent order block
        ob_idx = ob_candidates.index[-1]
        ob_row = df.loc[ob_idx]
        
        ob_zone = {
            'index': ob_idx,
            'open': ob_row['open'],
            'close': ob_row['close'],
            'high': ob_row['high'],
            'low': ob_row['low'],
            'volume': ob_row['volume']
        }
        
        return ob_idx, ob_zone
    
    return None, None

# Calculate Average True Range (ATR)
def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Average True Range for volatility measurement.
    
    Args:
        df: DataFrame with OHLC data
        period: Period for ATR calculation
        
    Returns:
        ATR values as pandas Series
    """
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = true_range.rolling(window=period).mean()
    
    return atr

# Check if price is at Fibonacci level
def is_at_fibonacci_level(price: float, fib_levels: dict, tolerance: float = 0.001) -> tuple:
    """
    Check if a price is at or near a Fibonacci retracement level.
    
    Args:
        price: Current price
        fib_levels: Dictionary of Fibonacci levels
        tolerance: Tolerance for level detection (as percentage)
        
    Returns:
        Tuple of (is_at_level, level_name, level_price)
    """
    for level_name, level_price in fib_levels.items():
        if level_name in [0.382, 0.5, 0.618]:  # Only check key levels
            tolerance_pips = level_price * tolerance
            if abs(price - level_price) <= tolerance_pips:
                return True, f"{level_name:.1%}", level_price
    
    return False, None, None 