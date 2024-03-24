from users.dtos import SportInfo
from pydantic import BaseModel, EmailStr
from typing import List
from users.dtos import UserInfo


class SelfProfileResponse(BaseModel):
    id: int
    # id: Optional[int] = None
    name: str
    # name: Optional[str] = None
    email: EmailStr
    # email: Optional[EmailStr] = None
    introduction: str
    # introduction: Optional[str] = None
    profile_image: str
    # profile_image: Optional[str] = None
    interested_sports: List[SportInfo]
    # interested_sports: Optional[List[SportInfo]] = None


class LoginResponse(BaseModel):
    user_info: UserInfo
    access_token: str = ""
    refresh_token: str = ""


class AccessTokenResponse(LoginResponse):
    is_new_user: bool


class RedirectUrlInfoResponse(BaseModel):
    redirect_url: str
