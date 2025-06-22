from typing import Dict, Optional
from app.services.market_service import market_service

class RiskService:
    # Initialize the risk management service with risk parameters.
    def __init__(self, max_risk_per_trade=0.015, max_positions=3, correlation_limit=0.7, max_daily_loss=0.05):
        self.max_risk_per_trade = max_risk_per_trade  # e.g., 1.5% of account
        self.max_positions = max_positions
        self.correlation_limit = correlation_limit
        self.max_daily_loss = max_daily_loss

    def calculate_position_size(
        self,
        account_balance: float,
        risk_percent: float,
        stop_loss_pips: float,
        pair: str
    ) -> Optional[Dict]:
        """
        Calculates the appropriate position size in lots.
        """
        if risk_percent <= 0 or stop_loss_pips <= 0 or account_balance <= 0:
            return {"error": "Account balance, risk percent, and stop-loss must be positive."}

        # 1 standard lot = 100,000 units
        pip_value_per_lot = market_service.get_pip_value_in_usd(pair, 100000)

        if pip_value_per_lot is None:
            return {"error": f"Could not calculate pip value for {pair}."}

        risk_amount_usd = account_balance * (risk_percent / 100)
        sl_cost_per_lot = stop_loss_pips * pip_value_per_lot
        
        if sl_cost_per_lot == 0:
            return {"error": "Stop-loss cost cannot be zero."}
            
        position_size_lots = risk_amount_usd / sl_cost_per_lot
        
        return {
            "account_balance": account_balance,
            "risk_percent": risk_percent,
            "risk_amount_usd": risk_amount_usd,
            "stop_loss_pips": stop_loss_pips,
            "pair": pair,
            "position_size_lots": position_size_lots
        }

    # Check if a new position can be opened based on open positions, daily loss, and correlation.
    def can_open_new_position(self, open_positions, daily_loss, pair_correlation):
        if open_positions >= self.max_positions:
            return False
        if daily_loss >= self.max_daily_loss:
            return False
        if pair_correlation > self.correlation_limit:
            return False
        return True

    # Calculate stop loss price based on entry price, stop loss pips, and trade direction.
    def apply_stop_loss(self, entry_price, stop_loss_pips, is_buy):
        if is_buy:
            return entry_price - stop_loss_pips
        else:
            return entry_price + stop_loss_pips

    # Calculate take profit price based on entry price, take profit pips, and trade direction.
    def apply_take_profit(self, entry_price, take_profit_pips, is_buy):
        if is_buy:
            return entry_price + take_profit_pips
        else:
            return entry_price - take_profit_pips

# Singleton instance
risk_service = RiskService() 