import pytest
from httpx import AsyncClient
from starlette import status

from common.dependencies import get_current_user
from users.models import User, Sport
from datetime import datetime, UTC, timedelta
from parties.models import (
    Party,
    PartyParticipant,
    ParticipationStatus,
    PartyComment,
    PartyLike,
)
from common.constants import FORMAT_YYYY_MM_DD_T_HH_MM_SS_TZ, NOTIFICATION_TYPE_PARTY
from notifications.models import Notification


@pytest.mark.asyncio
async def test_success_party_create(client: AsyncClient) -> None:
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
    assert response.status_code == status.HTTP_201_CREATED
    assert Party.get_or_none(title=request_data["title"]) is not None

    # 오버라이드 초기화
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_success_party_update(client: AsyncClient) -> None:
    user = await User.create(
        email="partyorg6@gmail.com",
        sns_id="some_sns_id",
        name="Party Organizer User",
        profile_image="https://path/to/image",
    )
    sport = await Sport.create(name="프리다이빙")

    party = await Party.create(
        title="Freediving Party",
        body="Freediving Party body",
        organizer_user=user,
        gather_at=datetime.now(UTC) + timedelta(days=2),
        due_at=datetime.now(UTC) + timedelta(days=1),
        participant_limit=5,
        participant_cost=200,
        sport=sport,
        notice="audwls624",
    )

    # 의존성 오버라이드 설정
    from main import app

    app.dependency_overrides[get_current_user] = lambda: user

    request_data = {
        "gather_at": "2024-02-03T08:30:00+09:00",
    }
    # API 호출
    response = await client.post(f"/api/party/{party.id}", json=request_data)
    updated_party = await Party.get_or_none(id=party.id)
    # 응답 검증
    assert response.status_code == status.HTTP_200_OK
    assert updated_party.gather_at == datetime.strptime(
        request_data["gather_at"], FORMAT_YYYY_MM_DD_T_HH_MM_SS_TZ
    )

    # 오버라이드 초기화
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_success_party_participate(client: AsyncClient) -> None:
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

    assert response.status_code == status.HTTP_201_CREATED
    assert (
        await PartyParticipant.get_or_none(
            party=test_party,
            participant_user=test_user,
            status=ParticipationStatus.PENDING,
        )
        is not None
    )
    assert (
        await Notification.filter(
            type=NOTIFICATION_TYPE_PARTY, related_id=test_party.id
        ).exists()
        is True
    )

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_organizer_accepts_participation(client: AsyncClient) -> None:
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
async def test_success_participant_cancel_participation(client: AsyncClient) -> None:
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


@pytest.mark.asyncio
async def test_get_party_details_success(client: AsyncClient) -> None:
    # 더미 데이터 생성
    organizer_user = await User.create(
        name="Organizer User", profile_image="http://example.com/image.jpg"
    )
    test_party = await Party.create(
        title="Test Party",
        body="Test Party body",
        organizer_user=organizer_user,
        gather_at=datetime.now(UTC) + timedelta(days=1),
        due_at=datetime.now(UTC) + timedelta(days=2),
        participant_limit=10,
        participant_cost=100,
        sport=await Sport.create(name="Freediving"),
    )
    approved_participant_user_1 = await User.create(
        name="Participated User 1", profile_image="http://example.com/image2.jpg"
    )
    approved_participant_user_2 = await User.create(
        name="Participated User 2", profile_image="http://example.com/image3.jpg"
    )
    approved_participant_user_3 = await User.create(
        name="Participated User 3", profile_image="http://example.com/image4.jpg"
    )

    pending_participant_user_1 = await User.create(
        name="Pending Participant User 1", profile_image="http://example.com/image5.jpg"
    )
    pending_participant_user_2 = await User.create(
        name="Pending Participant User 2", profile_image="http://example.com/image6.jpg"
    )
    await PartyParticipant.create(
        party=test_party,
        participant_user=approved_participant_user_1,
        status=ParticipationStatus.APPROVED,
    )
    await PartyParticipant.create(
        party=test_party,
        participant_user=approved_participant_user_2,
        status=ParticipationStatus.APPROVED,
    )
    await PartyParticipant.create(
        party=test_party,
        participant_user=approved_participant_user_3,
        status=ParticipationStatus.APPROVED,
    )
    await PartyParticipant.create(
        party=test_party,
        participant_user=pending_participant_user_1,
        status=ParticipationStatus.PENDING,
    )
    await PartyParticipant.create(
        party=test_party,
        participant_user=pending_participant_user_2,
        status=ParticipationStatus.PENDING,
    )

    # 의존성 오버라이드 설정
    from main import app

    app.dependency_overrides[get_current_user] = lambda: organizer_user

    # API 호출
    response = await client.get(f"/api/party/details/{test_party.id}")
    response_data = response.json()
    # 응답 검증
    assert response.status_code == 200
    assert response_data["sport_name"] == "Freediving"
    assert response_data["participants_info"] == "4/10"
    assert response_data["organizer_profile"]["name"] == "Organizer User"
    assert len(response_data["approved_participants"]) == 3
    assert len(response_data["pending_participants"]) == 2

    # 의존성 오버라이드 초기화
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_party_list_success(client: AsyncClient) -> None:
    # 더미 데이터 생성
    organizer_user_1 = await User.create(
        name="Organizer User 1", profile_image="http://example.com/image1.jpg"
    )
    organizer_user_2 = await User.create(
        name="Organizer User 2", profile_image="http://example.com/image2.jpg"
    )
    sport_1 = await Sport.create(name="Freediving")
    sport_2 = await Sport.create(name="Scuba Diving")

    await Party.create(
        title="Freediving Party",
        body="Freediving Party body",
        organizer_user=organizer_user_1,
        gather_at=datetime.now(UTC) + timedelta(days=3),
        due_at=datetime.now(UTC) + timedelta(days=4),
        participant_limit=5,
        participant_cost=200,
        sport=sport_1,
    )
    await Party.create(
        title="Scuba Diving Party",
        body="Scuba Diving Party body",
        organizer_user=organizer_user_2,
        gather_at=datetime.now(UTC) + timedelta(days=5),
        due_at=datetime.now(UTC) + timedelta(days=6),
        participant_limit=6,
        participant_cost=300,
        sport=sport_2,
    )

    # 의존성 오버라이드 설정
    from main import app

    app.dependency_overrides[get_current_user] = lambda: organizer_user_1

    # API 호출
    response = await client.get("/api/party/list")
    response_data = response.json()

    # 응답 검증
    assert response.status_code == 200
    assert len(response_data) == 2

    # 의존성 오버라이드 초기화
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_sports_list_success(client: AsyncClient) -> None:
    await Sport.create(name="프리다이빙")
    await Sport.create(name="스쿠버다이빙")
    await Sport.create(name="서핑")

    response = await client.get("/api/party/sports")
    sports_list = response.json()
    assert response.status_code == 200
    assert len(sports_list) == 3


