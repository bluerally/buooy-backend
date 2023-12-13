from enum import Enum
from common.constants import (
    AUTH_PLATFORM_GOOGLE,
    AUTH_PLATFORM_KAKAO,
    AUTH_PLATFORM_NAVER,
)


class SocialAuthPlatform(str, Enum):
    google = AUTH_PLATFORM_GOOGLE
    kakao = AUTH_PLATFORM_KAKAO
    naver = AUTH_PLATFORM_NAVER
