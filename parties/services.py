from parties.models import Party, PartyParticipant, ParticipationStatus
from users.models import User
from datetime import datetime, UTC
from parties.dtos import PartyDetailResponse
from users.dtos import UserSimpleProfile
from common.constants import (
    FORMAT_YYYY_d_MM_d_DD__HH_MM,
    FORMAT_YYYY_d_MM_d_DD,
    FORMAT_HH_MM,
)


class PartyParticipateService:
    def __init__(self, party: Party, user: User) -> None:
        self.party = party
        self.user = user

    @classmethod
    async def create(cls, party_id: int, user: User) -> "PartyParticipateService":
        party = await Party.get_or_none(id=party_id)
        if party is None:
            raise ValueError("Party Does Not Exist")
        if not party.is_active:
            raise ValueError("Party is not Active")
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


class PartyDetailService:
    """파티 상세 정보 service"""

    def __init__(self, party: Party) -> None:
        self.party = party

    @classmethod
    async def create(cls, party_id: int) -> "PartyDetailService":
        party = (
            await Party.get_or_none(id=party_id)
            .select_related("sport", "organizer_user")
            .prefetch_related("participants")
        )
        if party is None:
            raise ValueError("Party Does Not Exist")
        return cls(party)

    async def get_party_details(self, user: User) -> PartyDetailResponse:
        # 필요한 데이터를 가져와서 파싱합니다.
        participants = (
            await PartyParticipant.filter(party=self.party)
            .select_related("participant_user")
            .all()
        )

        approved_participants = [
            UserSimpleProfile(
                profile_picture=p.participant_user.profile_image,
                name=p.participant_user.name,
                user_id=p.participant_user_id,
            )
            for p in participants
            if p.status == ParticipationStatus.APPROVED
        ]

        pending_participants = [
            UserSimpleProfile(
                profile_picture=p.participant_user.profile_image,
                name=p.participant_user.name,
                user_id=p.participant_user_id,
                # application_date=p.created_at.strftime(FORMAT_YYYY_d_MM_d_DD)
            )
            for p in participants
            if p.status == ParticipationStatus.PENDING
        ]

        participants_info = (
            f"{len(approved_participants)}/{self.party.participant_limit}"
        )

        return PartyDetailResponse(
            sport_name=self.party.sport.name,
            gather_date=self.party.gather_at.strftime(FORMAT_YYYY_d_MM_d_DD),
            gather_time=self.party.gather_at.strftime(FORMAT_HH_MM),
            participants_info=participants_info,
            due_date=self.party.due_at.strftime(FORMAT_YYYY_d_MM_d_DD__HH_MM),
            price=self.party.participant_cost,
            body=self.party.body,
            organizer_profile=UserSimpleProfile(
                profile_picture=self.party.organizer_user.profile_image,
                name=self.party.organizer_user.name,
                user_id=self.party.organizer_user_id,
            ),
            posted_date=self.party.created_at.strftime(FORMAT_YYYY_d_MM_d_DD__HH_MM),
            is_user_organizer=user.id == self.party.organizer_user_id
            if user
            else False,
            pending_participants=pending_participants,
            approved_participants=approved_participants,
        )
