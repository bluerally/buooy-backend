from pydantic import BaseModel
from typing import Optional, List


class NotificationBaseDto(BaseModel):
    type: str
    classification: Optional[str] = None
    related_id: Optional[int] = None
    message: str
    is_global: bool


class NotificationSpecificDto(NotificationBaseDto):
    target_user_id: int


class NotificationDto(NotificationBaseDto):
    id: int
    created_at: str
    is_read: bool


class NotificationReadDto(BaseModel):
    user_id: int
    read_at: str
    notification_id: int


class NotificationListDto(BaseModel):
    notifications: List[NotificationDto]
    total_pages: int
