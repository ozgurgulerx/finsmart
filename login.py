import os

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://dev-datauploadapi.finsmart.ai"

# Credentials from .env
API_KEY = os.getenv("API_KEY")
PASSWORD = os.getenv("PASSWORD")
COMPANY_GUID = os.getenv("COMPANY_GUID")


def login(api_key: str, password: str) -> str:
    """Login to Finsmart API and return the token."""
    response = requests.post(
        f"{BASE_URL}/login",
        json={"apiKey": api_key, "password": password}
    )
    response.raise_for_status()
    data = response.json()
    print("Login response:", data)
    return data.get("token") or data  # adjust based on actual response structure


def analyze_data(token: str, company_guid: str) -> dict:
    """Call analyze-data endpoint with Bearer token."""
    response = requests.post(
        f"{BASE_URL}/ai-insight/analyze-data",
        headers={"Authorization": f"Bearer {token}"},
        json={"CompanyGuid": company_guid}
    )
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    import json
    
    # Step 1: Login
    token = login(API_KEY, PASSWORD)
    print(f"Token: {token}\n")
    
    # Step 2: Analyze data
    if token:
        result = analyze_data(token, COMPANY_GUID)
        
        # Write to file
        with open("output.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print("Response saved to output.json")
