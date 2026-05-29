# infrastructure/auth/jwt_service.py
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
    payload["exp"] = expire
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
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
