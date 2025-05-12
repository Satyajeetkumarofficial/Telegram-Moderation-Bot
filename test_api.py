import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API token from environment variables
API_TOKEN = os.getenv("API_TOKEN")

# Base URL for API
BASE_URL = "http://localhost:8000/api"

# Headers for API requests
headers = {
    "X-API-Key": API_TOKEN
}

def test_logs_endpoint():
    """Test the logs endpoint"""
    response = requests.get(f"{BASE_URL}/logs", headers=headers)
    if response.status_code == 200:
        print("✅ Logs endpoint is working")
        logs = response.json()
        print(f"   Found {len(logs)} logs")
    else:
        print(f"❌ Logs endpoint failed with status code {response.status_code}")
        print(f"   Response: {response.text}")

def test_groups_endpoint():
    """Test the groups endpoint"""
    response = requests.get(f"{BASE_URL}/groups", headers=headers)
    if response.status_code == 200:
        print("✅ Groups endpoint is working")
        groups = response.json()
        print(f"   Found {len(groups)} groups")
    else:
        print(f"❌ Groups endpoint failed with status code {response.status_code}")
        print(f"   Response: {response.text}")

def test_unauthorized_access():
    """Test unauthorized access to the API"""
    response = requests.get(f"{BASE_URL}/logs")
    if response.status_code == 401:
        print("✅ Unauthorized access test passed")
    else:
        print(f"❌ Unauthorized access test failed with status code {response.status_code}")
        print(f"   Response: {response.text}")

if __name__ == "__main__":
    print("Testing API endpoints...")
    test_logs_endpoint()
    test_groups_endpoint()
    test_unauthorized_access()
    print("API tests completed")