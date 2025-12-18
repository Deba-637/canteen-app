import app
import json

def test_admin_login():
    client = app.app.test_client()
    
    print("Testing Admin Login...")
    response = client.post('/api/login', 
                           data=json.dumps({'role': 'admin', 'username': 'admin', 'password': 'admin123'}),
                           content_type='application/json')
    
    print(f"Status: {response.status_code}")
    print(f"Data: {response.data.decode('utf-8')}")
    
    if response.status_code == 200:
        print("PASS")
    else:
        print("FAIL")

if __name__ == '__main__':
    try:
        test_admin_login()
    except Exception as e:
        print(f"CRITICAL EXCEPTION: {e}")
