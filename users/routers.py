from typing import List

from fastapi import APIRouter
from fastapi import HTTPException, status

from common.constants import AUTH_PLATFORM_GOOGLE
from common.dtos import BaseResponse
from users.auth import GoogleAuth
from users.dtos import (
    SocialLoginCallbackResponse,
    UserInfo,
    SocialLoginRedirectResponse,
    RedirectUrlInfo,
)
from users.models import CertificateLevel, Certificate
from users.models import CertificateName_Pydantic, CertificateLevel_Pydantic
from common.choices import SocialAuthPlatform


user_router = APIRouter(
    prefix="/api/user",
)


@user_router.get("/auth/redirect", response_model=SocialLoginRedirectResponse)
async def get_social_login_redirect_url(platform: SocialAuthPlatform):
    # async def get_social_login_redirect_url():
    if platform == AUTH_PLATFORM_GOOGLE:
        google_auth = GoogleAuth()
        redirect_url = await google_auth.get_login_redirect_url()
        redirect_url_info = RedirectUrlInfo(redirect_url=redirect_url)

        return BaseResponse(
            status_code=status.HTTP_200_OK,
            message="Google redirect URL fetched successfully",
            data=redirect_url_info,
        )

    # Naver와 Kakao에 대한 처리를 여기에 추가
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported platform"
        )


@user_router.get("/auth/callback", response_model=SocialLoginCallbackResponse)
async def social_auth_callback(platform: str, code: str):
    if platform == AUTH_PLATFORM_GOOGLE:
        try:
            google_auth = GoogleAuth()
            user_info_dict = await google_auth.get_user_data(code)
            # TODO 가공 로직 변경 필요
            user_info = UserInfo(**user_info_dict)
            return SocialLoginCallbackResponse(
                status_code=status.HTTP_200_OK,
                message="Google user fetched successfully",
                data=user_info,
            )
        except HTTPException as e:
            return SocialLoginCallbackResponse(
                status_code=e.status_code, message=str(e.detail), data=None
            )
    # Naver와 Kakao 처리 추가 예정
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported platform"
        )


@user_router.get(
    "/certificates", response_model=BaseResponse[List[CertificateName_Pydantic]]
)
async def certificate_level_list() -> BaseResponse:
    certificates = await CertificateName_Pydantic.from_queryset(Certificate.all())
    return BaseResponse(
        status_code=status.HTTP_200_OK,
        message="Certificates fetched successfully",
        data=certificates,
    )


@user_router.get(
    "/certificates/{certificate_id}/levels",
    response_model=BaseResponse[List[CertificateLevel_Pydantic]],
)
async def get_certificate_levels(certificate_id: int) -> BaseResponse:
    levels = await CertificateLevel_Pydantic.from_queryset(
        CertificateLevel.filter(certificate_id=certificate_id)
    )
    return BaseResponse(
        status_code=200, message="Certificate levels fetched successfully", data=levels
    )
