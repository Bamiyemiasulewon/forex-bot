"""
Strategy Performance Tracker for Order Block Strategy
"""

import logging
import json
from datetime import datetime, timezone
from typing import Dict, List
from app.services.order_block_strategy import order_block_strategy
from app.services.risk_service import risk_service

logger = logging.getLogger(__name__)

class StrategyPerformanceTracker:
    """Tracks Order Block strategy performance."""
    
    def __init__(self):
        self.trades = []
        self.stats_file = "order_block_performance.json"
    
    def add_trade(self, pair: str, signal_type: str, entry_price: float, 
                  stop_loss: float, take_profit: float, position_size: float,
                  fibonacci_level: float = None, rsi_value: float = None):
        """Add a new trade."""
        trade = {
            'pair': pair,
            'signal_type': signal_type,
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'position_size': position_size,
            'fibonacci_level': fibonacci_level,
            'rsi_value': rsi_value,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'status': 'open',
            'pnl': 0.0
        }
        self.trades.append(trade)
        logger.info(f"Added trade: {pair} {signal_type}")
    
    def close_trade(self, trade_index: int, exit_price: float, pnl: float):
        """Close a trade."""
        if 0 <= trade_index < len(self.trades):
            self.trades[trade_index]['exit_price'] = exit_price
            self.trades[trade_index]['pnl'] = pnl
            self.trades[trade_index]['status'] = 'closed'
            logger.info(f"Closed trade: PnL ${pnl:.2f}")
    
    def get_stats(self) -> Dict:
        """Get performance statistics."""
        if not self.trades:
            return {'total_trades': 0, 'win_rate': 0, 'total_pnl': 0}
        
        closed_trades = [t for t in self.trades if t['status'] == 'closed']
        if not closed_trades:
            return {'total_trades': len(self.trades), 'open_trades': len(self.trades)}
        
        winning_trades = [t for t in closed_trades if t['pnl'] > 0]
        total_pnl = sum(t['pnl'] for t in closed_trades)
        win_rate = (len(winning_trades) / len(closed_trades)) * 100
        
        return {
            'total_trades': len(self.trades),
            'closed_trades': len(closed_trades),
            'winning_trades': len(winning_trades),
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'average_pnl': total_pnl / len(closed_trades) if closed_trades else 0
        }
    
    def get_performance_report(self) -> Dict:
        """Generate performance report."""
        stats = self.get_stats()
        strategy_info = order_block_strategy.get_strategy_info()
        
        return {
            'strategy_info': strategy_info,
            'performance_stats': stats,
            'recent_trades': self.trades[-10:] if self.trades else []
        }

# Global instance
strategy_performance = StrategyPerformanceTracker() 