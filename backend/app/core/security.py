from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import get_settings

ALGORITHM = "HS256"


def hash_password(p: str) -> str:
    return bcrypt.hashpw(p.encode(), bcrypt.gensalt()).decode()


def verify_password(p: str, hashed: str) -> bool:
    return bcrypt.checkpw(p.encode(), hashed.encode())


def _encode(sub: int, kind: str, delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode({"sub": str(sub), "type": kind, "iat": now, "exp": now + delta}, get_settings().secret_key, algorithm=ALGORITHM)


def access_token(uid: int) -> str:
    return _encode(uid, "access", timedelta(minutes=get_settings().access_token_minutes))


def refresh_token(uid: int) -> str:
    return _encode(uid, "refresh", timedelta(days=get_settings().refresh_token_days))


def decode(token: str, kind: str) -> int:
    payload = jwt.decode(token, get_settings().secret_key, algorithms=[ALGORITHM])
    if payload.get("type") != kind:
        raise jwt.InvalidTokenError("wrong token type")
    return int(payload["sub"])
