# infrastructure/auth/jwt_service.py
from datetime import datetime, timedelta, timezone

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

SECRET_KEY = "Hospital_System_Paa_Top_IT_Secret_Key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/staff/login")


def create_access_token(data: dict) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload["exp"] = expire
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


def get_current_staff(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if not payload:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=401,
            detail="Token ไม่ถูกต้องหรือหมดอายุแล้ว กรุณา login ใหม่ออีกครั้ง",
        )
    return payload
