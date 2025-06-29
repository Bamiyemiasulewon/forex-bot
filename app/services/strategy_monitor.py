"""
Strategy Monitoring Service for Order Block + RSI + Fibonacci Strategy
"""

import logging
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from app.services.order_block_strategy import order_block_strategy
from app.services.risk_service import risk_service

logger = logging.getLogger(__name__)

@dataclass
class StrategyAlert:
    """Strategy alert data structure."""
    type: str  # 'signal', 'risk', 'session', 'performance'
    message: str
    severity: str  # 'info', 'warning', 'critical'
    timestamp: datetime
    data: Dict

class StrategyMonitor:
    """Monitors Order Block strategy performance and generates alerts."""
    
    def __init__(self):
        self.alerts: List[StrategyAlert] = []
        self.last_check = datetime.now(timezone.utc)
        self.monitoring_active = True
        
    async def start_monitoring(self):
        """Start the strategy monitoring loop."""
        logger.info("Starting Order Block strategy monitoring...")
        while self.monitoring_active:
            try:
                await self.check_strategy_status()
                await self.check_risk_limits()
                await self.check_trading_sessions()
                await self.cleanup_old_alerts()
                
                # Wait 5 minutes before next check
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"Error in strategy monitoring: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def check_strategy_status(self):
        """Check overall strategy status."""
        strategy_info = order_block_strategy.get_strategy_info()
        
        # Check if strategy is active
        if not strategy_info['in_session']:
            self.add_alert(
                type='session',
                message="Order Block strategy is outside trading sessions",
                severity='info',
                data={'session_status': 'inactive'}
            )
        
        # Check daily trade limit
        if strategy_info['daily_trades'] >= strategy_info['max_trades_per_day']:
            self.add_alert(
                type='risk',
                message=f"Daily trade limit reached ({strategy_info['daily_trades']}/{strategy_info['max_trades_per_day']})",
                severity='warning',
                data={'daily_trades': strategy_info['daily_trades']}
            )
    
    async def check_risk_limits(self):
        """Check risk management limits."""
        risk_summary = risk_service.get_risk_summary()
        daily_pnl = risk_summary['daily_pnl']
        max_daily_loss = float(risk_summary['max_daily_loss'].rstrip('%'))
        
        # Check daily loss limit
        if abs(daily_pnl) >= max_daily_loss * 100:  # Convert percentage to dollars
            self.add_alert(
                type='risk',
                message=f"Daily loss limit reached: ${daily_pnl:.2f}",
                severity='critical',
                data={'daily_pnl': daily_pnl, 'limit': max_daily_loss}
            )
        
        # Check if approaching daily loss limit (80% of limit)
        if abs(daily_pnl) >= max_daily_loss * 80:
            self.add_alert(
                type='risk',
                message=f"Approaching daily loss limit: ${daily_pnl:.2f}",
                severity='warning',
                data={'daily_pnl': daily_pnl, 'limit': max_daily_loss}
            )
    
    async def check_trading_sessions(self):
        """Check trading session status."""
        current_hour = datetime.now(timezone.utc).hour
        
        # London session starting soon
        if current_hour == 6:  # 1 hour before London session
            self.add_alert(
                type='session',
                message="London session starting in 1 hour",
                severity='info',
                data={'session': 'london', 'start_time': '07:00 GMT'}
            )
        
        # New York session starting soon
        if current_hour == 11:  # 1 hour before NY session
            self.add_alert(
                type='session',
                message="New York session starting in 1 hour",
                severity='info',
                data={'session': 'new_york', 'start_time': '12:00 GMT'}
            )
    
    def add_alert(self, type: str, message: str, severity: str, data: Dict):
        """Add a new strategy alert."""
        alert = StrategyAlert(
            type=type,
            message=message,
            severity=severity,
            timestamp=datetime.now(timezone.utc),
            data=data
        )
        self.alerts.append(alert)
        logger.info(f"Strategy alert: {severity.upper()} - {message}")
    
    async def cleanup_old_alerts(self):
        """Remove alerts older than 24 hours."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
        self.alerts = [alert for alert in self.alerts if alert.timestamp > cutoff_time]
    
    def get_recent_alerts(self, hours: int = 24) -> List[StrategyAlert]:
        """Get alerts from the last N hours."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        return [alert for alert in self.alerts if alert.timestamp > cutoff_time]
    
    def get_alerts_by_type(self, alert_type: str) -> List[StrategyAlert]:
        """Get alerts by type."""
        return [alert for alert in self.alerts if alert.type == alert_type]
    
    def get_alerts_by_severity(self, severity: str) -> List[StrategyAlert]:
        """Get alerts by severity level."""
        return [alert for alert in self.alerts if alert.severity == severity]
    
    def get_strategy_summary(self) -> Dict:
        """Get a summary of strategy monitoring status."""
        recent_alerts = self.get_recent_alerts(24)
        
        return {
            'monitoring_active': self.monitoring_active,
            'total_alerts_24h': len(recent_alerts),
            'critical_alerts': len(self.get_alerts_by_severity('critical')),
            'warning_alerts': len(self.get_alerts_by_severity('warning')),
            'info_alerts': len(self.get_alerts_by_severity('info')),
            'last_check': self.last_check.isoformat(),
            'recent_alerts': [
                {
                    'type': alert.type,
                    'message': alert.message,
                    'severity': alert.severity,
                    'timestamp': alert.timestamp.isoformat()
                }
                for alert in recent_alerts[-5:]  # Last 5 alerts
            ]
        }
    
    def stop_monitoring(self):
        """Stop the strategy monitoring."""
        self.monitoring_active = False
        logger.info("Order Block strategy monitoring stopped")

# Global strategy monitor instance
strategy_monitor = StrategyMonitor() 