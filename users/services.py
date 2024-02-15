from users.models import User
from users.dto.response import SelfProfileResponse
from users.models import UserInterestedSport
from users.dtos import SportInfo


class SelfProfileService:
    def __init__(self, user: User) -> None:
        self.user = user

    async def get_profile(self) -> SelfProfileResponse:
        interested_sports = (
            await UserInterestedSport.filter(user=self.user)
            .select_related("sport")
            .all()
        )
        return SelfProfileResponse(
            id=self.user.id,
            name=self.user.name,
            email=self.user.email,
            introduction=self.user.introduction,
            interested_sports=[
                SportInfo(
                    id=interested_sport.sport_id, name=interested_sport.sport.name
                )
                for interested_sport in interested_sports
            ],
        )
