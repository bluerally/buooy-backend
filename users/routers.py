from typing import List, Optional
import uuid
from fastapi import APIRouter, HTTPException, status, Depends, Request

from common.choices import SocialAuthPlatform
from common.constants import (
    AUTH_PLATFORM_GOOGLE,
    AUTH_PLATFORM_KAKAO,
    AUTH_PLATFORM_NAVER,
)
from common.dependencies import get_current_user
from common.dtos import BaseResponse
from users.auth import GoogleAuth, KakaoAuth, SocialLogin, NaverAuth
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


@user_router.get("/auth/{platform}", response_model=SocialLoginCallbackResponse)
async def social_auth_callback(
    request: Request,
    platform: SocialAuthPlatform,
    code: str,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
) -> SocialLoginCallbackResponse:
    auth: SocialLogin

    if platform == AUTH_PLATFORM_GOOGLE:
        auth = GoogleAuth()
    elif platform == AUTH_PLATFORM_KAKAO:
        if error is not None or error_description is not None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Kakao authorization Error, error: {error}, error_description: {error_description}",
            )
        session_nonce = request.session.get("nonce")
        auth = KakaoAuth(session_nonce)
    elif platform == AUTH_PLATFORM_NAVER:
        if error is not None or error_description is not None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Kakao authorization Error, error: {error}, error_description: {error_description}",
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
