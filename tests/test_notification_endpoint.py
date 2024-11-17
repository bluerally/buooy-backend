from zoneinfo import ZoneInfo

import pytest
from httpx import AsyncClient
from starlette import status
from datetime import datetime, timedelta

from common.dependencies import get_current_user
from notifications.models import Notification, NotificationRead
from parties.models import Party
from users.models import User, Sport


@pytest.mark.asyncio
async def test_success_get_notifications(client: AsyncClient) -> None:
    user = await User.create(
        email="fakeemail2@gmail.com",
        sns_id="sns_id",
        name="Test User",
        profile_image="https://path/to/image",
    )
    sport = await Sport.create(name="Freediving")
    party = await Party.create(
        title="Freediving Party",
        body="Freediving Party body",
        organizer_user=user,
        gather_at=datetime.now(ZoneInfo("UTC")) + timedelta(days=2),
        participant_limit=5,
        participant_cost=200,
        sport=sport,
        notice="카톡 아이디는 audwls624",
    )
    await Notification.create(type="all", message="전체 공지 1", is_global=True)
    notice_2 = await Notification.create(
        type="party",
        related_id=party.id,
        message="파티 공지1",
        target_user=user,
        classification="details_updated",
    )
    notice_3 = await Notification.create(
        type="all", message="전체 공지 2", is_global=True
    )
    await Notification.create(
        type="party",
        related_id=party.id,
        message="파티 공지1",
        target_user=user,
        classification="details_updated",
    )

    await NotificationRead.create(user=user, notification=notice_2)
    await NotificationRead.create(user=user, notification=notice_3)

    # 의존성 오버라이드 설정
    from main import app

    app.dependency_overrides[get_current_user] = lambda: user
    # API 호출
    response = await client.get("/api/notifications")
    # 응답 검증
    assert response.status_code == 200
    assert response.json()["notifications"][0].get("related_id") == party.id
    assert response.json()["total_pages"] == 1


@pytest.mark.asyncio
async def test_success_read_notifications(client: AsyncClient) -> None:
    user = await User.create(
        email="fakeemail2@gmail.com",
        sns_id="sns_id",
        name="Test User",
        profile_image="https://path/to/image",
    )

    noti_1 = await Notification.create(
        type="all", message="전체 공지 1", is_global=True
    )
    noti_2 = await Notification.create(
        type="all", message="전체 공지 2", is_global=True
    )

    # 의존성 오버라이드 설정
    from main import app

    app.dependency_overrides[get_current_user] = lambda: user
    # API 호출
    response = await client.post(
        "/api/notifications/read",
        json={"read_notification_list": [noti_1.id, noti_2.id]},
    )
    # 응답 검증
    assert response.status_code == 201
    assert await NotificationRead.filter(notification=noti_1).exists()
    assert await NotificationRead.filter(notification=noti_2).exists()


@pytest.mark.asyncio
async def test_get_unread_notification_count(client: AsyncClient) -> None:
    # Create a test user
    user = await User.create(
        email="testuser@example.com",
        sns_id="test_sns_id",
        name="Test User",
        profile_image="https://path/to/image",
    )

    # Create global notifications
    global_notification_1 = await Notification.create(
        type="all", message="Global Notification 1", is_global=True
    )
    await Notification.create(
        type="all", message="Global Notification 2", is_global=True
    )

    # Create a user-specific notification
    await Notification.create(
        type="personal",
        message="User-specific Notification",
        is_global=False,
        target_user=user,
    )

    # Mark one global notification as read
    await NotificationRead.create(user=user, notification=global_notification_1)

    # Override dependency to use the test user
    from main import app

    app.dependency_overrides[get_current_user] = lambda: user

    # Call the notification count endpoint
    response = await client.get("/api/notifications/count")

    # Assert the response
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert response_json["count"] == 2  # Two unread notifications

    # Clean up dependency overrides
    app.dependency_overrides.clear()
