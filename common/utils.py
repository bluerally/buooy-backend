import os
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional, Any

import aioboto3
import asyncio
import bcrypt
from fastapi import UploadFile
from common.config import logger, airtake_ins, IS_TEST, mixpanel_ins as mp
from common.constants import FORMAT_YYYY_MM_DD_T_HH_MM_SS_TZ
from common.mixpanel_constants import MIXPANEL_PROPERTY_KEY_USER_ID


def verify_password(plain_password: str, hashed_password: str) -> Any:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def convert_string_to_datetime(string_datetime: str) -> Optional[datetime]:
    try:
        return datetime.strptime(string_datetime, FORMAT_YYYY_MM_DD_T_HH_MM_SS_TZ)
    except Exception:
        logger.error(f"Invalid datetime: string - {string_datetime}")
        return None


async def s3_upload_file(folder: str, file: UploadFile) -> str:
    # 파일의 원본 이름에서 확장자 추출
    _, ext = os.path.splitext(file.filename)
    if not ext:
        raise ValueError("No file extension found in the uploaded file.")

    timestamp = datetime.now(ZoneInfo("UTC")).strftime("%Y%m%d%H%M%S%f")
    filename = f"{folder}/{timestamp}{ext}"

    session = aioboto3.Session()
    from common.config import AWS_S3_ACCESS_KEY, AWS_S3_SECRET_KEY, S3_BUCKET

    async with session.client(
        "s3",
        aws_access_key_id=AWS_S3_ACCESS_KEY,
        aws_secret_access_key=AWS_S3_SECRET_KEY,
    ) as s3:
        try:
            await s3.upload_fileobj(file.file, S3_BUCKET, filename)
        except Exception as e:
            logger.error(f"Unable to upload {file.filename} to S3: {e} ({type(e)})")
            return ""

    return filename


# def track_mixpanel(
#     distinct_id: Any = None,
#     event_name: str = "",
#     properties: Optional[dict[str, Any]] = None,
# ) -> None:
#     """
#
#     :rtype: object
#     """
#     if IS_TEST:
#         return
#
#     if not event_name:
#         return
#
#     if properties is None:
#         properties = {}
#
#     if not distinct_id:
#         distinct_id = str(uuid.uuid4())
#
#     properties.update(
#         {
#             "$os": "Server",
#         }
#     )
#
#     max_retry_num = 3
#     try_num = 0
#     for _ in range(max_retry_num):
#         try:
#             mp.track(distinct_id, event_name, properties)
#             logger.info(
#                 f"[Mixpanel] Mixpanel Retry Info : Successed tracking after {try_num} retry , event_name: {event_name}",
#                 exc_info=True,
#             )
#             break
#         except Exception as e:
#             logger.error(
#                 f"[Mixpanel] Mixpanel error : {e}, event_name: {event_name}",
#                 exc_info=True,
#             )
#             try_num += 1
#     # for loop 완전히 실행되면 실행됨.
#     else:
#         logger.error(
#             f"[Mixpanel] Mixpanel error : Failed to track event after {max_retry_num} attempts., event_name: {event_name}"
#         )


async def track_mixpanel(
    distinct_id: Any = None,
    event_name: str = "",
    properties: Optional[dict[str, Any]] = None,
) -> None:
    if IS_TEST or not event_name:
        return

    properties = properties or {}
    distinct_id = distinct_id or str(uuid.uuid4())
    properties.update({"$os": "Server"})

    async def _track() -> None:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Run Mixpanel tracking in a thread pool to not block
                await asyncio.get_event_loop().run_in_executor(
                    None, mp.track, distinct_id, event_name, properties
                )
                if attempt > 0:
                    logger.info(
                        f"[Mixpanel] Succeeded tracking after {attempt} retries: {event_name}"
                    )
                return
            except Exception as e:
                logger.error(
                    f"[Mixpanel] Error: {e}, event_name: {event_name}", exc_info=True
                )
        logger.error(
            f"[Mixpanel] Failed to track after {max_retries} attempts: {event_name}"
        )

    # Fire and forget
    asyncio.create_task(_track())


async def track_airtake(
    event_name: str = "",
    properties: Optional[dict[str, Any]] = None,
) -> None:
    if IS_TEST or not event_name:
        return

    properties = properties or {}
    if not properties.get("$actor_id") and not properties.get("$device_id"):
        properties["$device_id"] = str(uuid.uuid4())

    async def _track() -> None:
        try:
            # Run Mixpanel tracking in a thread pool to not block
            await asyncio.get_event_loop().run_in_executor(
                None, airtake_ins.track, event_name, properties
            )
        except Exception as e:
            logger.error(
                f"[Mixpanel] Error: {e}, event_name: {event_name}", exc_info=True
            )

    # Fire and forget
    asyncio.create_task(_track())


async def track_analytics(
    event_name: str = "",
    user_id: Optional[Any] = None,
    properties: Optional[dict[str, Any]] = None,
) -> None:
    """Track events to both Mixpanel and Airtake asynchronously"""
    tasks = []

    if event_name:
        distinct_id = user_id or str(uuid.uuid4())
        mp_properties = {"$os": "Server", **(properties or {})}
        if user_id:
            mp_properties[MIXPANEL_PROPERTY_KEY_USER_ID] = user_id
        tasks.append(track_mixpanel(distinct_id, event_name, mp_properties))

        # airtake
        at_properties = properties or {}
        if not at_properties.get("$actor_id") and not at_properties.get("$device_id"):
            at_properties["$device_id"] = str(uuid.uuid4())

        if user_id:
            at_properties["$actor_id"] = user_id

        tasks.append(track_airtake(event_name, at_properties))

    if tasks:
        asyncio.gather(*tasks)
