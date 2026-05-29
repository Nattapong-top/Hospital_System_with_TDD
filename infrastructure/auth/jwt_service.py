# infrastructure/auth/jwt_service.py
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from fastapi import HTTPException

from core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/staff/login")


def create_access_token(data: dict) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload.update({"exp": expire, "jti": uuid.uuid4().hex, "type": "access"})

    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(data: dict) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.refresh_token_expire_minutes
    )
    payload.update({"exp": expire, "jti": uuid.uuid4().hex, "type": "refresh"})

    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


def decode_refresh_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        if payload.get("type") != "refresh":
            return None
        return payload
    except JWTError:
        return None


def get_current_staff(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if not payload:

        raise HTTPException(
            status_code=401,
            detail="Token ไม่ถูกต้องหรือหมดอายุแล้ว กรุณา login ใหม่ออีกครั้ง",
        )
    return payload
