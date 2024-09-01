from pydantic import BaseModel
from typing import Optional


class RedirectUrlInfoResponse(BaseModel):
    redirect_url: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class AccessTokenRequest(BaseModel):
    user_uid: str


class NotificationReadRequest(BaseModel):
    read_notification_list: list[int]


class UserProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    introduction: Optional[str] = None
    interested_sports_ids: Optional[list[int]] = None
