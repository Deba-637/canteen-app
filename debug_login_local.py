# Helper Script to Debug Login
import requests
import json

def test_login():
    url = "http://localhost:5000/api/login"
    payload = {"role": "admin", "username": "admin", "password": "admin123"}
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_login()
