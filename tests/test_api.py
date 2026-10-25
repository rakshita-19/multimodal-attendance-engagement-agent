import pytest
import json
import tempfile
from pathlib import Path
from app import create_app
from backend.config import Config
from backend.database.db import init_db

@pytest.fixture
def client(monkeypatch):
    """Create Flask test client with an isolated temporary SQLite database."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_db = f.name

    init_db(temp_db, Config.SCHEMA_PATH)
    monkeypatch.setattr(Config, "DATABASE_PATH", temp_db)

    app = create_app({"TESTING": True})
    with app.test_client() as client:
        yield client

    try:
        Path(temp_db).unlink(missing_ok=True)
    except Exception:
        pass

def test_api_health(client):
    """Test /api/health endpoint."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "healthy"
    assert "Multimodal" in data["service"]

def test_frontend_route(client):
    """Test that root route serves the dashboard index.html."""
    res = client.get("/")
    assert res.status_code == 200
    assert b"Multimodal Attendance & Engagement Agent" in res.data
    assert b"chart-engagement-timeline" in res.data

def test_session_crud_api(client):
    """Test session creation, listing, retrieval, and deletion."""
    # 1. Create
    res = client.post("/api/sessions", json={"title": "Computer Networks Lab", "notes": "Room 302"})
    assert res.status_code == 201
    sess = res.get_json()["session"]
    sess_id = sess["id"]
    assert sess["title"] == "Computer Networks Lab"

    # 2. Get list
    res = client.get("/api/sessions")
    assert res.status_code == 200
    sessions = res.get_json()["sessions"]
    assert any(s["id"] == sess_id for s in sessions)

    # 3. Get single
    res = client.get(f"/api/sessions/{sess_id}")
    assert res.status_code == 200
    assert res.get_json()["session"]["id"] == sess_id

    # 4. Delete
    res = client.delete(f"/api/sessions/{sess_id}")
    assert res.status_code == 200
    assert res.get_json()["status"] == "success"

def test_demo_pipeline_and_analytics_flow(client):
    """Test full multimodal pipeline execution via /process-demo, attendance mapping, and CSV exports."""
    # 1. Create session
    res = client.post("/api/sessions", json={"title": "Demo Classroom Session"})
    sess_id = res.get_json()["session"]["id"]

    # 2. Run demo pipeline (generates 15s synthetic classroom video + audio and runs full agent)
    res = client.post(f"/api/sessions/{sess_id}/process-demo")
    assert res.status_code == 200
    body = res.get_json()
    assert body["status"] == "success"
    report = body["report"]
    assert report["session"]["status"] == "completed"
    assert len(report["attendance"]) > 0
    assert len(report["intervals"]) > 0
    assert len(report["recommendations"]) > 0

    # 3. Test Teacher Manual Name Mapping
    first_track_id = report["attendance"][0]["track_id"]
    patch_res = client.patch(
        f"/api/sessions/{sess_id}/attendance/{first_track_id}",
        json={"student_name": "Maya Lin", "notes": "Verified by instructor"}
    )
    assert patch_res.status_code == 200
    assert patch_res.get_json()["record"]["student_name"] == "Maya Lin"

    # 4. Test Analytics endpoint
    analytics_res = client.get(f"/api/sessions/{sess_id}/analytics")
    assert analytics_res.status_code == 200
    ana_data = analytics_res.get_json()
    assert "kpis" in ana_data
    assert "trends" in ana_data
    assert "student_summary" in ana_data
    assert ana_data["kpis"]["total_tracked"] > 0

    # 5. Test CSV exports
    csv_att = client.get(f"/api/sessions/{sess_id}/export/attendance.csv")
    assert csv_att.status_code == 200
    assert "text/csv" in csv_att.headers["Content-Type"]
    assert b"Track ID" in csv_att.data

    csv_ana = client.get(f"/api/sessions/{sess_id}/export/analytics.csv")
    assert csv_ana.status_code == 200
    assert "text/csv" in csv_ana.headers["Content-Type"]
    assert b"Interval Index" in csv_ana.data
