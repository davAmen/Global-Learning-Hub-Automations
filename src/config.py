"""Central application configuration loaded from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    supabase_url: str = ""
    supabase_key: str = ""
    admin_api_key: str = ""

    active_channel: Literal["whatsapp", "telegram"] = "whatsapp"
    backup_channel: Literal["whatsapp", "telegram"] = "telegram"

    whatsapp_token: str = ""
    whatsapp_phone_id: str = ""
    whatsapp_graph_version: str = "v23.0"

    telegram_bot_token: str = ""
    telegram_admin_chat_id: str = ""

    email_api_key: str = ""
    smtp_host: str = ""
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_username: str = ""
    smtp_password: str = ""

    sms_api_key: str = ""
    admin_email: str = ""
    admin_phone: str = ""

    timezone: str = "Africa/Accra"
    enable_scheduler: bool = False
    job_hour: int = Field(default=8, ge=0, le=23)
    job_minute: int = Field(default=0, ge=0, le=59)
    rate_limit_delay_seconds: float = Field(default=1.0, ge=0.0, le=3600.0)


@lru_cache
def get_settings() -> Settings:
    return Settings()
