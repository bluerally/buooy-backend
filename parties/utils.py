from parties.models import Party
from datetime import datetime


async def inactive_expired_parties() -> None:
    _now = datetime.now()
    await Party.filter(gather_at__lte=_now).update(is_active=False)
