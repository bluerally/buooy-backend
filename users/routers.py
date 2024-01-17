import logging
from typing import List, Optional, Any
import uuid
from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.responses import RedirectResponse

from common.choices import SocialAuthPlatform
from common.constants import (
    AUTH_PLATFORM_GOOGLE,
    AUTH_PLATFORM_KAKAO,
    AUTH_PLATFORM_NAVER,
)
from common.config import LOGIN_REDIRECT_URL
from common.dependencies import get_current_user
from common.dtos import BaseResponse
from users.auth import GoogleAuth, KakaoAuth, SocialLogin, NaverAuth
from users.dtos import (
    SocialLoginTokenResponse,
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
from common.logging_configs import LoggingAPIRoute

user_router = APIRouter(
    prefix="/api/user",
    route_class=LoggingAPIRoute,
)


@user_router.get(
    "/auth/redirect-url/{platform}", response_model=SocialLoginRedirectResponse
)
async def get_social_login_redirect_url(
    request: Request,
    platform: SocialAuthPlatform,
) -> SocialLoginRedirectResponse:
    auth: SocialLogin
    if platform == AUTH_PLATFORM_GOOGLE:
        auth = GoogleAuth()
    elif platform == AUTH_PLATFORM_KAKAO:
        session_nonce = str(uuid.uuid4())
        auth = KakaoAuth(session_nonce)
        request.session["nonce"] = session_nonce
    elif platform == AUTH_PLATFORM_NAVER:
        session_state = str(uuid.uuid4())
        auth = NaverAuth(session_state)
        request.session["state"] = session_state
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported platform"
        )

    redirect_url = await auth.get_login_redirect_url()
    redirect_url_info = RedirectUrlInfo(redirect_url=redirect_url)

    return SocialLoginRedirectResponse(
        status_code=status.HTTP_200_OK,
        message="redirect URL fetched successfully",
        data=redirect_url_info,
    )


@user_router.get("/auth/{platform}", response_model=None)
async def social_auth_callback(
    request: Request,
    platform: SocialAuthPlatform,
    code: str,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
) -> Any:  # 테스트 중(임시)
    auth: SocialLogin

    if platform == AUTH_PLATFORM_GOOGLE:
        auth = GoogleAuth()
    elif platform == AUTH_PLATFORM_KAKAO:
        if error is not None or error_description is not None:
            # TODO logging 필요
            # return RedirectResponse(
            #     url=f"{LOGIN_REDIRECT_URL}/login/{platform.value}?error={error}&error_decs={error_description}",
            #     status_code=status.HTTP_406_NOT_ACCEPTABLE,
            # )
            logging.error(
                f"[Auth Error]:{platform.value} | {error} | {error_description}"
            )
            return BaseResponse(
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                message=f"Error: {error}, Error Detail:{error_description}",
                data=None,
            )

        session_nonce = request.session.get("nonce")
        auth = KakaoAuth(session_nonce)
    elif platform == AUTH_PLATFORM_NAVER:
        if error is not None or error_description is not None:
            # TODO logging 필요
            # return RedirectResponse(
            #     url=f"{LOGIN_REDIRECT_URL}/login/{platform.value}?error={error}&error_decs={error_description}",
            #     status_code=status.HTTP_406_NOT_ACCEPTABLE,
            # )
            logging.error(
                f"[Auth Error]:{platform.value} | {error} | {error_description}"
            )
            return BaseResponse(
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                message=f"Error: {error}, Error Detail:{error_description}",
                data=None,
            )

        session_state = request.session.get("state")
        auth = NaverAuth(session_state)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported platform"
        )

    try:
        user_info = await auth.get_user_data(code)
        user = await User.get_or_none(sns_id=user_info.sns_id)
        if not user:
            user = await User.create(**user_info.__dict__)
        else:
            # 기존 사용자 정보 업데이트
            if (
                user.email != user_info.email
                or user.profile_image != user_info.profile_image
            ):
                user.email = user_info.email
                user.profile_image = user_info.profile_image
                await user.save()

        # 토큰 발행된 user_id 저장
        request.session["user_id"] = user.id

        return RedirectResponse(url=f"{LOGIN_REDIRECT_URL}/login/{platform.value}")

    except HTTPException as e:
        logging.error(
            f"[Social Login Callback Error: platform:{platform.value}, code:{code}, error:{error}, error_details:{error_description}, error_msg:{e}]"
        )
        return BaseResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Error: {e}",
            data=None,
        )
        # return RedirectResponse(
        #     url=f"{LOGIN_REDIRECT_URL}/login/{platform.value}?error={e.detail}&error_status={e.status_code}",
        #     status_code=status.HTTP_406_NOT_ACCEPTABLE,
        # )


@user_router.post("/auth/token", response_model=SocialLoginTokenResponse)
async def login_access_token(request: Request) -> SocialLoginTokenResponse:
    user_id = request.session.get("user_id")
    if not user_id:
        logging.error(f"[LOGIN API ERROR]: headers: {str(request.headers)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Need user ID"
        )

    user = await User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found with user ID",
        )

    user_info = UserInfo(
        sns_id=user.sns_id,
        email=user.email,
        name=user.name,
        profile_image=user.profile_image,
    )

    # Access, Refresh 토큰 생성 및 저장
    access_token = create_access_token(data={"user_id": user.id})
    refresh_token = await create_refresh_token(user)
    return SocialLoginTokenResponse(
        status_code=status.HTTP_200_OK,
        message="Login successful",
        data=LoginResponseData(
            user_info=user_info,
            access_token=access_token,
            refresh_token=refresh_token,
        ),
    )


@user_router.post("/auth/token/refresh", response_model=SocialLoginTokenResponse)
async def access_token_refresh(
    body: RefreshTokenRequest, user: User = Depends(get_current_user)
) -> SocialLoginTokenResponse:
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

    return SocialLoginTokenResponse(
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
