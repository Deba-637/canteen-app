import requests
import sys

BASE_URL = 'http://localhost:8000/api'

def test_sequential_ids():
    print("Testing Sequential IDs...")
    
    # 1. Login
    s = requests.Session()
    s.post(f'{BASE_URL}/login', json={'username': 'admin', 'password': 'admin123', 'role': 'admin'})
    
    # 2. Add 3 dummy students
    ids = []
    for i in range(3):
        res = s.post(f'{BASE_URL}/students', json={'name': f'SeqTest{i}', 'roll': f'SEQ{i}'})
        if res.status_code == 200:
            ids.append(res.json()['id'])
        else:
            print(f"Failed to add setup student: {res.text}")
            return

    print(f"Created IDs: {ids}")
    
    # 3. Delete the middle one
    middle_id = ids[1]
    print(f"Deleting ID: {middle_id}")
    s.delete(f'{BASE_URL}/students?id={middle_id}')
    
    # 4. Add new student - should take middle_id
    print("Adding new student (should reuse ID)...")
    res = s.post(f'{BASE_URL}/students', json={'name': 'GapFiller', 'roll': 'GAP01'})
    new_id = res.json()['id']
    
    if new_id == middle_id:
        print(f"✅ Success! Reused ID {new_id}")
    else:
        print(f"❌ Failed! Got ID {new_id}, expected {middle_id}")

    # Cleanup
    for i in ids + [new_id]:
         s.delete(f'{BASE_URL}/students?id={i}')

if __name__ == '__main__':
    test_sequential_ids()
