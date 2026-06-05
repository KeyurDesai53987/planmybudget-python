import hashlib
import hmac
from datetime import datetime, timezone, timedelta
from typing import Optional
from jose import jwt, JWTError
from app.config import get_settings

settings = get_settings()


def hash_password(password: str) -> str:
    import bcrypt
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    import bcrypt
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        return None


def generate_api_key() -> tuple[str, str, str]:
    import uuid
    key = f"pmb_{uuid.uuid4().hex}"
    prefix = key[:12]
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    return key, prefix, key_hash


def verify_api_key(key: str, key_hash: str) -> bool:
    return hmac.compare_digest(hashlib.sha256(key.encode()).hexdigest(), key_hash)
