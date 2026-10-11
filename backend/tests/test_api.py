"""Tests for API endpoints."""

from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import pytest


def test_health():
    from src.main import app
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_health_detailed():
    from src.main import app
    client = TestClient(app)
    with patch('src.api.routes_health.get_db') as mock_get_db, \
         patch('src.api.routes_health.get_settings') as mock_get_settings:
        mock_db = MagicMock()
        mock_db.table.return_value.select.return_value.limit.return_value.execute.return_value = MagicMock(data=[])
        mock_get_db.return_value = mock_db
        
        # Mock settings with required values
        mock_settings = MagicMock()
        mock_settings.supabase_url = "https://test.supabase.co"
        mock_settings.supabase_key = "test_key"
        mock_get_settings.return_value = mock_settings
        
        r = client.get("/health/detailed")
        assert r.status_code == 200
        data = r.json()
        assert data["service"] == "ok"
        assert data["database"] == "ok"
        assert data["config"] == "ok"


def test_health_detailed_db_failure():
    from src.main import app
    client = TestClient(app)
    with patch('src.api.routes_health.get_db') as mock_get_db:
        mock_get_db.side_effect = Exception("DB connection failed")
        
        r = client.get("/health/detailed")
        assert r.status_code == 503
        data = r.json()
        # The detail should contain the checks dict
        if "detail" in data:
            assert data["detail"]["database"] != "ok"
        else:
            assert data["database"] != "ok"


@patch("src.api.routes_jobs.get_db")
@patch("src.api.routes_jobs.send_reminders", return_value=3)
def test_run_daily_job(mock_send, mock_db):
    from src.main import app
    client = TestClient(app)
    r = client.post("/run-daily-job")
    assert r.status_code == 200
    assert r.json()["reminders_sent"] == 3


@patch("src.api.routes_reports.get_db")
@patch("src.api.routes_reports.build_report")
def test_reports_today(mock_build, mock_db):
    from src.main import app
    client = TestClient(app)
    mock_build.return_value = {"date": "2026-09-18", "courses_today": 1, "total_enrolled": 5}
    r = client.get("/reports/today")
    assert r.status_code == 200
    assert r.json()["courses_today"] == 1


@patch("src.api.routes_students.get_db")
def test_students_list(mock_get_db):
    from src.main import app
    client = TestClient(app)
    mock_db = MagicMock()
    mock_db.table.return_value.select.return_value.execute.return_value.data = [
        {"id": "1", "name": "Test Student", "phone": "+233548014157", "email": "test@example.com", "created_at": "2026-01-01T00:00:00"}
    ]
    mock_get_db.return_value = mock_db
    r = client.get("/students")
    assert r.status_code == 200
    assert len(r.json()["students"]) == 1


@patch("src.api.routes_courses.get_db")
def test_courses_list(mock_get_db):
    from src.main import app
    client = TestClient(app)
    mock_db = MagicMock()
    # Mock the query chain: select().eq().order().execute()
    mock_eq = MagicMock()
    mock_eq.order.return_value.execute.return_value.data = [
        {"id": "1", "name": "Test Course", "start_date": "2026-10-15", "class_time": "18:00:00", "created_at": "2026-01-01T00:00:00"}
    ]
    mock_select = MagicMock()
    mock_select.eq.return_value = mock_eq
    mock_db.table.return_value.select.return_value = mock_select
    mock_get_db.return_value = mock_db
    r = client.get("/courses")
    assert r.status_code == 200
    assert len(r.json()["courses"]) == 1


def test_rate_limiting():
    """Test that rate limiting works."""
    from src.main import app, rate_limiter
    from fastapi.testclient import TestClient
    from fastapi.exceptions import HTTPException
    import pytest
    
    client = TestClient(app)
    
    # Clear rate limiter
    rate_limiter.requests.clear()
    
    # Health endpoint is excluded from rate limiting
    # Test with students endpoint which is rate limited
    with patch('src.api.routes_students.get_db') as mock_get_db:
        mock_db = MagicMock()
        mock_db.table.return_value.select.return_value.execute.return_value.data = []
        mock_get_db.return_value = mock_db
        
        # Make requests up to limit (60 per minute)
        for i in range(60):
            r = client.get("/students")
            assert r.status_code == 200
        
        # Next request should be rate limited - expect HTTPException
        with pytest.raises(HTTPException) as exc_info:
            client.get("/students")
        assert exc_info.value.status_code == 429
    
    # Clean up
    rate_limiter.requests.clear()


def test_cors_headers():
    """Test CORS headers are present."""
    from src.main import app
    client = TestClient(app)
    # Use GET since OPTIONS might not be allowed
    r = client.get("/health", headers={"Origin": "http://localhost:3000"})
    assert r.status_code == 200
    # Check that CORS middleware is working (allow-origin should be present for allowed origins)
    assert "access-control-allow-origin" in r.headers