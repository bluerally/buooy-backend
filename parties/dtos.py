from typing import Optional, List
from pydantic import BaseModel
from parties.models import ParticipationStatus
from users.dtos import UserSimpleProfile
from common.dtos import BaseResponse


class RefreshTokenRequest(BaseModel):
    new_status: ParticipationStatus


class PartyInfo(BaseModel):
    id: int
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
    is_active: bool


class ParticipantProfile(UserSimpleProfile):
    participation_id: int


class PartyListDetail(PartyInfo):
    is_user_organizer: bool = False


class PartyDetail(PartyInfo):
    is_user_organizer: bool = False
    pending_participants: Optional[List[ParticipantProfile]] = None
    approved_participants: Optional[List[ParticipantProfile]] = None


class PartyDetailResponse(BaseResponse):
    data: PartyDetail


class PartyListResponse(BaseResponse):
    data: List[PartyListDetail]


class PartyCommentDetail(BaseModel):
    id: int
    commenter_profile: UserSimpleProfile
    posted_date: str
    content: str
    is_writer: Optional[bool] = None


class PartyCommentResponse(BaseResponse):
    data: List[PartyCommentDetail]


class PartyCommentPostRequest(BaseModel):
    content: str


class PartyCommentPost(BaseModel):
    comment_info: PartyCommentDetail


class PartyCommentPostResponse(BaseResponse):
    data: Optional[PartyCommentPost] = None
