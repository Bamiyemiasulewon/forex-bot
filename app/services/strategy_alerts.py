"""
Strategy Alert System for Order Block + RSI + Fibonacci Strategy
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class AlertType(Enum):
    """Types of strategy alerts."""
    SIGNAL_GENERATED = "signal_generated"
    TRADE_OPENED = "trade_opened"
    TRADE_CLOSED = "trade_closed"
    RISK_LIMIT_HIT = "risk_limit_hit"
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    DAILY_LIMIT_REACHED = "daily_limit_reached"
    STRATEGY_ERROR = "strategy_error"

class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

class StrategyAlert:
    """Represents a strategy alert."""
    
    def __init__(self, alert_type: AlertType, message: str, severity: AlertSeverity = AlertSeverity.INFO, data: Dict = None):
        self.type = alert_type
        self.message = message
        self.severity = severity
        self.data = data or {}
        self.timestamp = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict:
        """Convert alert to dictionary."""
        return {
            'type': self.type.value,
            'message': self.message,
            'severity': self.severity.value,
            'data': self.data,
            'timestamp': self.timestamp.isoformat()
        }

class StrategyAlertManager:
    """Manages strategy alerts and notifications."""
    
    def __init__(self):
        self.alerts: List[StrategyAlert] = []
        self.max_alerts = 1000  # Keep last 1000 alerts
        self.subscribers = []  # List of callback functions
    
    def add_alert(self, alert_type: AlertType, message: str, severity: AlertSeverity = AlertSeverity.INFO, data: Dict = None):
        """Add a new alert."""
        alert = StrategyAlert(alert_type, message, severity, data)
        self.alerts.append(alert)
        
        # Keep only the last max_alerts
        if len(self.alerts) > self.max_alerts:
            self.alerts = self.alerts[-self.max_alerts:]
        
        # Log the alert
        log_level = {
            AlertSeverity.INFO: logging.INFO,
            AlertSeverity.WARNING: logging.WARNING,
            AlertSeverity.CRITICAL: logging.ERROR
        }[severity]
        
        logger.log(log_level, f"Strategy Alert [{alert_type.value}]: {message}")
        
        # Notify subscribers
        self._notify_subscribers(alert)
    
    def signal_generated(self, pair: str, signal_type: str, confidence: int, entry_price: float, stop_loss: float, take_profit: float):
        """Alert when a new signal is generated."""
        message = f"🎯 Order Block Signal: {pair} {signal_type.upper()} (Confidence: {confidence}%)"
        data = {
            'pair': pair,
            'signal_type': signal_type,
            'confidence': confidence,
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit
        }
        self.add_alert(AlertType.SIGNAL_GENERATED, message, AlertSeverity.INFO, data)
    
    def trade_opened(self, pair: str, signal_type: str, entry_price: float, position_size: float):
        """Alert when a trade is opened."""
        message = f"📈 Trade Opened: {pair} {signal_type.upper()} at {entry_price:.5f}"
        data = {
            'pair': pair,
            'signal_type': signal_type,
            'entry_price': entry_price,
            'position_size': position_size
        }
        self.add_alert(AlertType.TRADE_OPENED, message, AlertSeverity.INFO, data)
    
    def trade_closed(self, pair: str, pnl: float, pnl_percent: float, duration_minutes: int):
        """Alert when a trade is closed."""
        emoji = "💰" if pnl > 0 else "📉"
        message = f"{emoji} Trade Closed: {pair} - PnL: ${pnl:.2f} ({pnl_percent:+.2f}%) - Duration: {duration_minutes}min"
        data = {
            'pair': pair,
            'pnl': pnl,
            'pnl_percent': pnl_percent,
            'duration_minutes': duration_minutes
        }
        severity = AlertSeverity.WARNING if pnl < 0 else AlertSeverity.INFO
        self.add_alert(AlertType.TRADE_CLOSED, message, severity, data)
    
    def risk_limit_hit(self, limit_type: str, current_value: float, limit_value: float):
        """Alert when risk limits are hit."""
        message = f"⚠️ Risk Limit Hit: {limit_type} - Current: {current_value:.2f}%, Limit: {limit_value:.2f}%"
        data = {
            'limit_type': limit_type,
            'current_value': current_value,
            'limit_value': limit_value
        }
        self.add_alert(AlertType.RISK_LIMIT_HIT, message, AlertSeverity.WARNING, data)
    
    def session_start(self, session_name: str):
        """Alert when trading session starts."""
        message = f"🌅 {session_name} Session Started - Order Block strategy active"
        data = {'session': session_name}
        self.add_alert(AlertType.SESSION_START, message, AlertSeverity.INFO, data)
    
    def session_end(self, session_name: str):
        """Alert when trading session ends."""
        message = f"🌆 {session_name} Session Ended - Strategy monitoring only"
        data = {'session': session_name}
        self.add_alert(AlertType.SESSION_END, message, AlertSeverity.INFO, data)
    
    def daily_limit_reached(self, limit_type: str, limit_value: int):
        """Alert when daily limits are reached."""
        message = f"🛑 Daily Limit Reached: {limit_type} ({limit_value}) - Trading stopped for today"
        data = {'limit_type': limit_type, 'limit_value': limit_value}
        self.add_alert(AlertType.DAILY_LIMIT_REACHED, message, AlertSeverity.WARNING, data)
    
    def strategy_error(self, error_message: str, pair: str = None):
        """Alert when strategy encounters an error."""
        message = f"❌ Strategy Error: {error_message}"
        data = {'error': error_message, 'pair': pair}
        self.add_alert(AlertType.STRATEGY_ERROR, message, AlertSeverity.CRITICAL, data)
    
    def get_recent_alerts(self, count: int = 10) -> List[Dict]:
        """Get recent alerts."""
        recent = self.alerts[-count:] if self.alerts else []
        return [alert.to_dict() for alert in recent]
    
    def get_alerts_by_type(self, alert_type: AlertType) -> List[Dict]:
        """Get alerts by type."""
        filtered = [alert for alert in self.alerts if alert.type == alert_type]
        return [alert.to_dict() for alert in filtered]
    
    def get_alerts_by_severity(self, severity: AlertSeverity) -> List[Dict]:
        """Get alerts by severity."""
        filtered = [alert for alert in self.alerts if alert.severity == severity]
        return [alert.to_dict() for alert in filtered]
    
    def subscribe(self, callback):
        """Subscribe to alert notifications."""
        self.subscribers.append(callback)
    
    def _notify_subscribers(self, alert: StrategyAlert):
        """Notify all subscribers of a new alert."""
        for callback in self.subscribers:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Error in alert subscriber callback: {e}")
    
    def get_alert_summary(self) -> Dict:
        """Get alert summary statistics."""
        if not self.alerts:
            return {'total_alerts': 0}
        
        total_alerts = len(self.alerts)
        alerts_by_type = {}
        alerts_by_severity = {}
        
        for alert in self.alerts:
            # Count by type
            alert_type = alert.type.value
            alerts_by_type[alert_type] = alerts_by_type.get(alert_type, 0) + 1
            
            # Count by severity
            severity = alert.severity.value
            alerts_by_severity[severity] = alerts_by_severity.get(severity, 0) + 1
        
        return {
            'total_alerts': total_alerts,
            'alerts_by_type': alerts_by_type,
            'alerts_by_severity': alerts_by_severity,
            'recent_alerts': self.get_recent_alerts(5)
        }

# Global alert manager instance
strategy_alerts = StrategyAlertManager() 