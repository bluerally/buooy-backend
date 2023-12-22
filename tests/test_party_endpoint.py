import pytest
from httpx import AsyncClient

from common.dependencies import get_current_user
from users.models import User, Sport


@pytest.mark.asyncio
async def test_success_party_create(client: AsyncClient):
    user = await User.create(
        email="partyorg6@gmail.com",
        sns_id="some_sns_id",
        name="Party Organizer User",
        profile_image="https://path/to/image",
    )
    sport = await Sport.create(name="프리다이빙")

    # 의존성 오버라이드 설정
    from main import app

    app.dependency_overrides[get_current_user] = lambda: user

    request_data = {
        "title": "test title",
        "body": "test body",
        "gather_at": "2023-12-27T17:13:40+09:00",
        "due_at": "2023-12-27T00:00:00+09:00",
        "place_id": 123314252353,
        "place_name": "딥스테이션",
        "address": "경기도 용인시 처인구 90길 90",
        "longitude": 34.12,
        "latitude": 55.123,
        "participant_limit": 4,
        "participant_cost": 66000,
        "sport_id": sport.id,
    }
    # API 호출
    response = await client.post("/api/party/", json=request_data)

    # 응답 검증
    assert response.status_code == 200
    print(response.json())

    # 오버라이드 초기화
    app.dependency_overrides.clear()
