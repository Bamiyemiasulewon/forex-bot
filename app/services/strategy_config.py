"""
Strategy Configuration Manager for Order Block + RSI + Fibonacci Strategy
"""

import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class StrategyConfig:
    """Manages configuration for the Order Block + RSI + Fibonacci strategy."""
    
    def __init__(self, config_file: str = "strategy_config.json"):
        self.config_file = config_file
        self.config = self._load_default_config()
        self._load_config()
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration."""
        return {
            "strategy_name": "Order Block + RSI + Fibonacci",
            "timeframe": "M5",
            "indicators": {
                "rsi": {
                    "period": 14,
                    "oversold": 30,
                    "overbought": 70
                },
                "fibonacci": {
                    "levels": [0.382, 0.5, 0.618],
                    "tolerance": 0.001
                },
                "atr": {
                    "period": 14
                }
            },
            "order_block": {
                "lookback_period": 20,
                "volume_threshold": 1.0
            },
            "risk_management": {
                "risk_per_trade": 0.10,  # 10%
                "max_trades_per_day": 3,
                "max_daily_loss": 0.10,  # 10%
                "risk_reward_ratio": 2.0,  # 1:2
                "stop_trading_on_drawdown": True
            },
            "trading_sessions": {
                "london": {
                    "start": 7,  # 7 AM GMT
                    "end": 11    # 11 AM GMT
                },
                "new_york": {
                    "start": 12,  # 12 PM GMT
                    "end": 16     # 4 PM GMT
                }
            },
            "pairs": [
                "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "NZDUSD", "USDCAD",
                "EURGBP", "EURJPY", "GBPJPY", "AUDJPY", "EURCHF"
            ],
            "notifications": {
                "enable_alerts": True,
                "alert_on_signal": True,
                "alert_on_trade": True,
                "alert_on_risk_limit": True
            },
            "performance": {
                "enable_tracking": True,
                "save_trades": True,
                "generate_reports": True
            }
        }
    
    def _load_config(self):
        """Load configuration from file."""
        try:
            if Path(self.config_file).exists():
                with open(self.config_file, 'r') as f:
                    file_config = json.load(f)
                    self.config.update(file_config)
                logger.info(f"Loaded configuration from {self.config_file}")
            else:
                self.save_config()
                logger.info(f"Created default configuration file: {self.config_file}")
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
    
    def save_config(self):
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """Set configuration value."""
        keys = key.split('.')
        config = self.config
        
        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
        logger.info(f"Configuration updated: {key} = {value}")
    
    def update_config(self, updates: Dict[str, Any]):
        """Update multiple configuration values."""
        for key, value in updates.items():
            self.set(key, value)
        self.save_config()
    
    def get_rsi_config(self) -> Dict[str, Any]:
        """Get RSI configuration."""
        return self.get("indicators.rsi", {})
    
    def get_fibonacci_config(self) -> Dict[str, Any]:
        """Get Fibonacci configuration."""
        return self.get("indicators.fibonacci", {})
    
    def get_risk_config(self) -> Dict[str, Any]:
        """Get risk management configuration."""
        return self.get("risk_management", {})
    
    def get_session_config(self) -> Dict[str, Any]:
        """Get trading session configuration."""
        return self.get("trading_sessions", {})
    
    def get_pairs(self) -> list:
        """Get trading pairs."""
        return self.get("pairs", [])
    
    def add_pair(self, pair: str):
        """Add a trading pair."""
        pairs = self.get_pairs()
        if pair not in pairs:
            pairs.append(pair)
            self.set("pairs", pairs)
            self.save_config()
    
    def remove_pair(self, pair: str):
        """Remove a trading pair."""
        pairs = self.get_pairs()
        if pair in pairs:
            pairs.remove(pair)
            self.set("pairs", pairs)
            self.save_config()
    
    def get_notification_config(self) -> Dict[str, Any]:
        """Get notification configuration."""
        return self.get("notifications", {})
    
    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance tracking configuration."""
        return self.get("performance", {})
    
    def validate_config(self) -> bool:
        """Validate configuration."""
        try:
            # Check required fields
            required_fields = [
                "strategy_name",
                "timeframe",
                "indicators.rsi.period",
                "indicators.rsi.oversold",
                "indicators.rsi.overbought",
                "risk_management.risk_per_trade",
                "risk_management.max_trades_per_day",
                "risk_management.max_daily_loss"
            ]
            
            for field in required_fields:
                if self.get(field) is None:
                    logger.error(f"Missing required configuration field: {field}")
                    return False
            
            # Validate risk percentages
            risk_per_trade = self.get("risk_management.risk_per_trade")
            max_daily_loss = self.get("risk_management.max_daily_loss")
            
            if not (0 < risk_per_trade <= 1):
                logger.error(f"Invalid risk_per_trade: {risk_per_trade}. Must be between 0 and 1.")
                return False
            
            if not (0 < max_daily_loss <= 1):
                logger.error(f"Invalid max_daily_loss: {max_daily_loss}. Must be between 0 and 1.")
                return False
            
            # Validate RSI values
            rsi_oversold = self.get("indicators.rsi.oversold")
            rsi_overbought = self.get("indicators.rsi.overbought")
            
            if not (0 <= rsi_oversold <= 100):
                logger.error(f"Invalid RSI oversold: {rsi_oversold}. Must be between 0 and 100.")
                return False
            
            if not (0 <= rsi_overbought <= 100):
                logger.error(f"Invalid RSI overbought: {rsi_overbought}. Must be between 0 and 100.")
                return False
            
            if rsi_oversold >= rsi_overbought:
                logger.error("RSI oversold must be less than RSI overbought.")
                return False
            
            logger.info("Configuration validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary."""
        return {
            "strategy_name": self.get("strategy_name"),
            "timeframe": self.get("timeframe"),
            "risk_per_trade": f"{self.get('risk_management.risk_per_trade', 0) * 100:.1f}%",
            "max_trades_per_day": self.get("risk_management.max_trades_per_day"),
            "max_daily_loss": f"{self.get('risk_management.max_daily_loss', 0) * 100:.1f}%",
            "trading_pairs": len(self.get_pairs()),
            "notifications_enabled": self.get("notifications.enable_alerts", False),
            "performance_tracking": self.get("performance.enable_tracking", False)
        }

# Global configuration instance
strategy_config = StrategyConfig() 