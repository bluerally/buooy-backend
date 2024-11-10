from users.dtos import SportInfo
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from users.dtos import UserInfo


class SelfProfileResponse(BaseModel):
    id: int
    # id: Optional[int] = None
    name: str
    # name: Optional[str] = None
    email: EmailStr
    # email: Optional[EmailStr] = None
    introduction: Optional[str]
    # introduction: Optional[str] = None
    profile_image: Optional[str]
    # profile_image: Optional[str] = None
    interested_sports: Optional[List[SportInfo]]
    # interested_sports: Optional[List[SportInfo]] = None


class TokenInfo(BaseModel):
    access_token: str = ""
    refresh_token: str = ""


class LoginResponse(TokenInfo):
    user_info: UserInfo


class AccessTokenResponse(LoginResponse):
    is_new_user: bool


class RedirectUrlInfoResponse(BaseModel):
    redirect_url: str


class TestTokenInfo(TokenInfo):
    user_id: int


class UserPartyStatisticsResponse(BaseModel):
    created_count: int
    participated_count: int
    liked_count: int
