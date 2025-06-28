import MetaTrader5 as mt5
import threading

class MT5Manager:
    def __init__(self):
        self.sessions = {}
        self.lock = threading.Lock()
        self.latest_signals = {}  # Optional: store latest signal per user

    def connect(self, user_id, login, password, server):
        with self.lock:
            if user_id in self.sessions:
                self.disconnect(user_id)
            if not mt5.initialize():
                return False, "MT5 terminal initialization failed"
            authorized = mt5.login(login=int(login), password=password, server=server)
            if not authorized:
                return False, f"MT5 login failed: {mt5.last_error()}"
            self.sessions[user_id] = True
            return True, "Connected"

    def disconnect(self, user_id):
        with self.lock:
            if user_id in self.sessions:
                mt5.shutdown()
                del self.sessions[user_id]

    def is_connected(self, user_id):
        return self.sessions.get(user_id, False)

    def get_account_info(self, user_id):
        if not self.is_connected(user_id):
            return None
        info = mt5.account_info()
        if info:
            return {
                "login": info.login,
                "balance": info.balance,
                "equity": info.equity,
                "margin": info.margin,
                "free_margin": info.margin_free,
                "leverage": info.leverage,
                "name": getattr(info, 'name', ''),
                "server": info.server,
            }
        return None

    def get_open_trades(self, user_id):
        if not self.is_connected(user_id):
            return None
        positions = mt5.positions_get()
        if positions is None:
            return []
        trades = []
        for pos in positions:
            trades.append({
                "ticket": pos.ticket,
                "symbol": pos.symbol,
                "type": "buy" if pos.type == mt5.POSITION_TYPE_BUY else "sell",
                "volume": pos.volume,
                "price_open": pos.price_open,
                "sl": pos.sl,
                "tp": pos.tp,
                "profit": pos.profit,
                "time": pos.time,
            })
        return trades

    def place_trade(self, user_id, symbol, trade_type, lot, sl, tp):
        if not self.is_connected(user_id):
            return False, "Not connected to MT5"
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            return False, f"Symbol {symbol} not found"
        if not symbol_info.visible:
            mt5.symbol_select(symbol, True)
        price = mt5.symbol_info_tick(symbol).ask if trade_type == "buy" else mt5.symbol_info_tick(symbol).bid
        order_type = mt5.ORDER_TYPE_BUY if trade_type == "buy" else mt5.ORDER_TYPE_SELL
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(lot),
            "type": order_type,
            "price": price,
            "sl": float(sl) if sl else 0.0,
            "tp": float(tp) if tp else 0.0,
            "deviation": 20,
            "magic": 123456,
            "comment": "TelegramBotTrade",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            return False, f"Order failed: {result.comment}"
        return True, f"Order placed! Ticket: {result.order}"

    def get_latest_signal(self, user_id):
        # Optional: implement if you want to store signals per user
        return self.latest_signals.get(user_id)

    def set_latest_signal(self, user_id, signal):
        # Optional: call this from your strategy engine
        self.latest_signals[user_id] = signal 