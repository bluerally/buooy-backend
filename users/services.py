from users.models import User
from dto.response import SelfProfileResponse
from users.models import UserInterestedSport


class SelfProfileService:
    def __init__(self, user: User) -> None:
        self.user = user

    async def get_profile(self) -> SelfProfileResponse:
        interested_sports = await UserInterestedSport.filter(user=self.user).all()
        return SelfProfileResponse(
            id=self.user.id,
            name=self.user.name,
            email=self.user.email,
            introduction=self.user.introduction,
            interested_sports=[sport.id for sport in interested_sports],
        )
