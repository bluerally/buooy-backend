from pydantic import BaseModel


class RedirectUrlInfoResponse(BaseModel):
    redirect_url: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class AccessTokenRequest(BaseModel):
    user_uid: str


class NotificationReadRequest(BaseModel):
    read_notification_list: list[int]
