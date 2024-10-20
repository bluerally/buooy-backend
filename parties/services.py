from typing import Any
from zoneinfo import ZoneInfo
from parties.models import (
    Party,
    PartyParticipant,
    ParticipationStatus,
    PartyComment,
    PartyLike,
)
from users.models import User
from datetime import datetime, UTC, timedelta
from parties.dtos import (
    ParticipantProfile,
    PartyDetail,
    PartyListDetail,
    PartyCommentDetail,
    PartyUpdateInfo,
)
from users.dtos import UserSimpleProfile
from common.constants import (
    FORMAT_HH_MM,
    FORMAT_YYYY_MM_DD,
    FORMAT_YYYY_MM_DD_T_HH_MM_SS_TZ,
    NOTIFICATION_TYPE_PARTY,
    NOTIFICATION_CLASSIFY_PARTY_COMMENT,
    NOTIFICATION_CLASSIFY_PARTY_DETAILS_UPDATED,
    NOTIFICATION_CLASSIFY_PARTY_PARTICIPATION_APPLY,
    NOTIFICATION_CLASSIFY_PARTY_PARTICIPATION_APPROVED,
    NOTIFICATION_CLASSIFY_PARTY_PARTICIPATION_REJECTED,
    NOTIFICATION_CLASSIFY_PARTY_PARTICIPATION_CANCELED,
    NOTIFICATION_CLASSIFY_PARTY_PARTICIPATION_CLOSED,
)
from typing import List, Optional, Union
from tortoise.expressions import Q
from fastapi import HTTPException, status
from parties.dto.request import PartyUpdateRequest
from notifications.service import NotificationService
from notifications.dto import NotificationSpecificDto
from notifications.message_format import (
    MESSAGE_FORMAT_PARTY_PARTICIPATE,
    MESSAGE_FORMAT_PARTY_ACCEPTED,
    MESSAGE_FORMAT_PARTY_REJECTED,
    MESSAGE_FORMAT_PARTY_CANCELED,
    MESSAGE_FORMAT_PARTY_DETAILS_CHANGED,
    MESSAGE_FORMAT_PARTY_COMMENT_ADDED,
)
from common.config import TIME_ZONE, logger


