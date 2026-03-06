from __future__ import annotations
import hashlib, os, hmac, base64

def hash_password(password: str, salt: bytes | None = None) -> str:
    if salt is None:
        salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return base64.b64encode(salt).decode() + "$" + base64.b64encode(dk).decode()

def verify_password(password: str, stored: str) -> bool:
    try:
        salt_b64, dk_b64 = stored.split("$", 1)
        salt = base64.b64decode(salt_b64.encode())
        dk_expected = base64.b64decode(dk_b64.encode())
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
        return hmac.compare_digest(dk, dk_expected)
    except Exception:
        return False
