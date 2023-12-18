from abc import ABC, abstractmethod
from os import getenv
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, status
from google.auth.transport import requests
from google.oauth2 import id_token


class SocialLogin(ABC):
    @abstractmethod
    async def get_login_redirect_url(self) -> str:
        pass

    @abstractmethod
    async def get_user_data(self, code: str):
        pass


class GoogleAuth(SocialLogin):
    AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    CLIENT_ID = getenv("GOOGLE_CLIENT_ID")
    CLIENT_SECRET = getenv("GOOGLE_CLIENT_SECRET")
    REDIRECT_URI = "http://localhost:8000/auth/callback/google"

    @staticmethod
    async def get_google_user_info(token: str):
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

    async def get_user_data(self, code: str):
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
                # id_info = id_token.verify_oauth2_token(
                #     token_response.json()["id_token"],
                #     requests.Request(),
                #     self.CLIENT_ID,
                # )
                response_content = await token_response.json()
                id_info = id_token.verify_oauth2_token(
                    response_content["id_token"],
                    requests.Request(),
                    self.CLIENT_ID,
                )
                return id_info
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
                )

    async def refresh_access_token(self, refresh_token: str):
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
    async def get_login_redirect_url(self):
        pass

    async def get_user_data(self, code: str):
        pass


class NaverAuth(SocialLogin):
    async def get_login_redirect_url(self):
        pass

    async def get_user_data(self, code: str):
        pass
