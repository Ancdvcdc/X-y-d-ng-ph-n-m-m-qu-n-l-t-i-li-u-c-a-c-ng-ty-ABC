import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from server import main
    from fastapi.testclient import TestClient
except Exception as e:
    print('IMPORT_ERROR', type(e).__name__, e)
    raise

client = TestClient(main.app)
response = client.get('/users', params={'admin_username': 'admin'})
print('status', response.status_code)
try:
    print('json', response.json())
except Exception as e:
    print('json_parse_error', e)
    print('text', response.text)
