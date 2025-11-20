"""
Test script for drift detection.
"""

import requests
import json
import time

DRIFT_API_URL = "http://localhost:5001"

def test_health():
    """Test health endpoint."""
    response = requests.get(f"{DRIFT_API_URL}/health")
    print(f"Health check: {response.status_code} - {response.json()}")
    return response.status_code == 200

def test_statistics():
    """Test statistics endpoint."""
    response = requests.get(f"{DRIFT_API_URL}/api/drift/statistics")
    print(f"\nDrift Statistics:")
    print(json.dumps(response.json(), indent=2))
    return response.status_code == 200

def test_alerts():
    """Test alerts endpoint."""
    response = requests.get(f"{DRIFT_API_URL}/api/drift/alerts?limit=10")
    print(f"\nDrift Alerts:")
    result = response.json()
    print(f"Total alerts: {result.get('count', 0)}")
    
    if result.get('alerts'):
        print("\nRecent alerts:")
        for alert in result['alerts'][:5]:
            print(f"  - Alert ID: {alert.get('id')}")
            print(f"    Timestamp: {alert.get('timestamp')}")
            print(f"    Drift Score: {alert.get('drift_score', 0):.3f}")
            print(f"    Features: {alert.get('drifted_features', 'N/A')}")
            print(f"    Acknowledged: {alert.get('acknowledged', 0)}")
            print()
    else:
        print("  No alerts yet. Process more documents to detect drift.")
    
    return response.status_code == 200

def acknowledge_alert(alert_id: int):
    """Acknowledge an alert."""
    response = requests.post(f"{DRIFT_API_URL}/api/drift/alert/{alert_id}/acknowledge")
    if response.status_code == 200:
        print(f"[OK] Alert {alert_id} acknowledged")
    else:
        print(f"[FAIL] Failed to acknowledge alert: {response.text}")
    return response.status_code == 200

if __name__ == '__main__':
    print("=" * 60)
    print("Drift Detection API Test")
    print("=" * 60)
    
    if not test_health():
        print("\n[FAIL] API not running. Start it with:")
        print("  python src/drift_api.py")
        exit(1)
    
    test_statistics()
    test_alerts()
    
    print("\n" + "=" * 60)
    print("Note: Drift detection requires processing many documents")
    print("to establish baseline and detect changes.")
    print("=" * 60)