class PartyParticipateService:
    def __init__(self, party: Party, user: User) -> None:
        self.party = party
        self.user = user

    def is_user_organizer(self) -> Any:
        return self.party.organizer_user_id == self.user.id

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
        if self.is_user_organizer():
            raise ValueError("Organizer can not participate")

        # 만남 시간이 지났는 지 확인
        if self.party.gather_at < datetime.now(UTC):
            raise ValueError("Cannot participate after the gather date.")

        # 해당 파티에 참여 신청 여부 확인.
        existing_participation = await PartyParticipant.get_or_none(
            participant_user=self.user, party=self.party
        )
        # TODO 취소된 신청인 경우 재신청 가능하게 만들 것
        if (
            existing_participation
            and existing_participation.status == ParticipationStatus.PENDING
        ):
            raise ValueError("Already applied to the party.")

        await PartyParticipant.create(
            participant_user=self.user,
            party=self.party,
        )

        # 파티장에게 알람 보내기
        notification_service = NotificationService(self.user)
        notification_info = NotificationSpecificDto(
            type=NOTIFICATION_TYPE_PARTY,
            classification=NOTIFICATION_CLASSIFY_PARTY_PARTICIPATION_APPLY,
            related_id=self.party.id,
            # 알람 메시지 생성
            message=MESSAGE_FORMAT_PARTY_PARTICIPATE.format(
                user=self.user.name, party=self.party.title
            ),
            is_global=False,
            target_user_id=self.party.organizer_user_id,
        )
        await notification_service.create_notifications([notification_info])

    async def participant_change_participation_status(
        self, new_status: ParticipationStatus
    ) -> PartyParticipant:
        participation = await PartyParticipant.get_or_none(
            party=self.party, participant_user=self.user
        ).select_related("participant_user")
        if not participation:
            raise ValueError("Operation is Forbidden for the user.")

        if participation.participant_user_id == self.user.id:
            return await self._participant_updates_own_status(participation, new_status)
        raise ValueError("Operation is Forbidden for the user.")

    async def organizer_change_participation_status(
        self, participation_id: int, new_status: ParticipationStatus
    ) -> PartyParticipant:
        participation = await PartyParticipant.get_or_none(
            id=participation_id
        ).select_related("participant_user")
        if participation is None:
            raise ValueError("Invalid Participation ID")
        if not self.is_user_organizer():
            raise PermissionError("Operation is Forbidden for the user.")

        if self.is_user_organizer():
            return await self._organizer_updates_participation(
                participation, new_status
            )

        raise ValueError("Operation is Forbidden for the user.")

    async def _organizer_updates_participation(
        self, participation: PartyParticipant, new_status: ParticipationStatus
    ) -> PartyParticipant:
        if new_status not in (
            ParticipationStatus.APPROVED,
            ParticipationStatus.REJECTED,
        ):
            raise ValueError("Invalid status change requested by organizer.")

        participation.status = new_status
        await participation.save()

        # 파티원에게 알람 보내기
        notification_service = NotificationService(self.user)
        # 알람 메시지 생성
        message = (
            MESSAGE_FORMAT_PARTY_ACCEPTED
            if new_status == ParticipationStatus.APPROVED
            else MESSAGE_FORMAT_PARTY_REJECTED
        )  # TODO 구조 변경 필요
        message = message.format(party=self.party.title)
        notification_info = NotificationSpecificDto(
            type=NOTIFICATION_TYPE_PARTY,
            classification=NOTIFICATION_CLASSIFY_PARTY_PARTICIPATION_APPROVED
            if new_status == ParticipationStatus.APPROVED
            else NOTIFICATION_CLASSIFY_PARTY_PARTICIPATION_REJECTED,
            related_id=self.party.id,
            message=message,
            is_global=False,
            target_user_id=participation.participant_user_id,
        )
        await notification_service.create_notifications([notification_info])

        return participation

    async def _participant_updates_own_status(
        self, participation: PartyParticipant, new_status: ParticipationStatus
    ) -> PartyParticipant:
        if new_status != ParticipationStatus.CANCELLED:
            raise ValueError("Participants can only cancel their own participation.")

        participation.status = new_status
        await participation.save()

        # 파티장에게 알람 보내기
        notification_service = NotificationService()
        message = MESSAGE_FORMAT_PARTY_CANCELED.format(
            user=participation.participant_user.name, party=self.party.title
        )
        notification_info = NotificationSpecificDto(
            type=NOTIFICATION_TYPE_PARTY,
            classification=NOTIFICATION_CLASSIFY_PARTY_PARTICIPATION_CANCELED,
            related_id=self.party.id,
            message=message,
            is_global=False,
            target_user_id=self.party.organizer_user_id,
        )
        await notification_service.create_notifications([notification_info])

        return participation

    async def set_party_deactivated(self, set_to_deactivate: bool = True) -> None:
        if not self.is_user_organizer():
            raise ValueError("Only Party of Organizer can set party status")
        if set_to_deactivate:
            self.party.is_active = False
        else:
            self.party.is_active = True
        await self.party.save()


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

        approved_participants = []
        pending_participants = []
        participants_id_list = []
        for participant in participants:
            if participant.status == ParticipationStatus.PENDING:
                pending_participants.append(
                    ParticipantProfile(
                        profile_picture=participant.participant_user.profile_image,
                        name=participant.participant_user.name,
                        user_id=participant.participant_user_id,
                        participation_id=participant.id,
                        # application_date=p.created_at.strftime(FORMAT_YYYY_d_MM_d_DD)
                    )
                )
            if participant.status == ParticipationStatus.APPROVED:
                approved_participants.append(
                    ParticipantProfile(
                        profile_picture=participant.participant_user.profile_image,
                        name=participant.participant_user.name,
                        user_id=participant.participant_user_id,
                        participation_id=participant.id,
                    )
                )
                participants_id_list.append(participant.participant_user.id)

        participants_info = (
            # 파티장 포함
            f"{len(approved_participants) + 1}/{self.party.participant_limit}"
        )

        return PartyDetail(
            id=self.party.id,
            sport_name=self.party.sport.name,
            title=self.party.title,
            gather_date=self.party.gather_at.strftime(FORMAT_YYYY_MM_DD),
            gather_time=self.party.gather_at.strftime(FORMAT_HH_MM),
            participants_info=participants_info,
            price=self.party.participant_cost,
            body=self.party.body,
            organizer_profile=UserSimpleProfile(
                profile_picture=self.party.organizer_user.profile_image,
                name=self.party.organizer_user.name,
                user_id=self.party.organizer_user_id,
            ),
            posted_date=self.party.created_at.strftime(FORMAT_YYYY_MM_DD_T_HH_MM_SS_TZ),
            is_user_organizer=user.id == self.party.organizer_user_id
            if user
            else False,
            pending_participants=pending_participants,
            approved_participants=approved_participants,
            is_active=self.party.is_active,
            notice=self.party.notice
            if user
            and (
                user.id in participants_id_list
                or user.id == self.party.organizer_user_id
            )
            else None,
            place_name=self.party.place_name,
            place_id=self.party.place_id,
            address=self.party.address,
            longitude=self.party.longitude,
            latitude=self.party.latitude,
        )

    async def update_party(
        self, user: User, update_info: PartyUpdateRequest
    ) -> PartyUpdateInfo:
        if self.party.organizer_user_id != user.id:
            raise PermissionError("user(user.id) is not party organizer")

        # 각 필드를 업데이트
        for field, value in update_info.__dict__.items():
            if value is not None and hasattr(self.party, field):
                if field == "gather_at":
                    try:
                        value = datetime.strptime(
                            value, FORMAT_YYYY_MM_DD_T_HH_MM_SS_TZ
                        )
                    except Exception as e:
                        raise ValueError(
                            f"field: {field}, format is in valid({FORMAT_YYYY_MM_DD_T_HH_MM_SS_TZ}), error: {e}"
                        )
                setattr(self.party, field, value)

        # 업데이트된 내용 저장
        await self.party.save()

        # 파티원들에게 알람 보내기
        notification_service = NotificationService()
        participant_list = await PartyParticipant.filter(
            party=self.party, status=ParticipationStatus.APPROVED
        ).all()
        message_list = []
        for participant in participant_list:
            message = MESSAGE_FORMAT_PARTY_DETAILS_CHANGED.format(
                party=self.party.title
            )
            notification_info = NotificationSpecificDto(
                type=NOTIFICATION_TYPE_PARTY,
                classification=NOTIFICATION_CLASSIFY_PARTY_DETAILS_UPDATED
                if self.party.is_active
                else NOTIFICATION_CLASSIFY_PARTY_PARTICIPATION_CLOSED,
                related_id=self.party.id,
                message=message,
                is_global=False,
                target_user_id=participant.participant_user_id,
            )
            message_list.append(notification_info)
        await notification_service.create_notifications(message_list)

        return PartyUpdateInfo(
            id=self.party.id,
            updated_at=self.party.updated_at.strftime(FORMAT_YYYY_MM_DD_T_HH_MM_SS_TZ),
            sport_name=self.party.sport.name,
            title=self.party.title,
            gather_date=self.party.gather_at.strftime(FORMAT_YYYY_MM_DD),
            gather_time=self.party.gather_at.strftime(FORMAT_HH_MM),
            price=self.party.participant_cost,
            body=self.party.body,
            organizer_profile=UserSimpleProfile(
                profile_picture=self.party.organizer_user.profile_image,
                name=self.party.organizer_user.name,
                user_id=self.party.organizer_user_id,
            ),
            posted_date=self.party.created_at.strftime(FORMAT_YYYY_MM_DD_T_HH_MM_SS_TZ),
            notice=self.party.notice,
            is_active=self.party.is_active,
        )


