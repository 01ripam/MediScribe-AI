from datetime import datetime, timedelta
from random import randint

_otp_store: dict[str, tuple[str, datetime]] = {}
OTP_TTL_MINUTES = 5


def generate_otp(phone: str) -> str:
    otp = str(randint(100000, 999999))
    expires_at = datetime.utcnow() + timedelta(minutes=OTP_TTL_MINUTES)
    _otp_store[phone] = (otp, expires_at)
    return otp


def validate_otp(phone: str, otp: str) -> bool:
    item = _otp_store.get(phone)
    if not item:
        return False
    stored_otp, expires_at = item
    if datetime.utcnow() > expires_at:
        _otp_store.pop(phone, None)
        return False
    if stored_otp != otp:
        return False
    _otp_store.pop(phone, None)
    return True
