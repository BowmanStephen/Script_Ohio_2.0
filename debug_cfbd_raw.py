import requests

API_KEY = "3nSBeJV4ODZlJLxQZ/H0vWG3DRAfTSPU2PporK/5K+BJininva/bPx5G4iNjeOsb"
URL = "https://api.collegefootballdata.com/games?year=2024&week=1&team=Ohio%20State"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "accept": "application/json"
}

print(f"Testing raw request to {URL}")
try:
    response = requests.get(URL, headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Success!")
        print(response.json()[0]['home_team'])
    else:
        print(f"❌ Failed: {response.text}")
except Exception as e:
    print(f"Error: {e}")

