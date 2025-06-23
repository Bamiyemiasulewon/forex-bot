import sqlite3
from cryptography.fernet import Fernet
import os

class CredentialManager:
    def __init__(self, db_path, key):
        self.db_path = db_path
        self.fernet = Fernet(key)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                mt5_login TEXT,
                mt5_password TEXT,
                mt5_server TEXT
            )''')
            conn.commit()

    def store_credentials(self, user_id, login, password, server):
        enc_login = self.fernet.encrypt(login.encode()).decode()
        enc_password = self.fernet.encrypt(password.encode()).decode()
        enc_server = self.fernet.encrypt(server.encode()).decode()
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''INSERT OR REPLACE INTO users (user_id, mt5_login, mt5_password, mt5_server)
                         VALUES (?, ?, ?, ?)''', (user_id, enc_login, enc_password, enc_server))
            conn.commit()

    def get_credentials(self, user_id):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('SELECT mt5_login, mt5_password, mt5_server FROM users WHERE user_id=?', (user_id,))
            row = c.fetchone()
            if row:
                return tuple(self.fernet.decrypt(x.encode()).decode() for x in row)
            return None

    def delete_credentials(self, user_id):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('DELETE FROM users WHERE user_id=?', (user_id,))
            conn.commit() 