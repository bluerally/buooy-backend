from typing import Optional

from pydantic import BaseModel
from common.dtos import BaseResponse


class UserInfo(BaseModel):
    sns_id: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    profile_image: Optional[str] = None
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


class UserSimpleProfile(BaseModel):
    user_id: int
    profile_picture: str
    name: str


class LoginResponseData(BaseModel):
    user_info: UserInfo
    access_token: str = ""
    refresh_token: str = ""


class AccessTokenResponse(LoginResponseData):
    is_new_user: bool


class RedirectUrlInfo(BaseModel):
    redirect_url: Optional[str] = ""
    state: Optional[str] = ""


class SocialLoginRedirectResponse(BaseResponse):
    data: Optional[RedirectUrlInfo] = None


class SocialLoginTokenResponse(BaseResponse):
    data: Optional[LoginResponseData] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class AccessTokenRequest(BaseModel):
    user_uid: str