class PartyListService:
    def __init__(self, user: Optional[User] = None) -> None:
        self.user = user

    async def get_party_list(
        self,
        sport_id_list: Optional[List[int]] = None,
        is_active: Optional[bool] = None,
        gather_date_min: Optional[str] = None,
        gather_date_max: Optional[str] = None,
        search_query: Optional[str] = None,
        page: int = 1,
        page_size: int = 8,
    ) -> List[PartyListDetail]:
        try:
            query = Q()

            if sport_id_list is not None:
                query &= Q(sport_id__in=sport_id_list)

            if is_active:
                query &= Q(is_active=True)

            if gather_date_min:
                gather_at_min = datetime.strptime(gather_date_min, FORMAT_YYYY_MM_DD)
                gather_at_min = gather_at_min.replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                gather_at_min_with_tz = gather_at_min.replace(
                    tzinfo=ZoneInfo(TIME_ZONE)
                )
                query &= Q(gather_at__gte=gather_at_min_with_tz)

            if gather_date_max:
                gather_at_max = datetime.strptime(gather_date_max, FORMAT_YYYY_MM_DD)
                gather_at_max += timedelta(days=1)
                gather_at_max = gather_at_max.replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                gather_at_max_with_tz = gather_at_max.replace(
                    tzinfo=ZoneInfo(TIME_ZONE)
                )
                query &= Q(gather_at__lt=gather_at_max_with_tz)

            if search_query:
                # TODO 쿼리 개선 필요
                query &= Q(title__icontains=search_query) | Q(
                    place_name__icontains=search_query
                )
                # query &= (Q(title__icontains=search_query) | Q(body__icontains=search_query) | Q(place_name__icontains=search_query))

            # 페이징 계산
            offset = (page - 1) * page_size
            limit = page_size

            parties = (
                await Party.filter(query)
                .select_related("sport", "organizer_user")
                .prefetch_related("participants")
                .order_by("-id")
                .offset(offset)
                .limit(limit)
            )
            party_list = [await self._build_party_response(party) for party in parties]
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        return party_list

    async def get_self_organized_parties(
        self, page: int = 1, page_size: int = 10
    ) -> List[PartyListDetail]:
        try:
            offset = (page - 1) * page_size
            limit = page_size

            parties = (
                await Party.filter(organizer_user=self.user)
                .select_related("sport", "organizer_user")
                .prefetch_related("participants")
                .order_by("-id")
                .offset(offset)
                .limit(limit)
            )
            party_list = [await self._build_party_response(party) for party in parties]
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        return party_list

    async def get_participated_parties(
        self, page: int = 1, page_size: int = 10
    ) -> List[PartyListDetail]:
        try:
            offset = (page - 1) * page_size
            limit = page_size
            party_participates = (
                await PartyParticipant.filter(
                    participant_user=self.user,
                    status__in=[
                        ParticipationStatus.APPROVED,
                        ParticipationStatus.PENDING,
                    ],
                )
                .select_related(
                    "party", "party__sport", "participant_user", "party__organizer_user"
                )
                .order_by("-id")
                .offset(offset)
                .limit(limit)
            )
            party_list = [
                await self._build_party_response(party_participate.party)
                for party_participate in party_participates
            ]
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
            gather_date=party.gather_at.strftime(FORMAT_YYYY_MM_DD),
            gather_time=party.gather_at.strftime(FORMAT_HH_MM),
            participants_info=f"{approved_participants}/{party.participant_limit}",
            price=party.participant_cost,
            body=party.body,
            organizer_profile=UserSimpleProfile(
                profile_picture=party.organizer_user.profile_image,
                name=party.organizer_user.name,
                user_id=party.organizer_user_id,
            ),
            posted_date=party.created_at.strftime(FORMAT_YYYY_MM_DD_T_HH_MM_SS_TZ),
            is_user_organizer=self.user.id == party.organizer_user_id
            if self.user
            else False,
            is_active=party.is_active,
            place_name=party.place_name,
            place_id=party.place_id,
            address=party.address,
            longitude=party.longitude,
            latitude=party.latitude,
        )