@pytest.mark.asyncio
async def test_post_party_comment_success(client: AsyncClient) -> None:
    user = await User.create(
        email="commenter@example.com",
        sns_id="commenter_sns_id",
        name="Commenter",
        profile_image="https://path/to/image",
    )
    party = await Party.create(
        title="Test Party",
        body="Test Party Body",
        organizer_user=user,
    )

    from main import app

    app.dependency_overrides[get_current_user] = lambda: user

    comment_content = "This is a test comment."
    response = await client.post(
        f"/api/party/{party.id}/comment", json={"content": comment_content}
    )

    response_data = response.json()
    assert response_data["content"] == comment_content

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_party_comments_success(client: AsyncClient) -> None:
    user = await User.create(
        email="commenter@example.com",
        sns_id="commenter_sns_id",
        name="Commenter",
        profile_image="https://path/to/image",
    )
    party = await Party.create(
        title="Test Party",
        body="Test Party Body",
        organizer_user=user,
    )
    await PartyComment.create(
        commenter=user, party=party, content="This is a test comment 1."
    )
    await PartyComment.create(
        commenter=user, party=party, content="This is a test comment 2."
    )

    response = await client.get(f"/api/party/{party.id}/comment")
    response_data = response.json()
    assert len(response_data) == 2


@pytest.mark.asyncio
async def test_change_party_comment_success(client: AsyncClient) -> None:
    user = await User.create(
        email="commenter@example.com",
        sns_id="commenter_sns_id",
        name="Commenter",
        profile_image="https://path/to/image",
    )
    party = await Party.create(
        title="Test Party",
        body="Test Party Body",
        organizer_user=user,
    )
    comment = await PartyComment.create(
        commenter=user, party=party, content="This is a test comment 1."
    )
    new_comment_content = "Updated test comment."

    from main import app

    app.dependency_overrides[get_current_user] = lambda: user

    response = await client.put(
        f"/api/party/{party.id}/comment/{comment.id}",
        json={"content": new_comment_content},
    )

    response_data = response.json()
    assert response_data["content"] == new_comment_content

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_delete_party_comment_success(client: AsyncClient) -> None:
    user = await User.create(
        email="commenter@example.com",
        sns_id="commenter_sns_id",
        name="Commenter",
        profile_image="https://path/to/image",
    )
    party = await Party.create(
        title="Test Party",
        body="Test Party Body",
        organizer_user=user,
    )
    comment = await PartyComment.create(
        commenter=user, party=party, content="This is a test comment 1."
    )

    from main import app

    app.dependency_overrides[get_current_user] = lambda: user

    response = await client.delete(f"/api/party/{party.id}/comment/{comment.id}")
    deleted_comment = await PartyComment.get_or_none(id=comment.id)
    assert response.status_code == status.HTTP_200_OK
    assert deleted_comment.is_deleted is True

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_post_party_like_success(client: AsyncClient) -> None:
    organizer = await User.create(
        email="organizer@example.com",
        sns_id="organizer",
        name="organizer",
        profile_image="https://path/to/image",
    )

    user = await User.create(
        email="liker@example.com",
        sns_id="liker",
        name="liker",
        profile_image="https://path/to/image",
    )
    party = await Party.create(
        title="Test Party",
        body="Test Party Body",
        organizer_user=organizer,
    )

    from main import app

    app.dependency_overrides[get_current_user] = lambda: user

    response = await client.post(f"/api/party/like/{party.id}")

    assert response.status_code == status.HTTP_201_CREATED
    assert await PartyLike.filter(user=user, party=party).exists()

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_post_party_like_cancel_success(client: AsyncClient) -> None:
    organizer = await User.create(
        email="organizer@example.com",
        sns_id="organizer",
        name="organizer",
        profile_image="https://path/to/image",
    )

    user = await User.create(
        email="liker@example.com",
        sns_id="liker",
        name="liker",
        profile_image="https://path/to/image",
    )
    party = await Party.create(
        title="Test Party",
        body="Test Party Body",
        organizer_user=organizer,
    )

    await PartyLike.create(user=user, party=party)

    from main import app

    app.dependency_overrides[get_current_user] = lambda: user

    response = await client.delete(f"/api/party/like/{party.id}")

    assert response.status_code == status.HTTP_200_OK
    assert not await PartyLike.filter(user=user, party=party).exists()

    app.dependency_overrides.clear()
