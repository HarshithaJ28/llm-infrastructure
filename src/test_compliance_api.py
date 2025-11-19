"""
Test script for Compliance API.
"""

import requests
import json

API_URL = "http://localhost:5000"

def test_health():
    """Test health endpoint."""
    response = requests.get(f"{API_URL}/health")
    print(f"Health check: {response.status_code} - {response.json()}")
    return response.status_code == 200

def test_query():
    """Test compliance query."""
    query = {
        "status": "success",
        "limit": 10
    }
    response = requests.post(f"{API_URL}/api/compliance/query", json=query)
    print(f"\nQuery Results:")
    print(json.dumps(response.json(), indent=2))
    return response.status_code == 200

def test_statistics():
    """Test statistics endpoint."""
    response = requests.get(f"{API_URL}/api/compliance/statistics")
    print(f"\nStatistics:")
    print(json.dumps(response.json(), indent=2))
    return response.status_code == 200

def test_get_request(request_id: str):
    """Test getting specific request."""
    response = requests.get(f"{API_URL}/api/compliance/request/{request_id}")
    print(f"\nRequest Details:")
    print(json.dumps(response.json(), indent=2))
    return response.status_code == 200

if __name__ == '__main__':
    print("=" * 60)
    print("Compliance API Test")
    print("=" * 60)
    
    if not test_health():
        print("\n❌ API not running. Start it with:")
        print("  python src/compliance_api.py")
        exit(1)
    
    test_statistics()
    test_query()
    
    # Test with a specific request ID (if you have one)
    # test_get_request("your-request-id-here")

