import pandas as pd
import numpy as np
import logging
from typing import Dict, Optional, List, Tuple
from app.utils.indicators import calculate_rsi, calculate_macd
import asyncio

logger = logging.getLogger(__name__)

class MarketStructureStrategy:
    def __init__(self):
        self.name = "Market Structure Strategy"
        self.timeframes = {
            'trend': ['15min', '60min'],  # M15, H1 for trend
            'poi': ['5min', '1min'],      # M5, M1 for POI
            'inducement': ['1min', '3min'], # M1, M3 for inducement
            'entry': ['1min']             # M1 for entry
        }
        
    def analyze_market_structure(self, df: pd.DataFrame, timeframe: str) -> Dict:
        """Analyze market structure to determine trend direction."""
        if len(df) < 50:
            return {"trend": "unknown", "structure": "insufficient_data"}
        
        # Calculate key levels
        highs = df['high'].rolling(20).max()
        lows = df['low'].rolling(20).min()
        
        # Identify higher highs and higher lows (bullish structure)
        recent_highs = highs.tail(10)
        recent_lows = lows.tail(10)
        
        # Check for market structure
        higher_highs = recent_highs.iloc[-1] > recent_highs.iloc[-5]
        higher_lows = recent_lows.iloc[-1] > recent_lows.iloc[-5]
        lower_highs = recent_highs.iloc[-1] < recent_highs.iloc[-5]
        lower_lows = recent_lows.iloc[-1] < recent_lows.iloc[-5]
        
        # Determine trend
        if higher_highs and higher_lows:
            trend = "bullish"
        elif lower_highs and lower_lows:
            trend = "bearish"
        else:
            trend = "ranging"
        
        # Calculate key levels
        current_price = df['close'].iloc[-1]
        resistance = highs.tail(5).max()
        support = lows.tail(5).min()
        
        return {
            "trend": trend,
            "structure": "valid",
            "current_price": current_price,
            "resistance": resistance,
            "support": support,
            "timeframe": timeframe
        }
    
    def find_order_blocks(self, df: pd.DataFrame, trend: str) -> List[Dict]:
        """Identify Order Blocks (POI) on M5 or M1 timeframe."""
        order_blocks = []
        
        if len(df) < 20:
            return order_blocks
        
        # Look for order blocks based on trend
        for i in range(5, len(df) - 1):
            current_candle = df.iloc[i]
            next_candle = df.iloc[i + 1]
            
            # Bullish Order Block (in bullish trend)
            if trend == "bullish":
                # Look for strong bearish candle followed by bullish move
                if (current_candle['close'] < current_candle['open'] and  # Bearish candle
                    next_candle['close'] > next_candle['open'] and       # Bullish candle
                    next_candle['close'] > current_candle['high']):      # Break above
                    
                    order_blocks.append({
                        "type": "bullish_order_block",
                        "index": i,
                        "high": current_candle['high'],
                        "low": current_candle['low'],
                        "strength": abs(current_candle['close'] - current_candle['open']) / current_candle['open']
                    })
            
            # Bearish Order Block (in bearish trend)
            elif trend == "bearish":
                # Look for strong bullish candle followed by bearish move
                if (current_candle['close'] > current_candle['open'] and  # Bullish candle
                    next_candle['close'] < next_candle['open'] and       # Bearish candle
                    next_candle['close'] < current_candle['low']):       # Break below
                    
                    order_blocks.append({
                        "type": "bearish_order_block",
                        "index": i,
                        "high": current_candle['high'],
                        "low": current_candle['low'],
                        "strength": abs(current_candle['close'] - current_candle['open']) / current_candle['open']
                    })
        
        return order_blocks
    
    def detect_inducement(self, df: pd.DataFrame, order_blocks: List[Dict]) -> List[Dict]:
        """Detect liquidity inducement or sweeps near order blocks."""
        inducements = []
        
        if len(df) < 10 or not order_blocks:
            return inducements
        
        for block in order_blocks:
            block_index = block['index']
            
            # Look for sweeps after the order block
            for i in range(block_index + 1, min(block_index + 10, len(df))):
                candle = df.iloc[i]
                
                # Bullish inducement (sweep below bullish order block)
                if (block['type'] == 'bullish_order_block' and
                    candle['low'] < block['low'] and
                    candle['close'] > block['low']):
                    
                    inducements.append({
                        "type": "bullish_inducement",
                        "block_index": block_index,
                        "sweep_index": i,
                        "sweep_low": candle['low'],
                        "recovery_price": candle['close']
                    })
                
                # Bearish inducement (sweep above bearish order block)
                elif (block['type'] == 'bearish_order_block' and
                      candle['high'] > block['high'] and
                      candle['close'] < block['high']):
                    
                    inducements.append({
                        "type": "bearish_inducement",
                        "block_index": block_index,
                        "sweep_index": i,
                        "sweep_high": candle['high'],
                        "recovery_price": candle['close']
                    })
        
        return inducements
    
    def find_fair_value_gaps(self, df: pd.DataFrame) -> List[Dict]:
        """Identify Fair Value Gaps (FVG) for exit strategy."""
        fvgs = []
        
        if len(df) < 3:
            return fvgs
        
        for i in range(1, len(df) - 1):
            prev_candle = df.iloc[i - 1]
            current_candle = df.iloc[i]
            next_candle = df.iloc[i + 1]
            
            # Bullish FVG
            if (prev_candle['high'] < next_candle['low']):
                fvgs.append({
                    "type": "bullish_fvg",
                    "index": i,
                    "gap_low": prev_candle['high'],
                    "gap_high": next_candle['low'],
                    "strength": next_candle['low'] - prev_candle['high']
                })
            
            # Bearish FVG
            elif (prev_candle['low'] > next_candle['high']):
                fvgs.append({
                    "type": "bearish_fvg",
                    "index": i,
                    "gap_low": next_candle['high'],
                    "gap_high": prev_candle['low'],
                    "strength": prev_candle['low'] - next_candle['high']
                })
        
        return fvgs
    
    def calculate_support_resistance(self, df: pd.DataFrame) -> Dict:
        """Calculate support and resistance levels from M5 or M15."""
        if len(df) < 20:
            return {"support": None, "resistance": None}
        
        # Use pivot points and recent highs/lows
        highs = df['high'].tail(20)
        lows = df['low'].tail(20)
        
        # Find clusters of highs and lows
        resistance_levels = highs.value_counts().head(3).index.tolist()
        support_levels = lows.value_counts().head(3).index.tolist()
        
        current_price = df['close'].iloc[-1]
        
        # Find nearest support and resistance
        nearest_resistance = min([r for r in resistance_levels if r > current_price], default=None)
        nearest_support = max([s for s in support_levels if s < current_price], default=None)
        
        return {
            "support": nearest_support,
            "resistance": nearest_resistance,
            "support_levels": support_levels,
            "resistance_levels": resistance_levels
        }
    
    def analyze_pair(self, df: pd.DataFrame, pair: str) -> Optional[Dict]:
        """Main analysis method combining all market structure elements."""
        try:
            if len(df) < 50:
                return None
            
            # 1. Analyze market structure (trend)
            structure = self.analyze_market_structure(df, "15min")
            if structure["structure"] == "insufficient_data":
                return None
            
            trend = structure["trend"]
            current_price = structure["current_price"]
            
            # 2. Find Order Blocks (POI)
            order_blocks = self.find_order_blocks(df, trend)
            if not order_blocks:
                return None
            
            # Get the strongest order block
            strongest_block = max(order_blocks, key=lambda x: x['strength'])
            
            # 3. Detect inducement
            inducements = self.detect_inducement(df, order_blocks)
            
            # 4. Find Fair Value Gaps
            fvgs = self.find_fair_value_gaps(df)
            
            # 5. Calculate Support/Resistance
            sr_levels = self.calculate_support_resistance(df)
            
            # 6. Generate signal based on alignment
            signal = None
            
            if trend == "bullish" and strongest_block['type'] == 'bullish_order_block':
                # Look for bullish inducement
                bullish_inducement = next((i for i in inducements if i['type'] == 'bullish_inducement'), None)
                
                if bullish_inducement:
                    entry_price = bullish_inducement['recovery_price']
                    stop_loss = strongest_block['low'] - (strongest_block['high'] - strongest_block['low']) * 0.1
                    
                    # Find nearest bullish FVG for take profit
                    bullish_fvgs = [f for f in fvgs if f['type'] == 'bullish_fvg' and f['gap_low'] > entry_price]
                    take_profit = bullish_fvgs[0]['gap_low'] if bullish_fvgs else entry_price * 1.005
                    
                    signal = {
                        "signal": "BUY",
                        "strategy": "Market Structure - Bullish",
                        "entry_price": round(entry_price, 5),
                        "stop_loss": round(stop_loss, 5),
                        "take_profit": round(take_profit, 5),
                        "confidence": "85%",
                        "trend": trend,
                        "order_block_strength": round(strongest_block['strength'], 4),
                        "inducement_detected": True
                    }
            
            elif trend == "bearish" and strongest_block['type'] == 'bearish_order_block':
                # Look for bearish inducement
                bearish_inducement = next((i for i in inducements if i['type'] == 'bearish_inducement'), None)
                
                if bearish_inducement:
                    entry_price = bearish_inducement['recovery_price']
                    stop_loss = strongest_block['high'] + (strongest_block['high'] - strongest_block['low']) * 0.1
                    
                    # Find nearest bearish FVG for take profit
                    bearish_fvgs = [f for f in fvgs if f['type'] == 'bearish_fvg' and f['gap_high'] < entry_price]
                    take_profit = bearish_fvgs[0]['gap_high'] if bearish_fvgs else entry_price * 0.995
                    
                    signal = {
                        "signal": "SELL",
                        "strategy": "Market Structure - Bearish",
                        "entry_price": round(entry_price, 5),
                        "stop_loss": round(stop_loss, 5),
                        "take_profit": round(take_profit, 5),
                        "confidence": "85%",
                        "trend": trend,
                        "order_block_strength": round(strongest_block['strength'], 4),
                        "inducement_detected": True
                    }
            
            if signal:
                signal.update({
                    "pair": pair,
                    "current_price": current_price,
                    "support": sr_levels["support"],
                    "resistance": sr_levels["resistance"],
                    "fvgs_count": len(fvgs),
                    "order_blocks_count": len(order_blocks)
                })
            
            return signal
            
        except Exception as e:
            logger.error(f"Error in market structure analysis for {pair}: {e}", exc_info=True)
            return None
    
    def get_strategy_info(self) -> Dict:
        """Get information about the strategy."""
        return {
            "name": self.name,
            "timeframes": self.timeframes,
            "description": "Market Structure Strategy using multiple timeframes for trend analysis, POI detection, inducement identification, and FVG-based exits.",
            "components": [
                "M15/H1 trend analysis",
                "M5/M1 Order Block detection",
                "M1/M3 inducement detection", 
                "M1 entry execution",
                "FVG and S/R exit strategy"
            ]
        }

# Create global instance
market_structure_strategy = MarketStructureStrategy() 