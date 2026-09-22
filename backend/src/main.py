"""FastAPI app entry point.

Sets up routes and APScheduler for the daily job.
"""

from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI

from src.api.routes_health import router as health_router
from src.api.routes_jobs import router as jobs_router
from src.api.routes_reports import router as reports_router
from src.api.routes_webhooks import router as webhooks_router
from src.config import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

scheduler = BackgroundScheduler()


def run_scheduled_job():
    from src.database import get_db
    from src.automation.scheduler import send_reminders

    logger.info("Scheduled job firing.")
    db = get_db()
    send_reminders(db)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    scheduler.add_job(run_scheduled_job, "cron", hour=settings.job_hour, minute=settings.job_minute)
    scheduler.start()
    logger.info(f"Scheduler started. Job fires daily at {settings.job_hour:02d}:{settings.job_minute:02d}.")
    yield
    scheduler.shutdown()
    logger.info("Scheduler shut down.")


app = FastAPI(title="Global Learning Hub Automation", lifespan=lifespan)

app.include_router(health_router)
app.include_router(jobs_router)
app.include_router(reports_router)
app.include_router(webhooks_router)
