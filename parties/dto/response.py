from pydantic import BaseModel
from parties.models import ParticipationStatus


class PartyParticipantStatusChangeResponse(BaseModel):
    participation_id: int
    status: ParticipationStatus
