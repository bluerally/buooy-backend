from typing import Optional, List
from pydantic import BaseModel
from parties.models import ParticipationStatus
from users.dtos import UserSimpleProfile


class RefreshTokenRequest(BaseModel):
    new_status: ParticipationStatus


class PartyInfo(BaseModel):
    id: int
    title: str
    sport_name: str
    gather_date: str
    gather_time: str
    price: int
    body: str
    organizer_profile: UserSimpleProfile
    posted_date: str
    is_active: bool


class ParticipantProfile(UserSimpleProfile):
    participation_id: Optional[int] = None
    is_organizer: bool = False


class PartyListDetail(PartyInfo):
    participants_info: str
    is_user_organizer: bool = False
    place_name: str
    place_id: Optional[int]
    address: str
    longitude: float
    latitude: float


class PartyDetail(PartyInfo):
    max_participants: int
    current_participants: int
    is_user_organizer: bool = False
    pending_participants: Optional[List[ParticipantProfile]] = None
    approved_participants: Optional[List[ParticipantProfile]] = None
    notice: Optional[str] = None
    place_name: str
    place_id: Optional[int]
    address: str
    longitude: float
    latitude: float


class PartyUpdateInfo(PartyInfo):
    updated_at: str
    notice: Optional[str] = None


class PartyCommentDetail(BaseModel):
    id: int
    commenter_profile: UserSimpleProfile
    posted_date: str
    content: str
    is_writer: Optional[bool] = None
