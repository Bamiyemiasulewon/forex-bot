import sqlite3
from cryptography.fernet import Fernet
import os

class SimpleCredentialManager:
    def __init__(self, db_path="credentials.db", fernet_key=None):
        self.db_path = db_path
        self.fernet_key = fernet_key or os.environ.get("FERNET_KEY")
        if not self.fernet_key:
            raise ValueError("FERNET_KEY environment variable not set!")
        self.fernet = Fernet(self.fernet_key)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS credentials (
                    user_id INTEGER PRIMARY KEY,
                    login TEXT NOT NULL,
                    password TEXT NOT NULL,
                    server TEXT NOT NULL
                )
            """)

    def add_or_update_credentials(self, user_id, login, password, server):
        enc_login = self.fernet.encrypt(login.encode()).decode()
        enc_password = self.fernet.encrypt(password.encode()).decode()
        enc_server = self.fernet.encrypt(server.encode()).decode()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO credentials (user_id, login, password, server)
                VALUES (?, ?, ?, ?)
            """, (user_id, enc_login, enc_password, enc_server))

    def get_credentials(self, user_id):
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT login, password, server FROM credentials WHERE user_id=?", (user_id,)).fetchone()
            if row:
                login = self.fernet.decrypt(row[0].encode()).decode()
                password = self.fernet.decrypt(row[1].encode()).decode()
                server = self.fernet.decrypt(row[2].encode()).decode()
                return login, password, server
            return None

    def delete_credentials(self, user_id):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM credentials WHERE user_id=?", (user_id,)) 