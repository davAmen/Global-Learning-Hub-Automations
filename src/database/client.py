"""Supabase connection client.

The client is created lazily and is a thin wrapper. In tests it is replaced
with a fake.
"""

from functools import lru_cache
from typing import Any

from supabase import create_client

from src.config import get_settings


class SupabaseClient:
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.supabase_url or not settings.supabase_key:
            raise RuntimeError(
                "SUPABASE_URL / SUPABASE_KEY missing. "
                "Copy .env.example to .env and fill in placeholders."
            )
        self._client: Any = create_client(settings.supabase_url, settings.supabase_key)

    def table(self, name: str) -> Any:
        return self._client.table(name)


@lru_cache
def get_db() -> SupabaseClient:
    return SupabaseClient()
