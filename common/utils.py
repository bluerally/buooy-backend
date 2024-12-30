import os
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional, Any

import aioboto3
import bcrypt
from fastapi import UploadFile
from common.config import logger, IS_TEST, mixpanel_ins as mp
from common.constants import FORMAT_YYYY_MM_DD_T_HH_MM_SS_TZ


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


def track_mixpanel(
    distinct_id: Any = None,
    event_name: str = "",
    properties: Optional[dict[str, Any]] = None,
) -> None:
    """

    :rtype: object
    """
    if IS_TEST:
        return

    if not event_name:
        return

    if properties is None:
        properties = {}

    if not distinct_id:
        distinct_id = str(uuid.uuid4())

    properties.update(
        {
            "$os": "Server",
        }
    )

    max_retry_num = 3
    try_num = 0
    for _ in range(max_retry_num):
        try:
            mp.track(distinct_id, event_name, properties)
            logger.info(
                f"[Mixpanel] Mixpanel Retry Info : Successed tracking after {try_num} retry , event_name: {event_name}",
                exc_info=True,
            )
            break
        except Exception as e:
            logger.error(
                f"[Mixpanel] Mixpanel error : {e}, event_name: {event_name}",
                exc_info=True,
            )
            try_num += 1
    # for loop 완전히 실행되면 실행됨.
    else:
        logger.error(
            f"[Mixpanel] Mixpanel error : Failed to track event after {max_retry_num} attempts., event_name: {event_name}"
        )
