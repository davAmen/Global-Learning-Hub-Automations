"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from zoneinfo import ZoneInfo

from fastapi import FastAPI

from src.api.routes_health import router as health_router
from src.api.routes_jobs import router as jobs_router
from src.api.routes_reports import router as reports_router
from src.api.routes_webhooks import router as webhooks_router
from src.config import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)
scheduler = None


def run_scheduled_job() -> None:
    from src.database import get_db
    from src.automation.scheduler import send_reminders
    from src.reports.daily_report import build_report, send_report_to_admin

    logger.info("Scheduled job firing.")
    db = get_db()
    send_reminders(db)
    send_report_to_admin(build_report(db))


@asynccontextmanager
async def lifespan(app: FastAPI):
    global scheduler
    settings = get_settings()

    if settings.enable_scheduler:
        from apscheduler.schedulers.background import BackgroundScheduler

        scheduler = BackgroundScheduler(timezone=ZoneInfo(settings.timezone))
        scheduler.add_job(
            run_scheduled_job,
            "cron",
            hour=settings.job_hour,
            minute=settings.job_minute,
            id="daily",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
        scheduler.start()
        logger.info(
            "Scheduler started for %02d:%02d %s.",
            settings.job_hour,
            settings.job_minute,
            settings.timezone,
        )
    else:
        logger.info("In-process scheduler disabled; use POST /run-daily-job or an external cron.")

    yield

    if scheduler is not None and scheduler.running:
        scheduler.shutdown(wait=False)
        scheduler = None
        logger.info("Scheduler shut down.")


app = FastAPI(title="Global Learning Hub Automation", lifespan=lifespan)

app.include_router(health_router)
app.include_router(jobs_router)
app.include_router(reports_router)
app.include_router(webhooks_router)
