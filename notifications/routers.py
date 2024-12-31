from fastapi import APIRouter, Depends, HTTPException
from starlette import status
from common.config import logger
from common.dependencies import get_current_user
from common.logging_configs import LoggingAPIRoute
from common.mixpanel_constants import (
    MIXPANEL_EVENT_VIEW_NOTIFICATIONS,
    MIXPANEL_EVENT_READ_NOTIFICATIONS,
)
from common.utils import track_analytics
from notifications.dto import NotificationUnreadCountDto, NotificationListDto
from notifications.service import NotificationService
from users.dto.request import NotificationReadRequest
from users.models import User

notification_router = APIRouter(
    prefix="/api/notifications",
    route_class=LoggingAPIRoute,
)


@notification_router.get(
    "",
    response_model=NotificationListDto,
    status_code=status.HTTP_200_OK,
)
async def get_user_notifications(
    user: User = Depends(get_current_user),
    page: int = 1,
) -> NotificationListDto:
    service = NotificationService(user)
    notification_list = await service.get_user_notifications(page=page)
    # analytics 트래킹
    await track_analytics(event_name=MIXPANEL_EVENT_VIEW_NOTIFICATIONS, user_id=user.id)
    return notification_list


@notification_router.post(
    "/read", response_model=None, status_code=status.HTTP_201_CREATED
)
async def read_user_notifications(
    body: NotificationReadRequest, user: User = Depends(get_current_user)
) -> str:
    service = NotificationService(user)
    await service.mark_notifications_as_read(body.read_notification_list)
    # analytics 트래킹
    await track_analytics(event_name=MIXPANEL_EVENT_READ_NOTIFICATIONS, user_id=user.id)
    return "Notifications successfully read"


@notification_router.get(
    "/count",
    response_model=NotificationUnreadCountDto,
    status_code=status.HTTP_200_OK,
)
async def get_notification_count(
    user: User = Depends(get_current_user)
) -> NotificationUnreadCountDto:
    try:
        service = NotificationService(user)
        notification_count = (
            await service.get_unread_notification_count()
        )  # Use the updated method
        return NotificationUnreadCountDto(count=notification_count)
    except Exception as e:
        logger.error(f"[Notification]: Get Unread Count Error, msg: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