class PartyCommentService:
    def __init__(self, party_id: int, user: Optional[Union[User, None]] = None) -> None:
        self.party_id = party_id
        self.user = user

    async def get_comments(self) -> List[PartyCommentDetail]:
        comments = await PartyComment.filter(
            party_id=self.party_id, is_deleted=False
        ).select_related("commenter")
        comments_list = [
            await self._build_party_comment(comment) for comment in comments
        ]
        return comments_list

    async def _build_party_comment(self, comment: PartyComment) -> PartyCommentDetail:
        return PartyCommentDetail(
            id=comment.id,
            commenter_profile=UserSimpleProfile(
                user_id=comment.commenter.id,
                name=comment.commenter.name,
                profile_picture=comment.commenter.profile_image,
            ),
            posted_date=comment.created_at.strftime(FORMAT_YYYY_MM_DD_T_HH_MM_SS_TZ),
            content=comment.content,
            is_writer=comment.commenter.id == self.user.id if self.user else False,
        )

    async def post_comment(self, content: Optional[str]) -> PartyCommentDetail:
        if not content:
            raise ValueError("Party comment must have content")
        try:
            comment = await PartyComment.create(
                party_id=self.party_id, commenter=self.user, content=content
            )

            # 파티원들에게 알람 보내기
            notification_service = NotificationService()
            party = await Party.get_or_none(id=self.party_id)
            participant_list = (
                await PartyParticipant.filter(
                    party_id=self.party_id,
                    status__in=[
                        ParticipationStatus.APPROVED,
                        ParticipationStatus.PENDING,
                    ],
                )
                .select_related("participant_user")
                .all()
            )
            message_list = []
            for participant in participant_list:
                # 자기 자신 제외한 사람들에게 알람
                if not self.user:
                    break
                if self.user.id == participant.participant_user_id:
                    continue
                message = MESSAGE_FORMAT_PARTY_COMMENT_ADDED.format(
                    user=self.user.name, party=party.title
                )
                notification_info = NotificationSpecificDto(
                    type=NOTIFICATION_TYPE_PARTY,
                    classification=NOTIFICATION_CLASSIFY_PARTY_COMMENT,
                    related_id=self.party_id,
                    message=message,
                    is_global=False,
                    target_user_id=participant.participant_user_id,
                )
                message_list.append(notification_info)
            if self.user and party.organizer_user_id != self.user.id:
                message = MESSAGE_FORMAT_PARTY_COMMENT_ADDED.format(
                    user=self.user.name, party=party.title
                )
                notification_info = NotificationSpecificDto(
                    type=NOTIFICATION_TYPE_PARTY,
                    related_id=self.party_id,
                    message=message,
                    is_global=False,
                    target_user_id=party.organizer_user_id,
                )
                message_list.append(notification_info)
            await notification_service.create_notifications(message_list)

            return PartyCommentDetail(
                id=comment.id,
                commenter_profile=UserSimpleProfile(
                    user_id=comment.commenter.id,
                    name=comment.commenter.name,
                    profile_picture=comment.commenter.profile_image,
                ),
                posted_date=comment.created_at.strftime(
                    FORMAT_YYYY_MM_DD_T_HH_MM_SS_TZ
                ),
                content=comment.content,
            )
        except Exception as e:
            logger.error(
                f"[Party Comment Error]: (POST) party_id:{self.party_id}, msg:{e}"
            )
            raise ValueError(f"Party comment posting error - party_id:{self.party_id}")

    async def delete_comment(self, comment_id: int) -> None:
        comment = await PartyComment.get_or_none(id=comment_id)
        if not comment:
            raise ValueError(f"Comment ID does not exist: {comment_id}")
        if self.user and comment.commenter_id != self.user.id:
            raise PermissionError(
                f"User is not commenter of the comment ID d: {comment_id}"
            )
        try:
            comment.is_deleted = True
            await comment.save()
        except Exception as e:
            logger.error(
                f"[Party Comment Error]: (DELETE) party_id:{self.party_id}, comment_id:{comment_id}, msg:{e}"
            )
            raise ValueError(f"Party comment delete error - comment_id:{comment_id}")

    async def change_comment(
        self, comment_id: int, content: Optional[str]
    ) -> PartyCommentDetail:
        if not content:
            raise ValueError("Party comment must have content")
        comment = await PartyComment.get_or_none(id=comment_id).select_related(
            "commenter"
        )
        if not comment:
            raise ValueError(f"Comment ID does not exist: {comment_id}")

        if self.user and comment.commenter_id != self.user.id:
            raise PermissionError(
                f"User is not commenter of the comment ID d: {comment_id}"
            )
        try:
            comment.content = content
            await comment.save()
            return PartyCommentDetail(
                id=comment.id,
                commenter_profile=UserSimpleProfile(
                    user_id=comment.commenter.id,
                    name=comment.commenter.name,
                    profile_picture=comment.commenter.profile_image,
                ),
                posted_date=comment.created_at.strftime(
                    FORMAT_YYYY_MM_DD_T_HH_MM_SS_TZ
                ),
                content=comment.content,
            )
        except Exception as e:
            logger.error(
                f"[Party Comment Error]: (CHANGE) party_id:{self.party_id}, comment_id:{comment_id}, msg:{e}"
            )
            raise ValueError(f"Party comment change error - comment_id:{comment_id}")


