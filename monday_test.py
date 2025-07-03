#!/usr/bin/env python
"""Test script for Monday.com API integration."""

import os
import sys
import json
import requests
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskforge.settings')
django.setup()

from django.conf import settings

# Monday.com API configuration
MONDAY_API_URL = "https://api.monday.com/v2"
API_VERSION = "2023-10"
MONDAY_API_KEY = settings.MONDAY_API_KEY
MONDAY_BOARD_ID = settings.MONDAY_BOARD_ID
MONDAY_GROUP_ID = settings.MONDAY_GROUP_ID

def test_monday_connection():
    """Test connection to Monday.com API by fetching current user info."""
    
    if not MONDAY_API_KEY:
        print("ERROR: MONDAY_API_KEY is not set.")
        return False
        
    headers = {
        "Authorization": f"Bearer {MONDAY_API_KEY}",
        "Content-Type": "application/json",
        "API-Version": API_VERSION
    }
    
    query = """
    query {
      me {
        id
        name
        email
      }
    }
    """
    
    payload = {
        "query": query
    }
    
    print(f"Testing connection to Monday.com API...")
    try:
        response = requests.post(MONDAY_API_URL, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if "errors" in data:
            print(f"API returned errors: {data['errors']}")
            return False
            
        print(f"Connection successful! Logged in as: {data['data']['me']['name']}")
        return True
    except Exception as e:
        print(f"Connection failed: {str(e)}")
        return False

def test_create_item():
    """Test creating an item on Monday.com board using the correct mutation format."""
    
    if not MONDAY_API_KEY or not MONDAY_BOARD_ID or not MONDAY_GROUP_ID:
        print("ERROR: Missing required Monday.com configuration.")
        return False
        
    headers = {
        "Authorization": f"Bearer {MONDAY_API_KEY}",
        "Content-Type": "application/json",
        "API-Version": API_VERSION
    }
    
    # Mutation exactly matching the n8n production flow
    mutation = """
    mutation ($board:Int!, $group:String, $name:String!, $cols:JSON!){
      create_item(board_id:$board, group_id:$group, item_name:$name, column_values:$cols){ id }
    }
    """
    
    # Build column values
    column_values = {
        "text_mkr7jgkp": "Test User",
        "text_mkr0hqsb": "test@example.com",
        "status_1": {"label": "High"},
        "status": {"label": "Approved"},
        "long_text": "This is a test item created by the Django integration test script."
    }
    
    variables = {
        "board": int(MONDAY_BOARD_ID),
        "group": MONDAY_GROUP_ID,
        "name": "Test Item from Django Integration",
        "cols": json.dumps(column_values)  # JSON-encode once
    }
    
    payload = {
        "query": mutation,
        "variables": variables
    }
    
    print(f"Creating test item on Monday.com board {MONDAY_BOARD_ID}...")
    try:
        response = requests.post(MONDAY_API_URL, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if "errors" in data:
            print(f"API returned errors: {data['errors']}")
            return False
            
        item_id = data.get("data", {}).get("create_item", {}).get("id")
        if item_id:
            print(f"Item created successfully! Item ID: {item_id}")
            return True
        else:
            print("Item creation failed: No item ID returned.")
            return False
    except Exception as e:
        print(f"Item creation failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("Monday.com Integration Test")
    print("==========================")
    
    # Test connection
    if not test_monday_connection():
        print("Connection test failed. Exiting.")
        sys.exit(1)
    
    # Test item creation
    if not test_create_item():
        print("Item creation test failed. Exiting.")
        sys.exit(1)
    
    print("All tests passed successfully!") 