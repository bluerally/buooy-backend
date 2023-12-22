import bcrypt
import logging
from datetime import datetime
from common.constants import FORMAT_YYYY_MM_DD_T_HH_MM_SS_TZ


def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def convert_string_to_datetime(string_datetime: str):
    try:
        return datetime.strptime(string_datetime, FORMAT_YYYY_MM_DD_T_HH_MM_SS_TZ)
    except Exception:
        logging.error(f"Invalid datetime: string - {string_datetime}")
        return None
