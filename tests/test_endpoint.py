import pytest
from httpx import AsyncClient
from users.auth import GoogleAuth
from urllib.parse import urlencode
from starlette import status
from unittest.mock import patch, AsyncMock
from users.models import User, UserToken
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


@pytest.mark.asyncio
async def test_create_test_endpoint(client):
    response = await client.get("/test")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_social_login_redirect_url(client: AsyncClient):
    response = await client.get(
        "/api/user/auth/redirect", params={"platform": "google"}
    )
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
async def test_social_auth_callback(mock_post, mock_verify, client: AsyncClient):
    mock_post.return_value.json = AsyncMock(
        return_value={
            "access_token": "mock_access_token",
            "id_token": "mock_id_token",
            "expires_in": 3599,
            "token_type": "Bearer",
        }
    )

    response = await client.get(
        "/api/user/auth/callback", params={"platform": "google", "code": "testcode"}
    )

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_refresh_token_endpoint(client: AsyncClient):
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
    response = await client.post(
        "/api/user/auth/token/refresh", json={"refresh_token": refresh_token}
    )

    assert response.status_code == status.HTTP_200_OK
    assert (
        await UserToken.get_or_none(
            user=user, refresh_token=refresh_token, is_active=True
        )
        is None
    )
