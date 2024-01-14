from abc import ABC, abstractmethod
from os import getenv
from typing import Any
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, status
from google.auth.transport import requests
from google.oauth2 import id_token

from common.constants import (
    AUTH_PLATFORM_GOOGLE,
    AUTH_PLATFORM_KAKAO,
    AUTH_PLATFORM_NAVER,
)
from users.dtos import UserInfo
from users.utils import validate_kakao_id_token


class SocialLogin(ABC):
    @abstractmethod
    async def get_login_redirect_url(self) -> str:
        pass

    @abstractmethod
    async def get_user_data(self, code: str) -> Any:
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
                return UserInfo(
                    sns_id=id_info.get("sub"),
                    email=id_info.get("email"),
                    name=id_info.get("name"),
                    profile_image=id_info.get("picture"),
                )
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
            return UserInfo(
                sns_id=decoded_id_token.get("sub"),
                email=decoded_id_token.get("email"),
                name=decoded_id_token.get("nickname"),
                profile_image=decoded_id_token.get("picture"),
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )


class NaverAuth(SocialLogin):
    AUTHORIZATION_URL = "https://nid.naver.com/oauth2.0/authorize"
    TOKEN_URL = "https://nid.naver.com/oauth2.0/token"
    CLIENT_ID = getenv("NAVER_CLIENT_ID")
    CLIENT_SECRET = getenv("NAVER_CLIENT_SECRET")
    REDIRECT_URI = (
        getenv("REDIRECT_URI", default="http://localhost:8000/api/user/auth")
        + f"/{AUTH_PLATFORM_NAVER}"
    )
    USER_PROFILE_URL = "https://openapi.naver.com/v1/nid/me"

    def __init__(self, state: str) -> None:
        self.state = state

    async def get_login_redirect_url(self) -> str:
        query_params = {
            "client_id": self.CLIENT_ID,
            "redirect_uri": self.REDIRECT_URI,
            "response_type": "code",
            "state": self.state,
        }
        return f"{self.AUTHORIZATION_URL}?{urlencode(query_params)}"

    async def get_user_data(self, code: str) -> Any:
        data = {
            "code": code,
            "client_id": self.CLIENT_ID,
            "client_secret": self.CLIENT_SECRET,
            "grant_type": "authorization_code",
            "state": self.state,
        }
        async with httpx.AsyncClient() as client:
            try:
                token_response = await client.post(self.TOKEN_URL, data=data)
                token_response.raise_for_status()
                response_content = token_response.json()
                access_token = response_content["access_token"]
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
                # 프로필 정보 요청
                headers = {"Authorization": f"Bearer {access_token}"}
                profile_response = await client.get(
                    self.USER_PROFILE_URL, headers=headers
                )
                profile_response.raise_for_status()
                profile_content = profile_response.json()

                # 사용자 정보 추출
                if profile_content.get("resultcode") != "00":
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Failed to retrieve user profile",
                    )

                user_info = profile_content.get("response", {})
                return UserInfo(
                    sns_id=user_info.get("id"),
                    email=user_info.get("email"),
                    name=user_info.get("name"),
                    profile_image=user_info.get("profile_image"),
                )
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
                )
