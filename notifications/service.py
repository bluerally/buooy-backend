from typing import Optional, List, Sequence

from tortoise.expressions import Q

from common.constants import FORMAT_YYYY_MM_DD_T_HH_MM_SS_TZ
from notifications.dto import (
    NotificationDto,
    NotificationBaseDto,
)
from notifications.models import Notification, NotificationRead
from users.models import User


class NotificationService:
    def __init__(self, user: Optional[User] = None) -> None:
        self.user = user

    @staticmethod
    async def create_notifications(
        notifications_data: Sequence[NotificationBaseDto]
    ) -> None:
        """
        여러 알림을 데이터베이스에 한 번에 삽입합니다.
        :param notifications_data: 알림 데이터 딕셔너리의 리스트
        """
        notifications = [Notification(**data.dict()) for data in notifications_data]
        await Notification.bulk_create(notifications)

    async def mark_notifications_as_read(self, notification_ids: list[int]) -> None:
        read_notifications = [
            NotificationRead(user=self.user, notification_id=notification_id)
            for notification_id in notification_ids
        ]
        await NotificationRead.bulk_create(read_notifications)

    async def get_user_notifications(self) -> List[NotificationDto]:
        notifications_query = Notification.filter(
            Q(target_user=self.user) | Q(is_global=True)
        ).order_by("-id")

        read_notifications_ids = {
            nr.notification_id for nr in await NotificationRead.filter(user=self.user)
        }

        notifications = await notifications_query
        result = []
        for notification in notifications:
            result.append(
                NotificationDto(
                    id=notification.id,
                    created_at=notification.created_at.strftime(
                        FORMAT_YYYY_MM_DD_T_HH_MM_SS_TZ
                    ),
                    type=notification.type,
                    related_id=notification.related_id,
                    message=notification.message,
                    is_global=notification.is_global,
                    is_read=notification.id in read_notifications_ids,
                )
            )
        return result
