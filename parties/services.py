from parties.models import Party, PartyParticipant, ParticipationStatus
from users.models import User
from datetime import datetime, UTC
from parties.dtos import ParticipantProfile, PartyDetail, PartyListDetail
from users.dtos import UserSimpleProfile
from common.constants import (
    FORMAT_YYYY_d_MM_d_DD__HH_MM,
    FORMAT_YYYY_d_MM_d_DD,
    FORMAT_HH_MM,
)
from typing import List, Optional
from tortoise.expressions import Q
from fastapi import HTTPException, status


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

    async def get_party_details(self, user: User) -> PartyDetail:
        # 필요한 데이터를 가져와서 파싱합니다.
        participants = (
            await PartyParticipant.filter(party=self.party)
            .select_related("participant_user")
            .all()
        )

        approved_participants = [
            ParticipantProfile(
                profile_picture=p.participant_user.profile_image,
                name=p.participant_user.name,
                user_id=p.participant_user_id,
                participation_id=p.id,
            )
            for p in participants
            if p.status == ParticipationStatus.APPROVED
        ]

        pending_participants = [
            ParticipantProfile(
                profile_picture=p.participant_user.profile_image,
                name=p.participant_user.name,
                user_id=p.participant_user_id,
                participation_id=p.id,
                # application_date=p.created_at.strftime(FORMAT_YYYY_d_MM_d_DD)
            )
            for p in participants
            if p.status == ParticipationStatus.PENDING
        ]

        participants_info = (
            f"{len(approved_participants)}/{self.party.participant_limit}"
        )

        return PartyDetail(
            id=self.party.id,
            sport_name=self.party.sport.name,
            title=self.party.title,
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


class PartyListService:
    def __init__(self, user: Optional[User] = None) -> None:
        self.user = user

    async def get_party_list(
        self,
        sport_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        gather_date_min: Optional[str] = None,
        gather_date_max: Optional[str] = None,
        search_query: Optional[str] = None,
    ) -> List[PartyListDetail]:
        try:
            query = Q()

            if sport_id is not None:
                query &= Q(sport_id=sport_id)

            if is_active:
                query &= Q(is_active=True)

            if gather_date_min:
                query &= Q(
                    gather_at__gte=datetime.strptime(
                        gather_date_min, FORMAT_YYYY_d_MM_d_DD
                    )
                )

            if gather_date_max:
                query &= Q(
                    gather_at__lte=datetime.strptime(
                        gather_date_max, FORMAT_YYYY_d_MM_d_DD
                    )
                )

            if search_query:
                # TODO 쿼리 개선 필요
                query &= Q(title__icontains=search_query) | Q(
                    place_name__icontains=search_query
                )
                # query &= (Q(title__icontains=search_query) | Q(body__icontains=search_query) | Q(place_name__icontains=search_query))

            parties = (
                await Party.filter(query)
                .select_related("sport", "organizer_user")
                .prefetch_related("participants")
            )
            party_list = [await self._build_party_response(party) for party in parties]
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        return party_list

    async def _build_party_response(self, party: Party) -> PartyListDetail:
        approved_participants = await PartyParticipant.filter(
            party=party, status=ParticipationStatus.APPROVED
        ).count()
        return PartyListDetail(
            id=party.id,
            sport_name=party.sport.name,
            title=party.title,
            gather_date=party.gather_at.strftime(FORMAT_YYYY_d_MM_d_DD),
            gather_time=party.gather_at.strftime(FORMAT_HH_MM),
            participants_info=f"{approved_participants}/{party.participant_limit}",
            due_date=party.due_at.strftime(FORMAT_YYYY_d_MM_d_DD__HH_MM),
            price=party.participant_cost,
            body=party.body,
            organizer_profile=UserSimpleProfile(
                profile_picture=party.organizer_user.profile_image,
                name=party.organizer_user.name,
                user_id=party.organizer_user_id,
            ),
            posted_date=party.created_at.strftime(FORMAT_YYYY_d_MM_d_DD__HH_MM),
            is_user_organizer=self.user.id == party.organizer_user_id
            if self.user
            else False,
        )
