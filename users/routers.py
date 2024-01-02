from typing import List

from fastapi import APIRouter, HTTPException, status, Depends

from common.choices import SocialAuthPlatform
from common.constants import AUTH_PLATFORM_GOOGLE
from common.dependencies import get_current_user
from common.dtos import BaseResponse
from users.auth import GoogleAuth
from users.dtos import (
    SocialLoginCallbackResponse,
    UserInfo,
    SocialLoginRedirectResponse,
    RedirectUrlInfo,
    LoginResponseData,
    RefreshTokenRequest,
)
from users.models import (
    CertificateLevel,
    Certificate,
    User,
    CertificateName_Pydantic,
    CertificateLevel_Pydantic,
    UserToken,
)
from users.utils import (
    create_refresh_token,
    create_access_token,
    is_active_refresh_token,
)

user_router = APIRouter(
    prefix="/api/user",
)


@user_router.get("/auth/redirect", response_model=SocialLoginRedirectResponse)
async def get_social_login_redirect_url(
    platform: SocialAuthPlatform
) -> SocialLoginRedirectResponse:
    if platform == AUTH_PLATFORM_GOOGLE:
        google_auth = GoogleAuth()
        redirect_url = await google_auth.get_login_redirect_url()
        redirect_url_info = RedirectUrlInfo(redirect_url=redirect_url)

        return SocialLoginRedirectResponse(
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
async def social_auth_callback(
    platform: SocialAuthPlatform, code: str
) -> SocialLoginCallbackResponse:
    if platform == AUTH_PLATFORM_GOOGLE:
        try:
            google_auth = GoogleAuth()
            user_info_dict = await google_auth.get_user_data(code)
            # TODO 가공 로직 변경 필요
            user_info = UserInfo(
                sns_id=user_info_dict.get("sub"),
                email=user_info_dict.get("email"),
                name=user_info_dict.get("name"),
                profile_image=user_info_dict.get("picture"),
            )

            # 데이터베이스에서 사용자 찾기 또는 생성
            user = await User.get_or_none(sns_id=user_info.sns_id)
            if not user:
                user = await User.create(**user_info_dict)

            # Access, Refresh 토큰 생성 및 저장
            access_token = create_access_token(data={"user_id": user.id})
            refresh_token = await create_refresh_token(user)

            return SocialLoginCallbackResponse(
                status_code=status.HTTP_200_OK,
                message="Login successful",
                data=LoginResponseData(
                    user_info=user_info,
                    access_token=access_token,
                    refresh_token=refresh_token,
                ),
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


@user_router.post("/auth/token/refresh", response_model=SocialLoginCallbackResponse)
async def access_token_refresh(
    body: RefreshTokenRequest, user: User = Depends(get_current_user)
) -> SocialLoginCallbackResponse:
    refresh_token = body.refresh_token

    is_token_active = await is_active_refresh_token(
        user=user, refresh_token=refresh_token
    )
    if not is_token_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid or inactive token"
        )

    # 새로운 Access 토큰 생성
    access_token = create_access_token(data={"user_id": user.id})

    return SocialLoginCallbackResponse(
        status_code=status.HTTP_200_OK,
        message="Token refreshed successfully",
        data=LoginResponseData(
            user_info=UserInfo(**user.__dict__),
            access_token=access_token,
        ),
    )


@user_router.post("/auth/logout", response_model=BaseResponse)
async def logout(user: User = Depends(get_current_user)) -> BaseResponse:
    # 사용자와 연관된 모든 리프레시 토큰을 비활성화
    await UserToken.filter(user=user, is_active=True).update(is_active=False)

    return BaseResponse(
        status_code=status.HTTP_200_OK, message="Logout successful", data=None
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
        status_code=status.HTTP_200_OK,
        message="Certificate levels fetched successfully",
        data=levels,
    )
