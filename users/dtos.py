from typing import Optional

from pydantic import BaseModel


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


class SportInfo(BaseModel):
    id: int
    name: str
