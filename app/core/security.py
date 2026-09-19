import hashlib
import secrets

def hash_password(password: str) -> str:
    """비밀번호 해싱 (솔트 + SHA-256)"""
    salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return f"{salt}:{h}"

def verify_password(stored_password: str, provided_password: str) -> bool:
    """비밀번호 검증"""
    if not stored_password or ":" not in stored_password:
        return False
    salt, h = stored_password.split(":", 1)
    test_h = hashlib.sha256((salt + provided_password).encode("utf-8")).hexdigest()
    return test_h == h
