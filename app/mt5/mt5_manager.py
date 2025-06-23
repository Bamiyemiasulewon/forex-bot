import MetaTrader5 as mt5
import threading

class MT5Manager:
    def __init__(self):
        self.sessions = {}
        self.lock = threading.Lock()

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