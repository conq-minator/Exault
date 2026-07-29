"""
ExcelPlorer — Tests for Report API Route

Tests for backend/api/report.py.
"""

import json
from pathlib import Path
import pytest
from flask import Flask

import config
from backend.api.report import report_bp


@pytest.fixture
def app():
    """Create a Flask app with the report blueprint registered."""
    app = Flask(__name__)
    app.register_blueprint(report_bp)
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def valid_session(tmp_path, monkeypatch):
    """Mocks a session directory with a report.json."""
    session_id = "test-session-123"
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    
    monkeypatch.setattr(config, "SESSIONS_DIR", sessions_dir)
    
    session_dir = sessions_dir / session_id
    session_dir.mkdir()
    
    # Dummy report
    payload = {
        "is_valid": True,
        "item_count": 10,
        "report": {
            "issues": []
        }
    }
    with open(session_dir / "report.json", "w") as f:
        json.dump(payload, f)
        
    return session_id, session_dir


class TestReportAPI:

    def test_report_json(self, client, valid_session):
        session_id, _ = valid_session
        
        response = client.get(f"/api/report/{session_id}") # defaults to json
        assert response.status_code == 200
        assert response.headers["Content-Type"] == "application/json"
        
        data = response.get_json()
        assert data["item_count"] == 10

    def test_report_txt(self, client, valid_session):
        session_id, _ = valid_session
        
        response = client.get(f"/api/report/{session_id}?format=txt")
        assert response.status_code == 200
        assert "text/plain" in response.headers["Content-Type"]
        
        text = response.get_data(as_text=True)
        assert "EXCELPLORER VALIDATION REPORT" in text
        assert "Total Rows:  10" in text

    def test_report_html(self, client, valid_session):
        session_id, _ = valid_session
        
        response = client.get(f"/api/report/{session_id}?format=html")
        assert response.status_code == 200
        assert "text/html" in response.headers["Content-Type"]
        
        html = response.get_data(as_text=True)
        assert "<html>" in html
        assert "Total Rows: <strong>10</strong>" in html

    def test_report_invalid_format(self, client, valid_session):
        session_id, _ = valid_session
        
        response = client.get(f"/api/report/{session_id}?format=pdf")
        assert response.status_code == 400
        assert "Invalid format" in response.get_json()["error"]

    def test_report_session_not_found(self, client, monkeypatch, tmp_path):
        monkeypatch.setattr(config, "SESSIONS_DIR", tmp_path)
        
        response = client.get("/api/report/fake-session")
        assert response.status_code == 404

    def test_report_not_generated_yet(self, client, valid_session):
        session_id, session_dir = valid_session
        
        (session_dir / "report.json").unlink()
        
        response = client.get(f"/api/report/{session_id}")
        assert response.status_code == 404
        assert "Report not found" in response.get_json()["error"]
