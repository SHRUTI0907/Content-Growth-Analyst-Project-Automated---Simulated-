import os
import requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("HUBSPOT_API_KEY")

response = requests.get(
    "https://api.hubapi.com/crm/v3/objects/contacts",
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
)

print(f"Status code: {response.status_code}")
print(f"Response: {response.json()}")