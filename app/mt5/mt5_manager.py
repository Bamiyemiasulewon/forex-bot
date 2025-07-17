import MetaTrader5 as mt5
import logging
import time
import concurrent.futures

logger = logging.getLogger("mt5_service")

class MT5Service:
    def __init__(self):
        self.connected = False
        self.last_login = None

    def _do_connect(self, login, password, server):
        return mt5.initialize(login=login, password=password, server=server)

    def connect(self, login, password, server, max_retries=3, backoff=2):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            for attempt in range(1, max_retries + 1):
                logger.info(f"Attempting MT5 connection (try {attempt}/{max_retries})...")
                future = executor.submit(self._do_connect, login, password, server)
                try:
                    result = future.result(timeout=10)  # 10 seconds timeout
                except concurrent.futures.TimeoutError:
                    logger.error("MT5 connection attempt timed out.")
                    result = False
                if result:
                    self.connected = True
                    self.last_login = login
                    logger.info("MT5 connected successfully.")
                    return True
                else:
                    error = mt5.last_error()
                    logger.error(f"MT5 connection failed: {error}")
                    if attempt < max_retries:
                        time.sleep(backoff ** attempt)
            self.connected = False
            return False

    def disconnect(self):
        mt5.shutdown()
        self.connected = False
        logger.info("MT5 disconnected.")

    def is_connected(self):
        return self.connected and mt5.terminal_info() is not None

    def get_balance(self):
        if not self.is_connected():
            logger.warning("MT5 not connected when fetching balance.")
            return None
        account_info = mt5.account_info()
        if account_info:
            return account_info.balance
        logger.error("Failed to fetch account info from MT5.")
        return None

    def get_data(self, symbol, timeframe=mt5.TIMEFRAME_M15, count=100):
        if not self.is_connected():
            logger.warning("MT5 not connected when fetching data.")
            return None
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
        if rates is None or len(rates) == 0:
            logger.warning(f"No data for {symbol}.")
            return None
        return rates 