"""
ExcelPlorer — Tests for Export API Route

Tests for backend/api/export.py.
"""

import json
from pathlib import Path
import pytest
from flask import Flask

import config
from backend.api.export import export_bp


@pytest.fixture
def app():
    """Create a Flask app with the export blueprint registered."""
    app = Flask(__name__)
    app.register_blueprint(export_bp)
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def valid_session(tmp_path, monkeypatch):
    """Mocks a session directory with required files."""
    session_id = "test-session-123"
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    
    # Patch the config directory
    monkeypatch.setattr(config, "SESSIONS_DIR", sessions_dir)
    
    session_dir = sessions_dir / session_id
    session_dir.mkdir()
    
    # 1. Dummy template
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Data Entry"
    ws.append(["SKU", "Color"])
    ws.append(["123", ""])
    wb.save(session_dir / "template.xlsx")
    
    # 2. Dummy schema
    schema = {
        "filename": "my_test.xlsx",
        "file_size": 100,
        "file_extension": ".xlsx",
        "sheet_count": 1,
        "sheets": [{
            "name": "Data Entry",
            "index": 0,
            "is_visible": True,
            "is_data_sheet": True,
            "header_row": 1,
            "columns": [
                {"name": "SKU", "index": 1, "data_type": "string", "is_required": True},
                {"name": "Color", "index": 2, "data_type": "string", "is_required": True}
            ]
        }]
    }
    with open(session_dir / "schema.json", "w") as f:
        json.dump(schema, f)
        
    # 3. Dummy input.json
    data = [{"SKU": "123", "Color": "Red"}]
    with open(session_dir / "input.json", "w") as f:
        json.dump(data, f)
        
    return session_id, session_dir


class TestExportAPI:

    def test_export_success(self, client, valid_session):
        session_id, session_dir = valid_session
        
        response = client.get(f"/api/export/{session_id}")
        
        assert response.status_code == 200
        assert response.headers["Content-Type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert "attachment; filename=my_test_Filled.xlsx" in response.headers["Content-Disposition"]
        
        # Verify output file was created
        assert (session_dir / "output.xlsx").exists()

    def test_export_session_not_found(self, client, monkeypatch, tmp_path):
        monkeypatch.setattr(config, "SESSIONS_DIR", tmp_path)
        
        response = client.get("/api/export/fake-session")
        assert response.status_code == 404

    def test_export_missing_template(self, client, valid_session):
        session_id, session_dir = valid_session
        
        # Delete template
        (session_dir / "template.xlsx").unlink()
        
        response = client.get(f"/api/export/{session_id}")
        assert response.status_code == 400
        data = response.get_json()
        assert "template is missing" in data["error"]

    def test_export_missing_input(self, client, valid_session):
        session_id, session_dir = valid_session
        
        # Delete input.json
        (session_dir / "input.json").unlink()
        
        response = client.get(f"/api/export/{session_id}")
        assert response.status_code == 400
        data = response.get_json()
        assert "Validated data is missing" in data["error"]
