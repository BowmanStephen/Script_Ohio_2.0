import os
from dotenv import load_dotenv

# Load .env explicitly to check file content
load_dotenv()

key = os.getenv("CFBD_API_KEY")

if key:
    print(f"CFBD_API_KEY found in environment: {key[:4]}...{key[-4:]}")
    if key.startswith("Bearer "):
        print("Warning: Key starts with 'Bearer '. This might be the issue if the client adds it automatically.")
else:
    print("CFBD_API_KEY NOT found in environment.")

# Check if .env file exists
if os.path.exists(".env"):
    print(".env file exists.")
    with open(".env", "r") as f:
        content = f.read()
        if "CFBD_API_KEY" in content:
            print("CFBD_API_KEY is present in .env file.")
        else:
            print("CFBD_API_KEY is NOT present in .env file.")
else:
    print(".env file does NOT exist.")
