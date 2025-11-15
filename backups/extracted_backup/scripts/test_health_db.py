#!/usr/bin/env python3
"""Test /health/db Endpoint"""
import requests
import json

try:
    response = requests.get("http://localhost:8111/health/db", timeout=5)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
except Exception as e:
    print(f"Fehler: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print(f"Response Text: {e.response.text}")

