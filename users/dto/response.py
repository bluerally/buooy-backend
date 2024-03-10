from users.dtos import LoginResponseData, SportInfo
from pydantic import BaseModel, EmailStr
from typing import List


class AccessTokenResponse(LoginResponseData):
    is_new_user: bool


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
