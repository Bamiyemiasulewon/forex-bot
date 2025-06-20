class RiskService:
    # Initialize the risk management service with risk parameters.
    def __init__(self, max_risk_per_trade=0.015, max_positions=3, correlation_limit=0.7, max_daily_loss=0.05):
        self.max_risk_per_trade = max_risk_per_trade  # e.g., 1.5% of account
        self.max_positions = max_positions
        self.correlation_limit = correlation_limit
        self.max_daily_loss = max_daily_loss

    # Calculate position size based on account balance, ATR, and stop multiplier.
    def calculate_position_size(self, account_balance, atr, stop_multiplier):
        risk_amount = account_balance * self.max_risk_per_trade
        position_size = risk_amount / (atr * stop_multiplier)
        return max(position_size, 0)

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