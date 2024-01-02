from parties.models import Party, PartyParticipant, ParticipationStatus
from users.models import User
from datetime import datetime, UTC


class PartyParticipateService:
    def __init__(self, party: Party, user: User) -> None:
        self.party = party
        self.user = user

    @classmethod
    async def create(cls, party_id: int, user: User):
        party = await Party.get_or_none(id=party_id)
        if party is None:
            raise ValueError("Party Does Not Exist")
        return cls(party, user)

    async def participate(self) -> None:
        # 파티장 신청 불가
        if self.party.organizer_user_id == self.user.id:
            raise ValueError("Organizer can not participate")

        # 마감 시간이 지났는 지 확인
        if self.party.due_at < datetime.now(UTC):
            raise ValueError("Cannot participate after the due date.")

        # 해당 파티에 참여 신청 여부 확인.
        existing_participation = await PartyParticipant.get_or_none(
            participant_user=self.user, party=self.party
        )
        if existing_participation:
            raise ValueError("Already applied to the party.")

        await PartyParticipant.create(
            participant_user=self.user,
            party=self.party,
        )

    async def participant_change_participation_status(
        self, new_status: ParticipationStatus
    ) -> PartyParticipant:
        participation = await PartyParticipant.get_or_none(
            party=self.party, participant_user=self.user
        )
        if not participation:
            raise ValueError("Operation is Forbidden for the user.")

        if participation.participant_user_id == self.user.id:
            return await self._participant_updates_own_status(participation, new_status)
        raise ValueError("Operation is Forbidden for the user.")

    async def organizer_change_participation_status(
        self, participation_id: int, new_status: ParticipationStatus
    ) -> PartyParticipant:
        participation = await PartyParticipant.get_or_none(id=participation_id)
        is_party_organizer = self.party.organizer_user_id == self.user.id
        if not participation and not is_party_organizer:
            raise ValueError("Operation is Forbidden for the user.")

        if is_party_organizer:
            return await self._organizer_updates_participation(
                participation, new_status
            )

        raise ValueError("Operation is Forbidden for the user.")

    async def _organizer_updates_participation(
        self, participation: PartyParticipant, new_status: ParticipationStatus
    ) -> PartyParticipant:
        if new_status in (ParticipationStatus.APPROVED, ParticipationStatus.REJECTED):
            participation.status = new_status
            await participation.save()
        else:
            raise ValueError("Invalid status change requested by organizer.")
        return participation

    async def _participant_updates_own_status(
        self, participation: PartyParticipant, new_status: ParticipationStatus
    ) -> PartyParticipant:
        if new_status == ParticipationStatus.CANCELLED:
            participation.status = new_status
            await participation.save()
        else:
            raise ValueError("Participants can only cancel their own participation.")
        return participation
