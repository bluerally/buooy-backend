import pytest
from httpx import AsyncClient

from common.dependencies import get_current_user
from users.models import User, Sport
from datetime import datetime, UTC, timedelta
from parties.models import Party, PartyParticipant, ParticipationStatus


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
    assert Party.get_or_none(title=request_data["title"]) is not None

    # 오버라이드 초기화
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_success_party_participate(client: AsyncClient):
    organizer_user = await User.create(name="Organizer User")
    test_party = await Party.create(
        title="Test Party",
        organizer_user=organizer_user,
        due_at=datetime.now(UTC) + timedelta(days=1),
    )
    test_user = await User.create(name="Test User")

    from main import app

    app.dependency_overrides[get_current_user] = lambda: test_user

    response = await client.post(f"/api/party/{test_party.id}/participate")

    assert response.status_code == 200
    assert (
        await PartyParticipant.get_or_none(
            party=test_party,
            participant_user=test_user,
            status=ParticipationStatus.PENDING,
        )
        is not None
    )

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_organizer_accepts_participation(client: AsyncClient):
    organizer_user = await User.create(name="Organizer User")
    participant_user = await User.create(name="Participant User")
    test_party = await Party.create(title="Test Party", organizer_user=organizer_user)

    # 참가 신청 생성
    participation = await PartyParticipant.create(
        party=test_party, participant_user=participant_user
    )

    from main import app

    # 파티장 권한으로 로그인
    app.dependency_overrides[get_current_user] = lambda: organizer_user

    # 참가 신청 수락
    response = await client.post(
        f"/api/party/organizer/{test_party.id}/status-change/{participation.id}",
        json={"new_status": ParticipationStatus.APPROVED.value},
    )
    assert response.status_code == 200
    changed_participation = await PartyParticipant.get_or_none(id=participation.id)
    assert changed_participation is not None
    assert changed_participation.status == ParticipationStatus.APPROVED


@pytest.mark.asyncio
async def test_success_participant_cancel_participation(client: AsyncClient):
    organizer_user = await User.create(name="Organizer User")
    participant_user = await User.create(name="Participant User")
    test_party = await Party.create(title="Test Party", organizer_user=organizer_user)

    # 참가 신청 생성
    participation = await PartyParticipant.create(
        party=test_party,
        participant_user=participant_user,
        status=ParticipationStatus.APPROVED,
    )

    from main import app

    app.dependency_overrides[get_current_user] = lambda: participant_user

    # 참가 신청 수락
    response = await client.post(
        f"/api/party/participants/{test_party.id}/status-change",
        json={"new_status": ParticipationStatus.CANCELLED.value},
    )
    assert response.status_code == 200
    changed_participation = await PartyParticipant.get_or_none(id=participation.id)
    assert changed_participation is not None
    assert changed_participation.status == ParticipationStatus.CANCELLED
