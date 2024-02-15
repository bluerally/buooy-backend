import logging
import uuid
from typing import List, Optional, Any

from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.responses import RedirectResponse

from common.cache_constants import CACHE_KEY_LOGIN_REDIRECT_UUID
from common.cache_utils import RedisManager
from common.choices import SocialAuthPlatform
from common.config import LOGIN_REDIRECT_URL
from common.constants import (
    AUTH_PLATFORM_GOOGLE,
    AUTH_PLATFORM_KAKAO,
    AUTH_PLATFORM_NAVER,
)
from common.dependencies import get_current_user
from common.logging_configs import LoggingAPIRoute
from users.auth import GoogleAuth, KakaoAuth, SocialLogin, NaverAuth
from users.dtos import (
    UserInfo,
    RedirectUrlInfo,
    LoginResponseData,
    RefreshTokenRequest,
    AccessTokenRequest,
)
from users.dto.response import AccessTokenResponse, SelfProfileResponse
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
from users.services import SelfProfileService
from parties.dtos import PartyListDetail
from parties.services import PartyLikeService

user_router = APIRouter(
    prefix="/api/user",
    route_class=LoggingAPIRoute,
)


@user_router.get(
    "/auth/redirect-url/{platform}",
    response_model=RedirectUrlInfo,
    status_code=status.HTTP_200_OK,
)
async def get_social_login_redirect_url(
    request: Request,
    platform: SocialAuthPlatform,
) -> RedirectUrlInfo:
    auth: SocialLogin
    if platform == AUTH_PLATFORM_GOOGLE:
        auth = GoogleAuth()
    elif platform == AUTH_PLATFORM_KAKAO:
        session_nonce = str(uuid.uuid4())
        auth = KakaoAuth(session_nonce)
    elif platform == AUTH_PLATFORM_NAVER:
        session_state = str(uuid.uuid4())
        auth = NaverAuth(session_state)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported platform"
        )

    redirect_url = await auth.get_login_redirect_url()

    return RedirectUrlInfo(redirect_url=redirect_url)


@user_router.get(
    "/auth/{platform}",
    response_model=None,
    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
)
async def social_auth_callback(
    request: Request,
    platform: SocialAuthPlatform,
    code: str,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
) -> RedirectResponse:
    auth: SocialLogin
    try:
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
                    f"[Auth Error]:platform-{platform.value} | error-{error} | desc-{error_description}"
                )
                raise HTTPException(
                    status_code=status.HTTP_406_NOT_ACCEPTABLE,
                    detail=f"Error: {error}, Error Detail:{error_description}",
                )

            # session_nonce = request.session.get("nonce")
            # auth = KakaoAuth(session_nonce)
            auth = KakaoAuth()
        elif platform == AUTH_PLATFORM_NAVER:
            if error is not None or error_description is not None:
                # TODO logging 필요
                # return RedirectResponse(
                #     url=f"{LOGIN_REDIRECT_URL}/login/{platform.value}?error={error}&error_decs={error_description}",
                #     status_code=status.HTTP_406_NOT_ACCEPTABLE,
                # )
                logging.error(
                    f"[Auth Error]:platform-{platform.value} | error-{error} | desc-{error_description}"
                )
                raise HTTPException(
                    status_code=status.HTTP_406_NOT_ACCEPTABLE,
                    detail=f"Error: {error}, Error Detail:{error_description}",
                )

            # session_state = request.session.get("state")
            # auth = NaverAuth(session_state)
            auth = NaverAuth()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported platform"
            )

        is_new_user = True
        user_info = await auth.get_user_data(code)
        user = await User.get_or_none(sns_id=user_info.sns_id)
        if not user:
            user = await User.create(**user_info.__dict__)
        else:
            is_new_user = False
            # 기존 사용자 정보 업데이트
            if (
                user.email != user_info.email
                or user.profile_image != user_info.profile_image
            ):
                user.email = user_info.email
                user.profile_image = user_info.profile_image
                await user.save()

            # uid 생성(인증한 유저 확인용)
            r = RedisManager()
            user_identify_uuid = str(uuid.uuid4())
            cache_key = CACHE_KEY_LOGIN_REDIRECT_UUID.format(uuid=user_identify_uuid)
            r.set_value(cache_key, [user.id, is_new_user])
            return RedirectResponse(
                url=f"{LOGIN_REDIRECT_URL}/login/{platform.value}?uid={user_identify_uuid}"
            )
    except Exception as e:
        logging.error(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@user_router.post(
    "/auth/token",
    response_model=AccessTokenResponse,
    status_code=status.HTTP_201_CREATED,
)
async def login_access_token(body: AccessTokenRequest) -> AccessTokenResponse:
    user_uuid = body.user_uid
    r = RedisManager()
    cache_key = CACHE_KEY_LOGIN_REDIRECT_UUID.format(uuid=user_uuid)
    user_id, is_new_user = r.get_value(cache_key)
    if not user_id:
        logging.error(f"[LOGIN API ERROR]: INVALID uuid: {user_uuid}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid uuid"
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
    return AccessTokenResponse(
        user_info=user_info,
        access_token=access_token,
        refresh_token=refresh_token,
        is_new_user=is_new_user,
    )


@user_router.post(
    "/auth/token/refresh",
    response_model=LoginResponseData,
    status_code=status.HTTP_201_CREATED,
)
async def access_token_refresh(
    body: RefreshTokenRequest, user: User = Depends(get_current_user)
) -> LoginResponseData:
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
    return LoginResponseData(
        user_info=UserInfo(**user.__dict__),
        access_token=access_token,
    )


@user_router.post("/auth/logout", response_model=None, status_code=status.HTTP_200_OK)
async def logout(user: User = Depends(get_current_user)) -> str:
    # 사용자와 연관된 모든 리프레시 토큰을 비활성화
    await UserToken.filter(user=user, is_active=True).update(is_active=False)

    return "Logged out successfully"


@user_router.get(
    "/certificates",
    response_model=List[CertificateName_Pydantic],
    status_code=status.HTTP_200_OK,
)
async def certificate_level_list() -> Any:
    certificates = await CertificateName_Pydantic.from_queryset(Certificate.all())
    return certificates


@user_router.get(
    "/certificates/{certificate_id}/levels",
    response_model=List[CertificateLevel_Pydantic],
    status_code=status.HTTP_200_OK,
)
async def get_certificate_levels(certificate_id: int) -> Any:
    levels = await CertificateLevel_Pydantic.from_queryset(
        CertificateLevel.filter(certificate_id=certificate_id)
    )
    return levels


@user_router.get(
    "/party/like",
    response_model=List[PartyListDetail],
    status_code=status.HTTP_200_OK,
)
async def get_liked_parties(
    user: User = Depends(get_current_user),
) -> List[PartyListDetail]:
    service = PartyLikeService(user)
    try:
        return await service.get_liked_parties()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@user_router.get(
    "/me", response_model=SelfProfileResponse, status_code=status.HTTP_200_OK
)
async def get_self_profile(
    user: User = Depends(get_current_user)
) -> SelfProfileResponse:
    service = SelfProfileService(user)
    return await service.get_profile()
