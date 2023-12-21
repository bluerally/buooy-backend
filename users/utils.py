import jwt
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict
from fastapi import HTTPException
from zoneinfo import ZoneInfo
from common.config import SECRET_KEY, ALGORITHM
from users.models import UserToken, User


def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    _now = datetime.now(ZoneInfo("UTC"))
    if expires_delta:
        expire = _now + expires_delta
    else:
        expire = _now + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_access_token(token: str) -> Dict:
    try:
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return decoded_token if decoded_token else None
    except jwt.PyJWTError:
        raise HTTPException(status_code=403, detail="Could not validate credentials")


async def create_refresh_token(user: User, token_type="Bearer", expires_in_days=3):
    refresh_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(ZoneInfo("UTC")) + timedelta(days=expires_in_days)
    await UserToken.create(
        user=user,
        refresh_token=refresh_token,
        token_type=token_type,
        expires_at=expires_at,
    )
    return refresh_token


async def is_active_refresh_token(user: User, refresh_token: str) -> bool:
    active_token_info = await UserToken.get_or_none(
        user=user,
        refresh_token=refresh_token,
        is_active=True,
    )
    if not active_token_info:
        return False

    expire_time = active_token_info.expires_at
    if expire_time < datetime.now(ZoneInfo("UTC")):
        active_token_info.is_active = False
        await active_token_info.save()
        return False
    return True
