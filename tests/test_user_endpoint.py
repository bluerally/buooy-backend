from datetime import datetime, timedelta
from unittest.mock import patch, Mock, AsyncMock
from urllib.parse import urlencode
from zoneinfo import ZoneInfo
import io
import pytest
from httpx import AsyncClient
from starlette import status

from common.dependencies import get_current_user
from users.auth import GoogleAuth
from users.models import User, UserToken, Sport, UserInterestedSport
from parties.models import Party, PartyLike

# from common.config import AWS_S3_URL
from pytest import MonkeyPatch
from typing import Callable, Any, Coroutine


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
    assert response.json()["redirect_url"] == _redirect_url


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


@pytest.mark.asyncio
async def test_success_get_liked_parties(client: AsyncClient) -> None:
    sport = await Sport.create(name="Sport")
    user = await User.create(
        email="fakeemail2@gmail.com",
        sns_id="sns_id",
        name="Test User",
        profile_image="https://path/to/image",
    )
    organizer = await User.create(
        email="organizer@gmail.com",
        sns_id="organizer_sns_id",
        name="Test organizer",
        profile_image="https://path/to/image",
    )
    party_1 = await Party.create(
        title="Test Party",
        created_at=datetime.now(),
        due_at=datetime.now() + timedelta(days=3),
        gather_at=datetime.now() + timedelta(days=2),
        body="Test Party Body",
        organizer_user=organizer,
        sport=sport,
    )
    party_2 = await Party.create(
        title="Test Party2",
        body="Test Party Body",
        created_at=datetime.now(),
        due_at=datetime.now() + timedelta(days=3),
        gather_at=datetime.now() + timedelta(days=2),
        organizer_user=organizer,
        sport=sport,
    )
    await PartyLike.create(user=user, party=party_1)
    await PartyLike.create(user=user, party=party_2)

    # 의존성 오버라이드 설정
    from main import app

    app.dependency_overrides[get_current_user] = lambda: user

    # API 호출
    response = await client.get("/api/user/party/like")
    response_json = response.json()

    # 응답 검증
    assert response.status_code == 200
    assert len(response_json) == 2

    # 오버라이드 초기화
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_success_get_self_profile(client: AsyncClient) -> None:
    sport_1 = await Sport.create(name="Sport1")
    sport_2 = await Sport.create(name="Sport2")
    sport_3 = await Sport.create(name="Sport3")
    user = await User.create(
        email="fakeemail2@gmail.com",
        sns_id="sns_id",
        name="Test User",
        introduction="안녕하세요",
        profile_image="https://path/to/image",
    )
    await UserInterestedSport.create(user=user, sport=sport_1)
    await UserInterestedSport.create(user=user, sport=sport_2)
    await UserInterestedSport.create(user=user, sport=sport_3)

    # 의존성 오버라이드 설정
    from main import app

    app.dependency_overrides[get_current_user] = lambda: user

    # API 호출
    response = await client.get("/api/user/me")

    # 응답 검증
    assert response.status_code == 200

    # 오버라이드 초기화
    app.dependency_overrides.clear()


@pytest.fixture
def mock_s3_upload(monkeypatch: MonkeyPatch) -> Callable[[], Coroutine[Any, Any, str]]:
    async def mock_upload_file(*args: Any, **kwargs: Any) -> str:
        return "user1/profile-image/fakeimage.jpg"

    monkeypatch.setattr("users.services.s3_upload_file", mock_upload_file)
    return mock_upload_file


@pytest.mark.asyncio
async def test_update_self_profile(
    client: AsyncClient, mock_s3_upload: AsyncMock
) -> None:
    # 유저와 관심 스포츠 생성
    user = await User.create(
        email="user@example.com",
        name="Test User",
        profile_image="user/1/original.jpg",
    )
    sport_1 = await Sport.create(name="Freediving")
    sport_2 = await Sport.create(name="Surfing")

    # 의존성 오버라이드 설정
    from main import app

    app.dependency_overrides[get_current_user] = lambda: user

    fake_image = io.BytesIO(b"test image")
    fake_image.seek(0)
    files = {
        "profile_image": ("mock_image.jpg", fake_image, "image/jpeg"),
    }

    # 업데이트할 프로필 정보
    profile_data = {
        "name": "Updated Name",
        "introduction": "Updated introduction",
        "interested_sports_ids": f"{sport_1.id},{sport_2.id}",
    }

    # API 호출
    response = await client.post("/api/user/me", data=profile_data, files=files)

    # 응답 검증
    assert response.status_code == status.HTTP_201_CREATED

    updated_user = await User.get(id=user.id)
    assert updated_user.name == "Updated Name"
    assert (
        updated_user.profile_image == "user1/profile-image/fakeimage.jpg"
    )  # Mock에서 반환된 URL
    interested_sports = await UserInterestedSport.filter(user=user).all()
    assert len(interested_sports) == 2

    # 오버라이드 초기화
    app.dependency_overrides.clear()
