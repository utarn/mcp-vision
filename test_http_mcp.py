#!/usr/bin/env python3
"""
Test script to verify MCP Vision HTTP server functionality
"""
import requests
import json

BASE_URL = "http://localhost:8080"

def test_health():
    """Test health endpoint"""
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")
    return response.status_code == 200

def test_list_tools():
    """Test tools listing endpoint"""
    print("Testing tools listing...")
    response = requests.get(f"{BASE_URL}/tools")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Available tools: {len(data.get('tools', []))}")
    for tool in data.get('tools', []):
        print(f"  - {tool['name']}: {tool.get('description', 'No description')}")
    print()
    return response.status_code == 200

def test_call_tool():
    """Test calling a tool"""
    print("Testing tool invocation...")
    # Test with a sample image
    test_data = {
        "image_path": "images/sample.png",
        "min_confidence": 0.0
    }
    
    response = requests.post(
        f"{BASE_URL}/call/read_text_from_image",
        json=test_data
    )
    print(f"Status: {response.status_code}")
    data = response.json()
    
    if data.get('isError'):
        print(f"Error: {data.get('content', [{}])[0].get('text', 'Unknown error')}")
    else:
        print(f"Success! Extracted text:")
        for item in data.get('content', []):
            print(f"  {item.get('text', '')[:100]}...")
    print()
    return response.status_code == 200

def main():
    """Run all tests"""
    print("=" * 60)
    print("MCP Vision HTTP Server Test")
    print("=" * 60)
    print()
    
    try:
        # Test health
        if not test_health():
            print("❌ Health check failed")
            return
        
        # Test tools listing
        if not test_list_tools():
            print("❌ Tools listing failed")
            return
        
        # Test tool invocation
        if test_call_tool():
            print("✅ All tests passed!")
        else:
            print("❌ Tool invocation failed")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Is it running on port 8080?")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    main()