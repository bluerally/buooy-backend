from typing import Optional
from pydantic import BaseModel


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
