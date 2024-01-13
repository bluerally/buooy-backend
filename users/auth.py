from abc import ABC, abstractmethod
from os import getenv
from typing import Any, Dict
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, status
from google.auth.transport import requests
from google.oauth2 import id_token

from common.constants import AUTH_PLATFORM_GOOGLE, AUTH_PLATFORM_KAKAO
from users.dtos import UserInfo
from users.utils import validate_kakao_id_token


class SocialLogin(ABC):
    @abstractmethod
    async def get_login_redirect_url(self) -> str:
        pass

    @abstractmethod
    async def get_user_data(self, code: str) -> Any:
        pass

    @abstractmethod
    async def _extract_user_info_from_payload(
        self, payload: Dict[str, Any]
    ) -> UserInfo:
        pass


class GoogleAuth(SocialLogin):
    AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    CLIENT_ID = getenv("GOOGLE_CLIENT_ID")
    CLIENT_SECRET = getenv("GOOGLE_CLIENT_SECRET")
    REDIRECT_URI = (
        getenv("REDIRECT_URI", default="http://localhost:8000/api/user/auth")
        + f"/{AUTH_PLATFORM_GOOGLE}"
    )

    @staticmethod
    async def get_google_user_info(token: str) -> Any:
        try:
            id_info = id_token.verify_oauth2_token(
                token, requests.Request(), GoogleAuth.CLIENT_ID
            )
            return id_info
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

    async def get_login_redirect_url(self) -> str:
        query_params = {
            "client_id": self.CLIENT_ID,
            "redirect_uri": self.REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
        }
        return f"{self.AUTHORIZATION_URL}?{urlencode(query_params)}"

    async def _extract_user_info_from_payload(
        self, payload: Dict[str, Any]
    ) -> UserInfo:
        return UserInfo(
            sns_id=payload.get("sub"),
            email=payload.get("email"),
            name=payload.get("name"),
            profile_image=payload.get("picture"),
        )

    async def get_user_data(self, code: str) -> UserInfo:
        data = {
            "code": code,
            "client_id": self.CLIENT_ID,
            "client_secret": self.CLIENT_SECRET,
            "redirect_uri": self.REDIRECT_URI,
            "grant_type": "authorization_code",
        }
        async with httpx.AsyncClient() as client:
            try:
                token_response = await client.post(self.TOKEN_URL, data=data)
                token_response.raise_for_status()
            except httpx.RequestError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Request error: {str(e)}",
                )
            except httpx.HTTPStatusError as e:
                raise HTTPException(
                    status_code=e.response.status_code, detail=f"HTTP error: {str(e)}"
                )

            try:
                response_content = await token_response.json()
                id_info = id_token.verify_oauth2_token(
                    response_content["id_token"],
                    requests.Request(),
                    self.CLIENT_ID,
                )
                return await self._extract_user_info_from_payload(id_info)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
                )

    async def refresh_access_token(self, refresh_token: str) -> Any:
        data = {
            "client_id": self.CLIENT_ID,
            "client_secret": self.CLIENT_SECRET,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(self.TOKEN_URL, data=data)
            if response.status_code != status.HTTP_200_OK:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Failed to refresh access token",
                )
            return response.json()


class KakaoAuth(SocialLogin):
    AUTHORIZATION_URL = "https://kauth.kakao.com/oauth/authorize"
    TOKEN_URL = "https://kauth.kakao.com/oauth/token"
    CLIENT_ID = getenv("KAKAO_CLIENT_ID")
    CLIENT_SECRET = getenv("KAKAO_CLIENT_SECRET")
    REDIRECT_URI = (
        getenv("REDIRECT_URI", default="http://localhost:8000/api/user/auth")
        + f"/{AUTH_PLATFORM_KAKAO}"
    )

    def __init__(self, nonce: str) -> None:
        self.nonce = nonce

    async def get_login_redirect_url(self) -> str:
        query_params = {
            "client_id": self.CLIENT_ID,
            "redirect_uri": self.REDIRECT_URI,
            "response_type": "code",
            "scope": "openid,profile_image,account_email,profile_nickname ",
            "nonce": self.nonce,
            # "state": str(uuid.uuid4()),
        }
        return f"{self.AUTHORIZATION_URL}?{urlencode(query_params)}"

    async def _extract_user_info_from_payload(
        self, payload: Dict[str, Any]
    ) -> UserInfo:
        return UserInfo(
            sns_id=payload.get("sub"),
            email=payload.get("email"),
            name=payload.get("nickname"),
            profile_image=payload.get("picture"),
        )

    async def get_user_data(self, code: str) -> UserInfo:
        data = {
            "code": code,
            "client_id": self.CLIENT_ID,
            "client_secret": self.CLIENT_SECRET,
            "redirect_uri": self.REDIRECT_URI,
            "grant_type": "authorization_code",
        }
        async with httpx.AsyncClient() as client:
            try:
                token_response = await client.post(self.TOKEN_URL, data=data)
                token_response.raise_for_status()
            except httpx.RequestError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Request error: {str(e)}",
                )
            except httpx.HTTPStatusError as e:
                raise HTTPException(
                    status_code=e.response.status_code, detail=f"HTTP error: {str(e)}"
                )

        try:
            response_content = token_response.json()
            id_token = response_content.get("id_token")

            decoded_id_token = await validate_kakao_id_token(
                id_token, self.CLIENT_ID, self.nonce
            )
            if not decoded_id_token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid ID token",
                )
            return await self._extract_user_info_from_payload(decoded_id_token)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )


class NaverAuth(SocialLogin):
    async def get_login_redirect_url(self) -> str:
        return ""

    async def get_user_data(self, code: str) -> Any:
        return ""
