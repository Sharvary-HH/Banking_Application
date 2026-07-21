from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.services.scheduler_job import run_due_scheduled_transfers

scheduler = AsyncIOScheduler()


def configure_scheduler() -> None:
    scheduler.add_job(
        run_due_scheduled_transfers,
        "interval",
        seconds=60,
        id="run_due_scheduled_transfers",
        replace_existing=True,
    )
