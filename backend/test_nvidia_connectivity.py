#!/usr/bin/env python3
"""Simple NVIDIA API connectivity test"""

import os
import sys
import urllib.request
import json

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def test_nvidia_connectivity():
    """Test basic connectivity to NVIDIA API endpoint"""
    api_key = os.getenv("NVIDIA_API_KEY")
    base_url = os.getenv("NVIDIA_API_BASE_URL", "https://integrate.api.nvidia.com/v1")
    
    if not api_key:
        print("ERROR: NVIDIA_API_KEY not set")
        return False
        
    if not api_key.startswith("nvapi-"):
        print("ERROR: NVIDIA_API_KEY doesn't appear to be valid format")
        return False
    
    print(f"Testing connectivity to: {base_url}")
    print(f"API Key: {api_key[:20]}...{api_key[-10:] if len(api_key) > 30 else api_key}")
    
    # Try to make a simple request to the models endpoint
    url = f"{base_url}/models"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        response = urllib.request.urlopen(req, timeout=10)
        data = json.loads(response.read().decode())
        print(f"SUCCESS: Connected to NVIDIA API")
        print(f"Response status: {response.getcode()}")
        if 'data' in data:
            print(f"Number of models available: {len(data['data'])}")
            if len(data['data']) > 0:
                print(f"First model: {data['data'][0].get('id', 'Unknown')}")
        return True
    except urllib.error.HTTPError as e:
        print(f"HTTP ERROR: {e.getcode()} {e.reason}")
        print(f"Response: {e.read().decode()[:200]}")
        return False
    except Exception as e:
        print(f"CONNECTIVITY ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_nvidia_connectivity()
    sys.exit(0 if success else 1)