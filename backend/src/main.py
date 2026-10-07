"""FastAPI app entry point.

Sets up routes and APScheduler for the daily job.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from time import time
from collections import defaultdict

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pytz import timezone as tz

from src.api.routes_health import router as health_router
from src.api.routes_jobs import router as jobs_router
from src.api.routes_reports import router as reports_router
from src.api.routes_webhooks import router as webhooks_router
from src.api.routes_students import router as students_router
from src.api.routes_courses import router as courses_router
from src.api.routes_approvals import router as approvals_router
from src.api.routes_payments import router as payments_router
from src.api.routes_groups import router as groups_router
from src.api.routes_enrollments import router as enrollments_router
from src.auth.routes import router as auth_router
from src.config import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

GMT = tz("GMT")
scheduler = BackgroundScheduler(timezone=GMT)

# Simple in-memory rate limiter
class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
    
    def is_allowed(self, client_ip: str) -> bool:
        now = time()
        minute_ago = now - 60
        # Clean old requests
        self.requests[client_ip] = [t for t in self.requests[client_ip] if t > minute_ago]
        # Check limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            return False
        self.requests[client_ip].append(now)
        return True

rate_limiter = RateLimiter(requests_per_minute=60)


def run_scheduled_job():
    """Run the daily individual reminders job."""
    from src.database import get_db
    from src.automation.scheduler import send_reminders

    logger.info("Scheduled daily reminders job firing.")
    db = get_db()
    send_reminders(db)


def run_ielts_reminder_job():
    """Run the IELTS daily reminder at 5am GMT."""
    import asyncio
    from src.automation.ielts_reminder import send_ielts_reminder_scheduled

    logger.info("Scheduled IELTS reminder job firing (5am GMT).")
    asyncio.run(send_ielts_reminder_scheduled())


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    
    # Daily individual reminders at configured time (GMT)
    scheduler.add_job(
        run_scheduled_job,
        CronTrigger(hour=settings.job_hour, minute=settings.job_minute, timezone=GMT),
        id="daily_reminders",
        replace_existing=True,
    )
    
    # IELTS daily reminder at 5am GMT
    scheduler.add_job(
        run_ielts_reminder_job,
        CronTrigger(hour=5, minute=0, timezone=GMT),
        id="ielts_reminder",
        replace_existing=True,
    )
    
    scheduler.start()
    logger.info(f"Scheduler started. Daily reminders at {settings.job_hour:02d}:{settings.job_minute:02d} GMT. IELTS reminder at 05:00 GMT.")
    
    yield
    
    scheduler.shutdown()
    logger.info("Scheduler shut down.")


app = FastAPI(
    title="Global Learning Hub Automation",
    description="WhatsApp-based Learning Management System",
    version="1.0.0",
    lifespan=lifespan,
)

# Rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    # Skip rate limiting for health checks and webhooks
    if request.url.path in ("/health", "/health/detailed") or request.url.path.startswith("/webhooks/"):
        return await call_next(request)
    
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")
    
    return await call_next(request)

# CORS configuration - restrict to frontend origin in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://*.vercel.app"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(jobs_router)
app.include_router(reports_router)
app.include_router(webhooks_router)
app.include_router(students_router)
app.include_router(courses_router)
app.include_router(approvals_router)
app.include_router(payments_router)
app.include_router(groups_router)
app.include_router(enrollments_router)
app.include_router(auth_router)