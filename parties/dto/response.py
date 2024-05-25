from pydantic import BaseModel
from typing import List, Optional
from parties.models import ParticipationStatus
from parties.dtos import PartyCommentDetail


class PartyParticipationStatusChangeResponse(BaseModel):
    participation_id: int
    status: ParticipationStatus


class PartyCreateResponse(BaseModel):
    party_id: int


class TestPartyCommentDetailResponse(BaseModel):
    comments: List[PartyCommentDetail]
    user_id: Optional[int] = None
