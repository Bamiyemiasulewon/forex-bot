import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()
FERNET_KEY = os.getenv("FERNET_KEY")

# Get a Fernet encryption object using the loaded key.
def get_fernet():
    return Fernet(FERNET_KEY.encode())

# Encrypt a secret string using Fernet symmetric encryption.
def encrypt_secret(secret: str) -> str:
    return get_fernet().encrypt(secret.encode()).decode()

# Decrypt a Fernet-encrypted string back to plaintext.
def decrypt_secret(token: str) -> str:
    return get_fernet().decrypt(token.encode()).decode() 