import os
from typing import Optional

from fastapi import UploadFile

from common.config import AWS_S3_URL
from common.utils import s3_upload_file
from users.dto.response import SelfProfileResponse
from users.dtos import SportInfo
from users.models import User
from users.models import UserInterestedSport, Sport


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
            profile_image=os.path.join(AWS_S3_URL, self.user.profile_image),
            interested_sports=[
                SportInfo(
                    id=interested_sport.sport_id, name=interested_sport.sport.name
                )
                for interested_sport in interested_sports
            ],
        )

    async def update_profile(
        self,
        name: Optional[str] = None,
        email: Optional[str] = None,
        introduction: Optional[str] = None,
        interested_sports_ids: Optional[str] = None,
        profile_image: Optional[UploadFile] = None,
    ) -> SelfProfileResponse:
        if name is not None:
            self.user.name = name
        if email is not None:
            self.user.email = email
        if introduction is not None:
            self.user.introduction = introduction

        if interested_sports_ids is not None:
            await UserInterestedSport.filter(user=self.user).delete()
            for sport_id in interested_sports_ids.split(","):
                sport = await Sport.get(id=int(sport_id))
                await UserInterestedSport.create(user=self.user, sport=sport)

        if profile_image:
            folder = f"user/{self.user.id}/profile_image"
            image_url = await s3_upload_file(folder, profile_image)

            if image_url:
                self.user.profile_image = image_url

        await self.user.save()

        return await self.get_profile()
