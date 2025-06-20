import time
from app.services.strategy_engine import multi_strategy_signal
from app.services.risk_service import RiskService
from app.services.realtime_service import RealTimeService

class MarketScanner:
    def __init__(self, pairs, db, telegram_alert_func):
        self.pairs = pairs
        self.db = db
        self.risk_service = RiskService()
        self.realtime_service = RealTimeService()
        self.telegram_alert_func = telegram_alert_func

    def scan(self):
        for symbol in self.pairs:
            # Fetch data for all timeframes (placeholder)
            # df_1h, df_4h, etc. should be loaded here
            df = None  # Replace with actual data
            signal = multi_strategy_signal(df)
            # Risk checks (placeholder)
            # Format and send notification if valid
            if signal['signal']:
                self.telegram_alert_func(symbol, signal)

    def run(self):
        while True:
            self.scan()
            time.sleep(300)  # 5 minutes 