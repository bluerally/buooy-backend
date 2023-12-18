from typing import Optional

from pydantic import BaseModel
from common.dtos import BaseResponse


class UserInfo(BaseModel):
    sns_id: str = ""
    name: str = ""
    email: str = ""
    profile_image: str = ""
    # iss: Optional[str] = None
    # sub: Optional[str] = None
    # aud: Optional[str] = None
    # iat: Optional[str] = None
    # exp: Optional[str] = None
    # email: Optional[str] = None
    # name: Optional[str] = None
    # picture: Optional[str] = None
    # given_name: Optional[str] = None
    # family_name: Optional[str] = None


class LoginResponseData(BaseModel):
    user_info: UserInfo
    access_token: str
    refresh_token: str


class RedirectUrlInfo(BaseModel):
    redirect_url: Optional[str] = ""


class SocialLoginRedirectResponse(BaseResponse):
    data: Optional[RedirectUrlInfo] = None


class SocialLoginCallbackResponse(BaseResponse):
    data: Optional[LoginResponseData] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str
