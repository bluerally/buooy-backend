from typing import List
from typing import Optional, Any

from fastapi import APIRouter, status, Depends, Request, HTTPException
from fastapi.responses import JSONResponse

from common.dependencies import get_current_user
from common.dtos import BaseResponse
from common.utils import convert_string_to_datetime
from parties.dtos import PartyCreateRequest
from parties.dtos import (
    RefreshTokenRequest,
    PartyListResponse,
    PartyDetailResponse,
    PartyCommentResponse,
    PartyCommentPostRequest,
    PartyCommentPostResponse,
    PartyCommentPost,
)
from parties.models import Party
from parties.services import PartyDetailService, PartyListService, PartyCommentService
from parties.services import PartyParticipateService
from users.models import User, Sport, SportName_Pydantic

party_router = APIRouter(
    prefix="/api/party",
)


@party_router.get(
    "/sports",
    response_model=List[SportName_Pydantic],
    status_code=status.HTTP_200_OK,
)
async def get_sports_list(request: Request) -> Any:
    sports_list = await SportName_Pydantic.from_queryset(Sport.all())
    return sports_list


@party_router.post("/", response_model=None, status_code=status.HTTP_201_CREATED)
async def create_party(
    request_data: PartyCreateRequest, user: User = Depends(get_current_user)
) -> JSONResponse:
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
    return JSONResponse(
        status_code=status.HTTP_201_CREATED, content={"party_id": party.id}
    )


@party_router.post(
    "/{party_id}/participate",
    response_model=None,
    status_code=status.HTTP_201_CREATED,
)
async def participate_in_party(
    party_id: int, user: User = Depends(get_current_user)
) -> JSONResponse:
    service = await PartyParticipateService.create(party_id, user)
    try:
        await service.participate()
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content="Participation requested successfully.",
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@party_router.post(
    "/participants/{party_id}/status-change",
    response_model=BaseResponse,
    status_code=status.HTTP_200_OK,
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
            data={"participation_id": changed_participation.id},
            message="Participation status changed successfully.",
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@party_router.post(
    "/organizer/{party_id}/status-change/{participation_id}",
    response_model=BaseResponse,
    status_code=status.HTTP_200_OK,
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
            data={"participation_id": changed_participation.id},
            message="Participation status changed successfully.",
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@party_router.get(
    "/details/{party_id}",
    response_model=PartyDetailResponse,
    status_code=status.HTTP_200_OK,
)
async def get_party_details(party_id: int, request: Request) -> PartyDetailResponse:
    user = request.state.user
    service = await PartyDetailService.create(party_id)
    party_details = await service.get_party_details(user)
    return PartyDetailResponse(
        data=party_details,
        message="Party details successfully retrieved.",
    )


@party_router.get(
    "/list", response_model=PartyListResponse, status_code=status.HTTP_200_OK
)
async def get_party_list(
    request: Request,
    sport_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    gather_date_min: Optional[str] = None,
    gather_date_max: Optional[str] = None,
    search_query: Optional[str] = None,
) -> PartyListResponse:
    user = request.state.user
    service = PartyListService(user)
    party_list = await service.get_party_list(
        sport_id=sport_id,
        is_active=is_active,
        gather_date_min=gather_date_min,
        gather_date_max=gather_date_max,
        search_query=search_query,
    )
    return PartyListResponse(
        data=party_list,
        message="Party list successfully retrieved.",
    )


@party_router.get(
    "/{party_id}/comment",
    response_model=PartyCommentResponse,
    status_code=status.HTTP_200_OK,
)
async def get_party_comments(request: Request, party_id: int) -> PartyCommentResponse:
    user = request.state.user
    try:
        service = PartyCommentService(party_id, user)
        party_comments = await service.get_comments()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return PartyCommentResponse(
        data=party_comments,
        message="Party comments successfully retrieved.",
    )


@party_router.post(
    "/{party_id}/comment",
    response_model=PartyCommentPostResponse,
    status_code=status.HTTP_201_CREATED,
)
async def post_party_comment(
    party_id: int, body: PartyCommentPostRequest, user: User = Depends(get_current_user)
) -> PartyCommentPostResponse:
    comment_content = body.content
    try:
        service = PartyCommentService(party_id, user)
        posted_comment = await service.post_comment(comment_content)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    return PartyCommentPostResponse(
        data=PartyCommentPost(comment_info=posted_comment),
        message="Party comment successfully posted.",
    )


@party_router.post(
    "/{party_id}/comment/{comment_id}",
    response_model=PartyCommentPostResponse,
    status_code=status.HTTP_200_OK,
)
async def change_party_comment(
    party_id: int,
    comment_id: int,
    body: PartyCommentPostRequest,
    user: User = Depends(get_current_user),
) -> PartyCommentPostResponse:
    is_comment_delete = body.is_delete
    service = PartyCommentService(party_id, user)
    try:
        if is_comment_delete:
            await service.delete_comment(comment_id)
            return PartyCommentPostResponse(
                message=f"Party comment {comment_id} successfully deleted",
            )

        comment_content = body.content
        updated_comment = await service.change_comment(comment_id, comment_content)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    return PartyCommentPostResponse(
        data=PartyCommentPost(comment_info=updated_comment),
        message="Party comment successfully updated.",
    )
