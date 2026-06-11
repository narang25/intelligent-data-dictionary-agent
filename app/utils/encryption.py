"""
AES-Fernet encryption utility for storing database credentials at rest.
Uses FERNET_KEY from environment; auto-generates one if missing.
"""
import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

_KEY = os.getenv("DB_ENCRYPTION_KEY")
if not _KEY:
    raise RuntimeError(
        "🚨 DB_ENCRYPTION_KEY environment variable is not set! "
        "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\" "
        "and add it to your .env file."
    )

_fernet = Fernet(_KEY.encode() if isinstance(_KEY, str) else _KEY)


def encrypt_value(plain: str) -> str:
    """Encrypt a plaintext string. Returns base64-encoded ciphertext."""
    return _fernet.encrypt(plain.encode()).decode()


def decrypt_value(cipher: str) -> str:
    """Decrypt a base64-encoded ciphertext string."""
    return _fernet.decrypt(cipher.encode()).decode()
