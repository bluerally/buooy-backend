import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict
from fastapi import HTTPException
from zoneinfo import ZoneInfo
from common.config import SECRET_KEY, ALGORITHM


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
