import json
import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Union, Any
from zoneinfo import ZoneInfo

import httpx
from fastapi import HTTPException
from jose import jwt, jwk
from jose.utils import base64url_decode

from users.models import UserToken, User
from datetime import UTC


def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> Any:
    to_encode = data.copy()
    _now = datetime.now(ZoneInfo("UTC"))
    if expires_delta:
        expire = _now + expires_delta
    else:
        expire = _now + timedelta(minutes=30)
    to_encode.update({"exp": expire})

    from common.config import SECRET_KEY, ALGORITHM

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_access_token(token: str) -> Union[Dict[str, Any], None]:
    try:
        from common.config import SECRET_KEY, ALGORITHM

        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return decoded_token if decoded_token else None
    except jwt.JWTError:
        raise HTTPException(status_code=403, detail="Could not validate credentials")


async def create_refresh_token(
    user: User, token_type: str = "Bearer", expires_in_days: int = 3
) -> Any:
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


async def validate_kakao_id_token(
    id_token: Union[str, None],
    client_id: Union[str, None],
    session_nonce: Optional[str] = None,
) -> Dict[str, Any]:
    decoded_id_token: Dict[str, Any] = {}
    if not id_token or not client_id:
        return decoded_id_token
    try:
        header, payload, signature = id_token.split(".")

        decoded_header = base64url_decode(header)
        header_data = json.loads(decoded_header)

        # Payload 에러가 나지 않을때만 유효성 검사
        try:
            decoded_payload = base64url_decode(payload)
            payload_data = json.loads(decoded_payload)

            if payload_data.get("iss") != "https://kauth.kakao.com":
                return decoded_id_token
            if payload_data.get("aud") != client_id:
                return decoded_id_token
            if payload_data.get("exp") < datetime.now(UTC).timestamp():
                return decoded_id_token
            if payload_data.get("nonce") != session_nonce:
                return decoded_id_token
        except Exception as e:
            logging.error(f"Payload processing error: {e}")
            pass

        async with httpx.AsyncClient() as client:
            jwks_response = await client.get(
                "https://kauth.kakao.com/.well-known/jwks.json"
            )
            jwks = jwks_response.json()

        public_key = None
        for jwk_key in jwks.get("keys", []):
            if jwk_key.get("kid") == header_data.get("kid"):
                public_key = jwk.construct(jwk_key)

        if not public_key:
            return decoded_id_token

        decoded_id_token = jwt.decode(
            id_token, public_key, algorithms=["RS256"], audience=client_id
        )
        return decoded_id_token
    except jwt.JWTError:
        return decoded_id_token
