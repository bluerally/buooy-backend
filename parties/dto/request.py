from typing import Optional
from pydantic import BaseModel
from parties.models import ParticipationStatus


class PartyDetailRequest(BaseModel):
    title: str
    body: Optional[str] = None
    gather_at: str
    due_at: str
    place_id: int
    place_name: str
    address: str
    longitude: float
    latitude: float
    participant_limit: int = 2
    participant_cost: int = 0
    sport_id: int
    notice: Optional[str] = None


class PartyUpdateRequest(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    gather_at: Optional[str] = None
    due_at: Optional[str] = None
    place_id: Optional[int] = None
    place_name: Optional[str] = None
    address: Optional[str] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    participant_limit: Optional[int] = None
    participant_cost: Optional[int] = None
    sport_id: Optional[int] = None
    notice: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    new_status: ParticipationStatus


class PartyCommentPostRequest(BaseModel):
    content: str
