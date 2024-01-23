from pydantic import BaseModel
from parties.models import ParticipationStatus


class PartyParticipationStatusChangeResponse(BaseModel):
    participation_id: int
    status: ParticipationStatus


class PartyCreateResponse(BaseModel):
    party_id: int
