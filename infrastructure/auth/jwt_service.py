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


class RoleChecker:
    """
    คลาสสำหรับตรวจสอบสิทธิ์ (RBAC)
    รับรายชื่อ Role ที่อนุญาตให้ผ่านได้
    """

    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_staff: dict = Depends(get_current_staff)):
        # แกะ role ออกมาจาก Token ที่ get_current_staff อ่านไว้ให้
        user_role = current_staff.get("role")

        # ถ้า role ไม่อยู่ในรายชื่อที่อนุญาต ให้เตะออก 403 ทันที
        if user_role not in self.allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"ไม่มีสิทธิ์เข้าถึง (Requires {', '.join(self.allowed_roles)} role)",
            )

        return current_staff
