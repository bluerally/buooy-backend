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


class MobileAuthRequest(BaseModel):
    """모바일 앱에서 소셜 로그인 후 토큰을 처리하기 위한 요청 모델"""

    token: str
    platform: str
    user_info: dict[str, Optional[str]]
