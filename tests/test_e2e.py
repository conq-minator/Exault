import os
import json
import pytest
from io import BytesIO
from pathlib import Path
from backend.app import create_app
import config

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_full_e2e_workflow(client, tmp_path):
    # 1. Upload
    # We will upload a dummy file that looks like a template
    # Since we need a real xlsx, we can create a tiny one or mock the analyzer.
    # Actually, we can use the `test_data` if available, or just create a dummy one.
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "DataSheet"
    ws.append(["SKU", "Name", "Price", "Description"])
    ws.append(["123", "", "", ""])
    ws.append(["456", "", "", ""])
    
    file_stream = BytesIO()
    wb.save(file_stream)
    file_stream.seek(0)
    
    response = client.post(
        '/api/upload',
        data={'file': (file_stream, 'test_template.xlsx')}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert 'session_id' in data
    
    session_id = data['session_id']
    
    # 2. Get Analysis
    response = client.get(f'/api/analysis/{session_id}')
    assert response.status_code == 200
    
    # 3. Generate Prompt
    response = client.get(f'/api/prompt/{session_id}')
    assert response.status_code == 200
    prompt_data = response.get_json()
    assert 'prompt' in prompt_data
    
    # 4. Validate JSON
    mock_json = [
        {"SKU": "123", "Name": "Product 1", "Price": 100, "Description": "A test product"},
        {"SKU": "456", "Name": "Product 2", "Price": "200", "Description": "Another test"}
    ]
    response = client.post(
        f'/api/validate/{session_id}',
        json={'raw_json': json.dumps(mock_json)}
    )
    assert response.status_code == 200
    val_data = response.get_json()
    assert val_data['is_valid'] is True # or False depending on rules, but it should process
    
    # 5. Get Preview
    response = client.get(f'/api/preview/{session_id}')
    assert response.status_code == 200
    preview_data = response.get_json()
    assert len(preview_data) == 2
    
    # 6. Update Preview Row
    response = client.put(
        f'/api/preview/{session_id}/row/0',
        json={"SKU": "123", "Name": "Product 1 Updated", "Price": 150, "Description": "A test product"}
    )
    assert response.status_code == 200
    
    # 7. Get Report
    response = client.get(f'/api/report/{session_id}?format=json')
    assert response.status_code == 200
    
    # 8. Export
    response = client.get(f'/api/export/{session_id}')
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    
    # 9. List Sessions
    response = client.get('/api/sessions')
    assert response.status_code == 200
    sessions = response.get_json()['sessions']
    assert any(s['session_id'] == session_id for s in sessions)
    
    # 10. Delete Session
    response = client.delete(f'/api/sessions/{session_id}')
    assert response.status_code == 200
