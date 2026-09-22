"""Central configuration.

All settings come from environment variables (loaded via .env).
Nothing is hardcoded - no API key or credential ever appears in source code.
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    supabase_url: str = ""
    supabase_key: str = ""

    active_channel: Literal["whatsapp", "telegram", "email", "sms"] = "whatsapp"
    backup_channel: Literal["whatsapp", "telegram", "email", "sms"] = "telegram"

    whatsapp_token: str = ""
    whatsapp_phone_id: str = ""

    telegram_bot_token: str = ""
    telegram_admin_chat_id: str = ""

    email_api_key: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""

    sms_api_key: str = ""

    admin_email: str = ""
    admin_phone: str = ""

    job_hour: int = 8
    job_minute: int = 0
    rate_limit_delay_seconds: float = 60.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
