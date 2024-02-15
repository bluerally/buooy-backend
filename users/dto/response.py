from users.dtos import LoginResponseData
from pydantic import BaseModel
from typing import List


class AccessTokenResponse(LoginResponseData):
    is_new_user: bool


class SelfProfileResponse(BaseModel):
    id: int
    name: str
    email: str
    introduction: str
    interested_sports: List[str]
