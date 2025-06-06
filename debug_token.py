#!/usr/bin/env python3
"""Debug token parsing"""

import sys
import requests
import traceback

def test_token_parsing():
    """Test token parsing directly"""
    token = "user_alice|||https://generativelanguage.googleapis.com/v1beta/openai/|||gemini-2.0-flash-exp|||REDACTED_API_KEY"
    
    print(f"Testing token: {token}")
    print("=" * 50)
    
    # Test API call
    url = "http://localhost:8050/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "gemini-2.0-flash-exp",
        "messages": [
            {"role": "user", "content": "Hello, test message"}
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code != 200:
            print(f"Response Headers: {dict(response.headers)}")
            
    except Exception as e:
        print(f"Request error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_token_parsing()
