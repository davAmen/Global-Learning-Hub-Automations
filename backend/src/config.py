"""Central configuration.

All settings come from environment variables (loaded via .env).
Nothing is hardcoded - no API key or credential ever appears in source code.
"""

from functools import lru_cache
from typing import Literal, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""

    # Active channel
    active_channel: Literal["whatsapp", "telegram", "email", "sms"] = "whatsapp"
    backup_channel: Literal["whatsapp", "telegram", "email", "sms"] = "telegram"

    # WasenderAPI
    wasender_api_key: str = ""
    wasender_base_url: str = "https://www.wasenderapi.com"
    wasender_webhook_secret: str = ""

    # Telegram (backup)
    telegram_bot_token: str = ""
    telegram_admin_chat_id: str = ""

    # Email (backup)
    email_api_key: str = ""
    smtp_host: str = ""
    smtp_port: Optional[int] = 587
    smtp_username: str = ""
    smtp_password: str = ""

    # SMS (backup)
    sms_api_key: str = ""

    # Admin contact
    admin_email: str = ""
    admin_phone: str = ""

    # Scheduler
    job_hour: int = 8
    job_minute: int = 0
    rate_limit_delay_seconds: float = 6.0

    # IELTS-specific (can be overridden in .env)
    ielts_course_name: str = "IELTS Preparation (Oct 15-30, 6-8pm GMT)"
    ielts_announcement_group_jid: str = "120363418173591450@g.us"
    ielts_proof_group_jid: str = "120363428841556134@g.us"
    ielts_class_access_group_jid: str = "120363413380837553@g.us"
    ielts_proof_group_url: str = "https://chat.whatsapp.com/IPtb2v6EzQUJ6LGLrObDrw"
    ielts_class_access_group_url: str = "https://chat.whatsapp.com/HZpPBTfKDQq7aVYOgpUFkw"
    ielts_start_date: str = "2026-10-15"
    ielts_end_date: str = "2026-10-30"
    ielts_class_time: str = "18:00-20:00 GMT"
    ielts_momo_number: str = "+233548014157"
    ielts_telecel_number: str = "+23333206967251"
    ielts_reference: str = "ILETS"
    ielts_amount: float = 100.0
    ielts_currency: str = "GHS"

    # Feature flags
    auto_approve_reminders: bool = False
    enable_ielts_reminders: bool = True

    # Payment providers
    paystack_public_key: str = ""
    paystack_secret_key: str = ""
    paystack_webhook_secret: str = ""

    seefcash_public_key: str = ""
    seefcash_secret_key: str = ""
    seefcash_webhook_secret: str = ""

    stripe_public_key: str = ""
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""

    # JWT Authentication
    jwt_secret_key: str = ""

    # App base URL for callbacks
    app_base_url: str = "http://localhost:3000"

    @field_validator("smtp_port", mode="before")
    @classmethod
    def parse_smtp_port(cls, v):
        if v is None or v == "":
            return 587
        return int(v)


@lru_cache
def get_settings() -> Settings:
    return Settings()