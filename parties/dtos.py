from typing import Optional, List
from pydantic import BaseModel
from parties.models import ParticipationStatus
from users.dtos import UserSimpleProfile
from common.dtos import BaseResponse


class PartyCreateRequest(BaseModel):
    title: str = ""
    body: Optional[str] = None
    gather_at: str = ""
    due_at: str = ""
    place_id: int = 1
    place_name: str = ""
    address: str = ""
    longitude: float = 0
    latitude: float = 0
    participant_limit: int = 2
    participant_cost: int = 0
    sport_id: int = 1


class RefreshTokenRequest(BaseModel):
    new_status: ParticipationStatus


class PartyInfo(BaseModel):
    id: int
    title: str
    sport_name: str
    gather_date: str
    gather_time: str
    participants_info: str
    due_date: str
    price: int
    body: str
    organizer_profile: UserSimpleProfile
    posted_date: str


class ParticipantProfile(UserSimpleProfile):
    participation_id: int


class PartyListDetail(PartyInfo):
    is_user_organizer: bool = False


class PartyDetail(PartyInfo):
    is_user_organizer: bool = False
    pending_participants: Optional[List[ParticipantProfile]] = None
    approved_participants: Optional[List[ParticipantProfile]] = None


class PartyDetailResponse(BaseResponse):
    data: PartyDetail


class PartyListResponse(BaseResponse):
    data: List[PartyListDetail]
