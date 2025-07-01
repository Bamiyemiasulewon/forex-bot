# forex-bot/app/services/ai_config.py
from typing import Dict, List

class AIConfig:
    """
    Centralized configuration for the AI Trading Bot.
    """
    # --- Core Settings ---
    SYMBOLS: List[str] = ["EURUSD", "GBPUSD", "GBPJPY", "NZDUSD", "AUDCAD", "XAUUSD"]
    TIMEFRAME: str = "15m"  # 15-minute charts
    CANDLE_COUNT: int = 100  # Number of historical candles to analyze
    LOOP_INTERVAL_SECONDS: int = 30  # Time between each analysis cycle

    # --- Trade Isolation & Coexistence ---
    AI_MAGIC_NUMBER: int = 13579  # Unique ID for AI-placed trades
    MANUAL_MAGIC_NUMBER: int = 97531 # Unique ID for bot-assisted manual trades
    SHADOW_MODE: bool = False  # If True, AI will not execute trades, only log them
    AVOID_OPPOSING_MANUAL_TRADES: bool = True # If True, AI won't trade against a manual position on the same symbol
    MAX_TOTAL_OPEN_TRADES: int = 5 # Maximum combined (AI + Manual) open trades

    # --- Risk Management ---
    RISK_PER_TRADE_PERCENT: float = 5.0
    RISK_REWARD_RATIO: float = 3.0
    MAX_DAILY_TRADES: int = 10
    MAX_DAILY_RISK_PERCENT: float = 10.0
    MINIMUM_ACCOUNT_BALANCE: float = 20.0
    MAX_ACCOUNT_DRAWDOWN_PERCENT: float = 20.0
    EMERGENCY_STOP_DAILY_DRAWDOWN_PERCENT: float = 15.0
    MIN_POSITION_SIZE: float = 0.01

    # --- Indicator Settings ---
    RSI_PERIOD: int = 14
    MA_FAST_PERIOD: int = 12
    MA_SLOW_PERIOD: int = 26
    MACD_SIGNAL_PERIOD: int = 9

    # --- Pair-Specific Settings ---
    # Stop Loss is in PIPS for forex, and points for Gold.
    PAIR_SETTINGS: Dict[str, Dict] = {
        "DEFAULT": {"stop_loss_pips": 50},
        "EURUSD": {"stop_loss_pips": 50},
        "GBPUSD": {"stop_loss_pips": 50},
        "GBPJPY": {"stop_loss_pips": 80},
        "NZDUSD": {"stop_loss_pips": 60},
        "AUDCAD": {"stop_loss_pips": 60},
        "XAUUSD": {"stop_loss_pips": 200},
    }

    @classmethod
    def get_stop_loss(cls, symbol: str) -> int:
        """Returns the stop loss in pips/points for a given symbol."""
        return cls.PAIR_SETTINGS.get(symbol, cls.PAIR_SETTINGS["DEFAULT"])["stop_loss_pips"]

    @classmethod
    def get_take_profit(cls, symbol: str) -> int:
        """Calculates take profit based on the 1:3 risk-reward ratio."""
        sl = cls.get_stop_loss(symbol)
        return int(sl * cls.RISK_REWARD_RATIO)

# Instantiate the config for easy import
ai_config = AIConfig() 