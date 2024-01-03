from fastapi import APIRouter, status, Depends
from common.dependencies import get_current_user
from common.dtos import BaseResponse
from common.utils import convert_string_to_datetime
from parties.models import Party
from parties.dtos import PartyCreateRequest
from users.models import User
from parties.services import PartyParticipateService
from fastapi import HTTPException
from parties.dtos import RefreshTokenRequest, PartyDetailResponse
from parties.services import PartyDetailService


party_router = APIRouter(
    prefix="/api/party",
)


@party_router.post("/", response_model=BaseResponse)
async def create_party(
    request_data: PartyCreateRequest, user: User = Depends(get_current_user)
) -> BaseResponse:
    party = await Party.create(
        title=request_data.title,
        body=request_data.body,
        gather_at=convert_string_to_datetime(request_data.gather_at),
        due_at=convert_string_to_datetime(request_data.due_at),
        place_id=request_data.place_id,
        place_name=request_data.place_name,
        address=request_data.address,
        longitude=request_data.longitude,
        latitude=request_data.latitude,
        participant_limit=request_data.participant_limit,
        participant_cost=request_data.participant_cost,
        sport_id=request_data.sport_id,
        organizer_user=user,
    )

    # 생성된 파티 정보를 응답
    return BaseResponse(
        status_code=status.HTTP_201_CREATED,
        message="Party created successfully",
        data={"party_id": party.id},
    )


@party_router.post("/{party_id}/participate", response_model=BaseResponse)
async def participate_in_party(
    party_id: int, user: User = Depends(get_current_user)
) -> BaseResponse:
    service = await PartyParticipateService.create(party_id, user)
    try:
        await service.participate()
        return BaseResponse(
            status_code=status.HTTP_200_OK,
            message="Participation requested successfully.",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@party_router.post(
    "/participants/{party_id}/status-change", response_model=BaseResponse
)
async def participant_change_participation_status(
    party_id: int, body: RefreshTokenRequest, user: User = Depends(get_current_user)
) -> BaseResponse:
    new_status = body.new_status
    service = await PartyParticipateService.create(party_id, user)
    try:
        changed_participation = await service.participant_change_participation_status(
            new_status
        )
        return BaseResponse(
            status_code=status.HTTP_200_OK,
            data={"participation_id": changed_participation.id},
            message="Participation status changed successfully.",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@party_router.post(
    "/organizer/{party_id}/status-change/{participation_id}",
    response_model=BaseResponse,
)
async def organizer_change_participation_status(
    party_id: int,
    participation_id: int,
    body: RefreshTokenRequest,
    user: User = Depends(get_current_user),
) -> BaseResponse:
    new_status = body.new_status
    service = await PartyParticipateService.create(party_id, user)
    try:
        changed_participation = await service.organizer_change_participation_status(
            participation_id, new_status
        )
        return BaseResponse(
            status_code=status.HTTP_200_OK,
            data={"participation_id": changed_participation.id},
            message="Participation status changed successfully.",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@party_router.get("/details/{party_id}", response_model=PartyDetailResponse)
async def get_party_details(
    party_id: int, user: User = Depends(get_current_user)
) -> PartyDetailResponse:
    service = await PartyDetailService.create(party_id)
    response = await service.get_party_details(user)
    return response
