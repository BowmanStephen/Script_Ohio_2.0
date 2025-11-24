import os
from dotenv import load_dotenv
import cfbd

load_dotenv()

api_key = os.getenv('CFBD_API_KEY')

print(f"Key found: {bool(api_key)}")
if api_key:
    print(f"Key length: {len(api_key)}")
    print(f"Key starts with 'Bearer': {api_key.startswith('Bearer')}")
    print(f"Key starts with quote: {api_key.startswith(chr(34)) or api_key.startswith(chr(39))}")
    print(f"First 4 chars: {api_key[:4]}")
    print(f"Last 4 chars: {api_key[-4:]}")

    import requests
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    }
    url = "https://api.collegefootballdata.com/games?year=2024&week=1&seasonType=regular"
    try:
        response = requests.get(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:200]}")
    except Exception as e:
        print(f"Request Failed: {e}")
