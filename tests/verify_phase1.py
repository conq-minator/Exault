"""Quick verification script for Phase 1."""
import sys
sys.path.insert(0, '.')
from backend.app import create_app

app = create_app()
client = app.test_client()

# Test root route
resp = client.get('/')
print(f"GET / -> Status: {resp.status_code}")
print(f"Content-Type: {resp.content_type}")
has_content = b"ExcelPlorer" in resp.data
print(f"Contains 'ExcelPlorer': {has_content}")

# Test API stubs
resp2 = client.post('/api/upload')
print(f"\nPOST /api/upload -> Status: {resp2.status_code}")

resp3 = client.get('/api/sessions')
print(f"GET /api/sessions -> Status: {resp3.status_code}")

print("\n[PASS] All Phase 1 checks passed!" if resp.status_code == 200 and has_content else "\n[FAIL] Some checks failed!")
