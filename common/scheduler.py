from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from parties.utils import inactive_expired_parties

scheduler = AsyncIOScheduler(timezone="Asia/Seoul")


def start_scheduler() -> None:
    scheduler.add_job(
        inactive_expired_parties,
        CronTrigger(hour=0, minute=0),  # 매일 밤 12시에 실행
        id="inactive_expired_parties",
        name="Inactivate expired parties",
        replace_existing=True,
    )
    scheduler.start()
