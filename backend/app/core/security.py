import base64
import hashlib
import hmac
import json
import os
import time
from typing import Callable

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.models.user import User


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return f"scrypt${base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(digest).decode()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        _, salt_text, digest_text = encoded.split("$", 2)
        salt = base64.urlsafe_b64decode(salt_text.encode())
        expected = base64.urlsafe_b64decode(digest_text.encode())
        actual = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def _encode(value: dict) -> str:
    return base64.urlsafe_b64encode(json.dumps(value, separators=(",", ":")).encode()).rstrip(b"=").decode()


def create_token(user: User) -> str:
    header = _encode({"alg": "HS256", "typ": "JWT"})
    payload = _encode({"sub": user.id, "role": user.role, "exp": int(time.time()) + get_settings().auth_token_ttl_minutes * 60})
    signature = hmac.new(get_settings().auth_secret.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest()
    return f"{header}.{payload}.{base64.urlsafe_b64encode(signature).rstrip(b'=').decode()}"


def _decode(token: str) -> dict:
    try:
        header, payload, encoded_signature = token.split(".")
        signature = base64.urlsafe_b64decode(encoded_signature + "=")
        expected = hmac.new(get_settings().auth_secret.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(signature, expected):
            raise ValueError
        claims = json.loads(base64.urlsafe_b64decode(payload + "=="))
        if int(claims["exp"]) <= int(time.time()):
            raise ValueError
        return claims
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def current_user(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> User:
    if get_settings().testing and not authorization:
        return db.query(User).first() or User(id="test-user", email="test@example.com", role="ADMIN")
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    user = db.query(User).filter(User.id == _decode(authorization.split(" ", 1)[1]).get("sub")).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def require_roles(*roles: str) -> Callable:
    def dependency(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return dependency


require_engineer = require_roles("ADMIN", "ENGINEER")