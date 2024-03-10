import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional, Any

import aioboto3
import bcrypt
from fastapi import UploadFile

from common.constants import FORMAT_YYYY_MM_DD_T_HH_MM_SS_TZ


def verify_password(plain_password: str, hashed_password: str) -> Any:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def convert_string_to_datetime(string_datetime: str) -> Optional[datetime]:
    try:
        return datetime.strptime(string_datetime, FORMAT_YYYY_MM_DD_T_HH_MM_SS_TZ)
    except Exception:
        logging.error(f"Invalid datetime: string - {string_datetime}")
        return None


async def s3_upload_file(folder: str, file: UploadFile) -> str:
    # 파일의 원본 이름에서 확장자 추출
    _, ext = os.path.splitext(file.filename)
    if not ext:
        raise ValueError("No file extension found in the uploaded file.")

    filename = f"{folder}/{datetime.now(ZoneInfo("UTC"))}{ext}"

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
            logging.error(f"Unable to upload {file.filename} to S3: {e} ({type(e)})")
            return ""

    return filename
