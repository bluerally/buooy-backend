from typing import Optional, List
from pydantic import BaseModel
from parties.models import ParticipationStatus
from users.dtos import UserSimpleProfile


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


class PartyDetailResponse(BaseModel):
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
    is_user_organizer: bool
    pending_participants: Optional[List[UserSimpleProfile]] = None
    approved_participants: Optional[List[UserSimpleProfile]] = None