class PartyLikeService:
    def __init__(self, user: User):
        self.user = user

    async def party_like(self, party_id: int) -> None:
        party_exists = await Party.exists(id=party_id)
        is_liked_party = await PartyLike.exists(user=self.user, party_id=party_id)
        if not party_exists:
            raise ValueError(f"Party-{party_id} is does not exists")
        if is_liked_party:
            raise ValueError(f"Party-{party_id} is already liked")
        await PartyLike.create(user=self.user, party_id=party_id)

    async def cancel_party_like(self, party_id: int) -> None:
        party_exists = await Party.exists(id=party_id)
        liked_party = await PartyLike.get_or_none(user=self.user, party_id=party_id)
        if not party_exists:
            raise ValueError(f"Party-{party_id} is does not exists")
        if not liked_party:
            raise ValueError(f"Party-{party_id} is already liked")
        await liked_party.delete()

    async def _build_party_info(self, party: Party) -> PartyListDetail:
        approved_participants = await PartyParticipant.filter(
            party=party, status=ParticipationStatus.APPROVED
        ).count()  # TODO 추후 캐시로 처리
        return PartyListDetail(
            id=party.id,
            sport_name=party.sport.name,
            title=party.title,
            gather_date=party.gather_at.strftime(FORMAT_YYYY_MM_DD),
            gather_time=party.gather_at.strftime(FORMAT_HH_MM),
            participants_info=f"{approved_participants}/{party.participant_limit}",
            price=party.participant_cost,
            body=party.body,
            organizer_profile=UserSimpleProfile(
                profile_picture=party.organizer_user.profile_image,
                name=party.organizer_user.name,
                user_id=party.organizer_user_id,
            ),
            posted_date=party.created_at.strftime(FORMAT_YYYY_MM_DD_T_HH_MM_SS_TZ),
            is_user_organizer=False,
            is_active=party.is_active,
            place_name=party.place_name,
            place_id=party.place_id,
            address=party.address,
            longitude=party.longitude,
            latitude=party.latitude,
        )

    async def get_liked_parties(
        self, page: int = 1, page_size: int = 8
    ) -> List[PartyListDetail]:
        # 페이징 계산
        offset = (page - 1) * page_size
        limit = page_size
        liked_parties = (
            await PartyLike.filter(user=self.user)
            .select_related("party", "party__organizer_user", "party__sport")
            .offset(offset)
            .limit(limit)
            .order_by("-id")
        )
        liked_party_info_list = [
            await self._build_party_info(liked_party.party)
            for liked_party in liked_parties
        ]
        return liked_party_info_list
