"""Tests for safe and usable application configuration."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from src.config import Settings


def test_example_environment_file_loads_with_defaults() -> None:
    example_env = Path(__file__).resolve().parents[1] / ".env.example"

    settings = Settings(_env_file=example_env)

    assert settings.smtp_port == 587
    assert settings.rate_limit_delay_seconds == 60


@pytest.mark.parametrize(
    "value",
    [0, -1, float("inf"), float("nan")],
)
def test_send_delay_must_be_positive_and_finite(value: float) -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, rate_limit_delay_seconds=value)


@pytest.mark.parametrize(
    "setting,value",
    [
        ("job_hour", -1),
        ("job_hour", 24),
        ("job_minute", -1),
        ("job_minute", 60),
        ("smtp_port", 0),
        ("smtp_port", 65536),
    ],
)
def test_time_and_smtp_port_must_be_in_valid_ranges(setting: str, value: int) -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **{setting: value})
