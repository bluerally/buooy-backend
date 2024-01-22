from datetime import datetime, timedelta
from unittest.mock import patch, Mock
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

import pytest
from httpx import AsyncClient
from starlette import status

from common.dependencies import get_current_user
from users.auth import GoogleAuth
from users.models import User, UserToken


@pytest.mark.asyncio
async def test_get_social_login_redirect_url(client: AsyncClient) -> None:
    response = await client.get("/api/user/auth/redirect-url/google")
    assert response.status_code == status.HTTP_200_OK
    query_params = {
        "client_id": GoogleAuth.CLIENT_ID,
        "redirect_uri": GoogleAuth.REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
    }
    _redirect_url = f"{GoogleAuth.AUTHORIZATION_URL}?{urlencode(query_params)}"
    assert response.json()["data"]["redirect_url"] == _redirect_url


MOCKED_GOOGLE_USER_INFO = {
    "iss": "https://accounts.google.com",
    "azp": "some-client-id.apps.googleusercontent.com",
    "aud": "some-client-id.apps.googleusercontent.com",
    "sub": "some-unique-id",
    "email": "user@example.com",
    "email_verified": True,
    "at_hash": "some-hash",
    "name": "John Doe",
    "picture": "https://profile.image.url",
    "given_name": "John",
    "family_name": "Doe",
    "locale": "en",
    "iat": 1616161616,
    "exp": 1616165216,
}


@patch("users.auth.id_token.verify_oauth2_token", return_value=MOCKED_GOOGLE_USER_INFO)
@patch("httpx.AsyncClient.post")
@pytest.mark.asyncio
async def test_social_auth_google(
    mock_post: Mock, mock_verify: Mock, client: AsyncClient
) -> None:
    mock_post.return_value.json = lambda: {
        "access_token": "mock_access_token",
        "id_token": "mock_id_token",
        "expires_in": 3599,
        "token_type": "Bearer",
    }

    response = await client.get("/api/user/auth/google", params={"code": "testcode"})

    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT


@pytest.mark.asyncio
async def test_refresh_token_endpoint(client: AsyncClient) -> None:
    # 테스트 데이터 세팅
    user = await User.create(
        id=1,
        email="fakeemail@gmail.com",
        sns_id="some_sns_id",
        name="Test User",
        profile_image="path/to/image",
    )
    refresh_token = "test_refresh_token"
    await UserToken.create(
        user=user,
        refresh_token=refresh_token,
        token_type="Bearer",
        expires_at=datetime.now(ZoneInfo("UTC")) + timedelta(days=1),
    )

    # 의존성 오버라이드 설정
    from main import app

    app.dependency_overrides[get_current_user] = lambda: user

    # API 호출
    response = await client.post(
        "/api/user/auth/token/refresh", json={"refresh_token": refresh_token}
    )

    # 응답 검증
    assert response.status_code == status.HTTP_201_CREATED
    assert (
        await UserToken.get_or_none(
            user=user, refresh_token=refresh_token, is_active=True
        )
        is not None
    )

    # 오버라이드 초기화
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_success_logout(client: AsyncClient) -> None:
    user = await User.create(
        id=3,
        email="fakeemail2@gmail.com",
        sns_id="some_sns_id",
        name="Test User",
        profile_image="path/to/image",
    )
    refresh_token = "test_refresh_token"
    await UserToken.create(
        user=user,
        refresh_token=refresh_token,
        token_type="Bearer",
        expires_at=datetime.now(ZoneInfo("UTC")) + timedelta(days=1),
    )

    # 의존성 오버라이드 설정
    from main import app

    app.dependency_overrides[get_current_user] = lambda: user

    # API 호출
    response = await client.post("/api/user/auth/logout")

    # 응답 검증
    assert response.status_code == 200
    assert await UserToken.get_or_none(user=user, is_active=True) is None

    # 오버라이드 초기화
    app.dependency_overrides.clear()
