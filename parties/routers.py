from fastapi import APIRouter, status, Depends
from common.dependencies import get_current_user
from common.dtos import BaseResponse
from common.utils import convert_string_to_datetime
from parties.models import Party
from parties.dtos import PartyCreateRequest
from users.models import User

party_router = APIRouter(
    prefix="/api/party",
)


@party_router.post("/", response_model=BaseResponse)
async def create_party(
    request_data: PartyCreateRequest, user: User = Depends(get_current_user)
):
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
