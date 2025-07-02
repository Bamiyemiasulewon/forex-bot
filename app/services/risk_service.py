from typing import Dict, Optional
from app.services.market_service import market_service
import json
import datetime

class RiskService:
    # Initialize the risk management service with risk parameters for Order Block + RSI + Fibonacci strategy
    def __init__(self, max_risk_per_trade=0.10, max_positions=3, correlation_limit=0.7, max_daily_loss=0.10):
        self.max_risk_per_trade = max_risk_per_trade  # 10% of account per trade
        self.max_positions = max_positions  # Max 3 trades per day
        self.correlation_limit = correlation_limit
        self.max_daily_loss = max_daily_loss  # 10% daily loss limit
        self.daily_trades = 0
        self.daily_pnl = 0.0
        self.last_reset_date = None
        self._load_state()

    def _get_state(self):
        return {
            "daily_trades": self.daily_trades,
            "daily_pnl": self.daily_pnl,
            "last_reset_date": self.last_reset_date
        }

    def _save_state(self):
        try:
            with open("risk_state.json", "w") as f:
                json.dump(self._get_state(), f)
        except Exception as e:
            print(f"Error saving risk state: {e}")

    def _load_state(self):
        try:
            with open("risk_state.json", "r") as f:
                state = json.load(f)
                self.daily_trades = state.get("daily_trades", 0)
                self.daily_pnl = state.get("daily_pnl", 0.0)
                self.last_reset_date = state.get("last_reset_date")
                self._auto_reset_if_new_day()
        except Exception:
            self.last_reset_date = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d')
            self._save_state()

    def _auto_reset_if_new_day(self):
        today = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d')
        if self.last_reset_date != today:
            self.reset_daily_counters()
            self.last_reset_date = today
            self._save_state()
            print(f"RiskService: Auto-reset daily counters for new day: {today}")

    def reset_daily_counters(self):
        self.daily_trades = 0
        self.daily_pnl = 0.0
        self.last_reset_date = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d')
        self._save_state()
        print("RiskService: Daily counters reset.")

    async def calculate_position_size(
        self,
        account_balance: float,
        risk_percent: float,
        stop_loss_pips: float,
        pair: str
    ) -> Optional[Dict]:
        """
        Calculates the appropriate position size in lots for Order Block strategy.
        Uses 10% risk per trade as specified in the strategy.
        """
        if risk_percent <= 0 or stop_loss_pips <= 0 or account_balance <= 0:
            return {"error": "Account balance, risk percent, and stop-loss must be positive."}

        # Use strategy-specified risk (10%)
        strategy_risk_percent = 10.0  # 10% as per Order Block + RSI + Fibonacci strategy
        
        # 1 standard lot = 100,000 units
        pip_value_per_lot = await market_service.get_pip_value_in_usd(pair, 100000)

        if pip_value_per_lot is None:
            return {"error": f"Could not calculate pip value for {pair}."}

        risk_amount_usd = account_balance * (strategy_risk_percent / 100)
        sl_cost_per_lot = stop_loss_pips * pip_value_per_lot
        
        if sl_cost_per_lot == 0:
            return {"error": "Stop-loss cost cannot be zero."}
            
        position_size_lots = risk_amount_usd / sl_cost_per_lot
        
        return {
            "account_balance": account_balance,
            "risk_percent": strategy_risk_percent,
            "risk_amount_usd": risk_amount_usd,
            "stop_loss_pips": stop_loss_pips,
            "pair": pair,
            "position_size_lots": position_size_lots,
            "strategy": "Order Block + RSI + Fibonacci"
        }

    def calculate_position_size_sync(
        self,
        account_balance: float,
        risk_percent: float,
        stop_loss_pips: float,
        pair: str,
        pip_value_per_lot: float = None
    ) -> Optional[Dict]:
        """
        Synchronous version of calculate_position_size for testing purposes.
        """
        if risk_percent <= 0 or stop_loss_pips <= 0 or account_balance <= 0:
            return {"error": "Account balance, risk percent, and stop-loss must be positive."}

        # Use strategy-specified risk (10%)
        strategy_risk_percent = 10.0  # 10% as per Order Block + RSI + Fibonacci strategy
        
        # Use provided pip value or default for testing
        if pip_value_per_lot is None:
            # Default pip values for major pairs (approximate)
            pip_values = {
                "EURUSD": 10.0, "GBPUSD": 10.0, "USDJPY": 9.0, "USDCHF": 10.0,
                "AUDUSD": 10.0, "NZDUSD": 10.0, "USDCAD": 10.0, "EURGBP": 10.0,
                "EURJPY": 9.0, "GBPJPY": 9.0, "AUDJPY": 9.0, "EURCHF": 10.0
            }
            pip_value_per_lot = pip_values.get(pair, 10.0)

        risk_amount_usd = account_balance * (strategy_risk_percent / 100)
        sl_cost_per_lot = stop_loss_pips * pip_value_per_lot
        
        if sl_cost_per_lot == 0:
            return {"error": "Stop-loss cost cannot be zero."}
            
        position_size_lots = risk_amount_usd / sl_cost_per_lot
        
        return {
            "account_balance": account_balance,
            "risk_percent": strategy_risk_percent,
            "risk_amount_usd": risk_amount_usd,
            "stop_loss_pips": stop_loss_pips,
            "pair": pair,
            "position_size_lots": position_size_lots,
            "strategy": "Order Block + RSI + Fibonacci"
        }

    # Check if a new position can be opened based on Order Block strategy rules
    def can_open_new_position(self, open_positions, daily_loss, pair_correlation, account_balance):
        """
        Check if new position can be opened based on Order Block strategy risk rules:
        - Max 3 trades per day
        - Max 10% daily loss
        - 10% risk per trade
        """
        # Check max positions (3 trades per day)
        if open_positions >= self.max_positions:
            return False, f"Maximum daily trades reached ({self.max_positions})"
        
        # Check daily loss limit (10%)
        daily_loss_percent = abs(daily_loss) / account_balance if account_balance > 0 else 0
        if daily_loss_percent >= self.max_daily_loss:
            return False, f"Daily loss limit reached ({daily_loss_percent:.2%})"
        
        # Check correlation limit
        if pair_correlation > self.correlation_limit:
            return False, f"Pair correlation too high ({pair_correlation:.2f})"
        
        return True, "Position can be opened"

    # Calculate stop loss price based on Order Block strategy
    def apply_stop_loss(self, entry_price, stop_loss_pips, is_buy):
        """
        Calculate stop loss price for Order Block strategy.
        Stop loss is placed just beyond the order block or last swing.
        """
        if is_buy:
            return entry_price - stop_loss_pips
        else:
            return entry_price + stop_loss_pips

    # Calculate take profit price based on Order Block strategy (1:2 RR)
    def apply_take_profit(self, entry_price, stop_loss_pips, is_buy, risk_reward_ratio=2.0):
        """
        Calculate take profit price for Order Block strategy.
        Uses 1:2 risk-reward ratio as specified in the strategy.
        """
        risk = stop_loss_pips
        reward = risk * risk_reward_ratio
        
        if is_buy:
            return entry_price + reward
        else:
            return entry_price - reward

    def update_daily_stats(self, trade_result: float):
        """
        Update daily trading statistics for risk management.
        """
        self.daily_trades += 1
        self.daily_pnl += trade_result

    def get_risk_summary(self) -> Dict:
        """
        Get current risk management summary for Order Block strategy.
        """
        return {
            "strategy": "Order Block + RSI + Fibonacci",
            "risk_per_trade": f"{self.max_risk_per_trade:.1%}",
            "max_trades_per_day": self.max_positions,
            "max_daily_loss": f"{self.max_daily_loss:.1%}",
            "daily_trades": self.daily_trades,
            "daily_pnl": self.daily_pnl,
            "risk_reward_ratio": "1:2"
        }

# Singleton instance with Order Block strategy parameters
risk_service = RiskService(max_risk_per_trade=0.10, max_positions=3, max_daily_loss=0.10) 