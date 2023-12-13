from typing import Optional

from pydantic import BaseModel
from common.dtos import BaseResponse


class UserInfo(BaseModel):
    id: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    picture: Optional[str] = None
    locale: Optional[str] = None


class RedirectUrlInfo(BaseModel):
    redirect_url: Optional[str] = ""


class SocialLoginRedirectResponse(BaseResponse):
    data: Optional[RedirectUrlInfo] = None


class SocialLoginCallbackResponse(BaseResponse):
    data: Optional[UserInfo] = None
