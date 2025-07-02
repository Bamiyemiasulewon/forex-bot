# forex-bot/app/services/ai_risk_manager.py
import logging
import json
import os
from typing import Dict, Any, List

from .ai_config import AIConfig
from .mt5_service import MT5Service

logger = logging.getLogger(__name__)

STATE_FILE = "ai_state.json"

class AIRiskManager:
    """
    Manages all risk calculations and validations for the AI Trading Bot.
    """
    def __init__(self, config: AIConfig, mt5_service: MT5Service):
        self.config = config
        self.mt5 = mt5_service
        self.daily_trade_count = 0
        self.daily_pnl = 0.0
        self.daily_pair_trade_count = {}  # {pair: count}
        self.daily_pair_pnl = {}  # {pair: pnl}
        self.daily_pair_traded = {}  # {pair: True/False} - tracks if pair was traded today
        self.load_state()

    def _get_state(self) -> Dict[str, Any]:
        """Gets the current state as a dictionary."""
        return {
            "daily_trade_count": self.daily_trade_count,
            "daily_pnl": self.daily_pnl,
            "daily_pair_trade_count": self.daily_pair_trade_count,
            "daily_pair_pnl": self.daily_pair_pnl,
            "daily_pair_traded": self.daily_pair_traded
        }

    def save_state(self):
        """Saves the current risk state to a file."""
        try:
            with open(STATE_FILE, 'w') as f:
                json.dump(self._get_state(), f)
            logger.info("AI risk state saved successfully.")
        except IOError as e:
            logger.error(f"Error saving AI state: {e}")

    def load_state(self):
        """Loads the risk state from a file if it exists."""
        if not os.path.exists(STATE_FILE):
            logger.info("No AI state file found. Starting fresh.")
            return

        try:
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
                self.daily_trade_count = state.get("daily_trade_count", 0)
                self.daily_pnl = state.get("daily_pnl", 0.0)
                self.daily_pair_trade_count = state.get("daily_pair_trade_count", {})
                self.daily_pair_pnl = state.get("daily_pair_pnl", {})
                self.daily_pair_traded = state.get("daily_pair_traded", {})
                logger.info("AI risk state loaded successfully.")
        except (IOError, json.JSONDecodeError) as e:
            logger.error(f"Error loading AI state, starting fresh: {e}")

    def reset_daily_counters(self):
        """Resets all daily counters and pair tracking."""
        self.daily_trade_count = 0
        self.daily_pnl = 0.0
        self.daily_pair_trade_count = {}
        self.daily_pair_pnl = {}
        self.daily_pair_traded = {}  # Reset daily pair trading status
        self.save_state()
        logger.info("🔄 Daily counters and pair tracking reset.")

    def can_trade_pair_today(self, pair: str) -> bool:
        """Check if a specific pair can be traded today (only one trade per pair per day)."""
        return not self.daily_pair_traded.get(pair, False)

    def mark_pair_traded_today(self, pair: str):
        """Mark a pair as traded today to prevent multiple trades on the same pair."""
        self.daily_pair_traded[pair] = True
        self.save_state()
        logger.info(f"✅ {pair} marked as traded today.")

    def get_daily_pair_status(self) -> Dict[str, Any]:
        """Get status of all pairs for today."""
        return {
            "daily_trade_count": self.daily_trade_count,
            "daily_pnl": self.daily_pnl,
            "pairs_traded_today": list(self.daily_pair_traded.keys()),
            "pairs_available_today": [pair for pair in self.get_all_pairs() if not self.daily_pair_traded.get(pair, False)],
            "daily_pair_pnl": self.daily_pair_pnl
        }

    def get_all_pairs(self) -> List[str]:
        """Get list of all trading pairs."""
        return [
            "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "NZDUSD", "USDCAD",
            "EURGBP", "EURJPY", "GBPJPY", "AUDJPY", "EURCHF", "XAUUSD"
        ]

    async def calculate_position_size(self, balance: float, symbol: str) -> float:
        """
        Calculates the appropriate position size based on the 5% risk rule.
        Returns 0.0 if a trade cannot be placed.
        """
        if balance < self.config.MINIMUM_ACCOUNT_BALANCE:
            logger.warning(f"Balance ${balance:.2f} is below minimum ${self.config.MINIMUM_ACCOUNT_BALANCE}. No trade.")
            return 0.0

        if self.daily_trade_count >= self.config.MAX_DAILY_TRADES:
            logger.warning(f"Daily trade limit of {self.config.MAX_DAILY_TRADES} reached. No more trades today.")
            return 0.0
            
        risk_amount_usd = balance * (self.config.RISK_PER_TRADE_PERCENT / 100.0)
        stop_loss_pips = self.config.get_stop_loss(symbol)

        # First, get pip value for a 1.0 lot size to determine the value per pip
        pip_value_per_lot = await self.mt5.get_pip_value(symbol, 1.0)
        if pip_value_per_lot == 0.0:
            logger.error(f"Could not calculate pip value for {symbol}. Cannot determine position size.")
            return 0.0
            
        # Value of one pip for one lot
        cost_per_pip = pip_value_per_lot

        # Calculate position size
        # Position Size = Risk Amount / (Stop Loss Pips * Value per Pip)
        position_size = risk_amount_usd / (stop_loss_pips * cost_per_pip)
        
        # Validate against minimum and round to broker's increment
        if position_size < self.config.MIN_POSITION_SIZE:
            logger.warning(f"Calculated position size {position_size:.4f} is below minimum {self.config.MIN_POSITION_SIZE}. No trade.")
            return 0.0
            
        # Round to 2 decimal places (standard for most brokers)
        final_position_size = round(position_size, 2)
        
        logger.info(
            f"Position size calculated for {symbol}: "
            f"Balance=${balance:.2f}, Risk=${risk_amount_usd:.2f}, "
            f"SL Pips={stop_loss_pips}, Pip Value=${cost_per_pip:.2f}/lot, "
            f"Size={final_position_size:.2f} lots"
        )
        
        return final_position_size

    def record_trade_opened(self, pair=None):
        """Increments the daily trade counter, and per-pair if pair is given."""
        self.daily_trade_count += 1
        if pair:
            self.daily_pair_trade_count[pair] = self.daily_pair_trade_count.get(pair, 0) + 1
        logger.info(f"Trade opened. Daily trade count is now {self.daily_trade_count}/{self.config.MAX_DAILY_TRADES}.")
        self.save_state()

    def record_trade_closed(self, pnl: float, pair=None):
        """Records the P&L of a closed trade, and per-pair if pair is given."""
        self.daily_pnl += pnl
        if pair:
            self.daily_pair_pnl[pair] = self.daily_pair_pnl.get(pair, 0.0) + pnl
        logger.info(f"Trade closed with P&L: ${pnl:.2f}. Total daily P&L: ${self.daily_pnl:.2f}.")
        self.save_state() 