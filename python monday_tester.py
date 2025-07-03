import requests
import json
import sys # For exiting the script gracefully on critical errors
import datetime # To make the item title unique if needed later

# --- START: Your API Key (JWT) Here ---
# 1. PASTE YOUR MONDAY.COM API KEY BELOW, INSIDE THE QUOTES.
#    This is the JWT key you provided.
#    DO NOT include "Bearer " in front of the key here. The script adds that.
MONDAY_API_KEY = "eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjUxMjY3Mjg4OCwiYWFpIjoxMSwidWlkIjo3NTc1NzcxNiwiaWFkIjoiMjAyNS0wNS0xNFQxMTowNzowMS4wMDBaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6Mjg0NjkxNTUsInJnbiI6InVzZTEifQ.DiRDF-_B--_QqgBLrhg3L_Z22d3IiQhQC9jpLrblnpg"
# --- END: Your API Key (JWT) Here ---


# --- Target Board and Group Configuration ---
# IMPORTANT:
# - Ensure Board ID 9212659997 exists and you have write access to it.
# - Ensure Group ID 'group_mks780x2' exists on that board.
# - BOARD_ID must be a STRING because Monday.com expects type "ID!" for board_id.
BOARD_ID = "9212659997" # <<< ENSURE THIS IS A STRING
GROUP_ID = "group_mks780x2"
ITEM_TITLE = "THIS IS TEST"


# --- API Configuration (typically stable) ---
MONDAY_API_URL = "https://api.monday.com/v2"
API_VERSION = "2023-10"


def test_monday_connection_and_create_item():
    """
    Connects to Monday.com API using the provided key, attempts to create an item,
    and prints a detailed report on success or failure.
    """
    if not MONDAY_API_KEY:
        print("\nFATAL ERROR: API Key Not Set!")
        print("Please paste your Monday.com API key into the 'MONDAY_API_KEY' variable near the top of the script.")
        print("Example: MONDAY_API_KEY = 'sk-proj-abc123...' OR your JWT key.")
        sys.exit(1)

    headers = {
        "Authorization": f"Bearer {MONDAY_API_KEY}", # Adds the "Bearer " prefix correctly
        "Content-Type": "application/json",
        "API-Version": API_VERSION
    }

    # GraphQL Mutation to create an item
    # Note: $boardId type must be ID! in GraphQL
    mutation = """
    mutation createItem($boardId: ID!, $groupId: String!, $itemName: String!) {
      create_item (
        board_id: $boardId,
        group_id: $groupId,
        item_name: $itemName
      ) {
        id
        name
        board {
          id
          name
        }
        group {
          id
          title
        }
      }
    }
    """

    variables = {
        "boardId": BOARD_ID,
        "groupId": GROUP_ID,
        "itemName": ITEM_TITLE
    }

    # --- FIX: Ensure payload is defined BEFORE it's used in requests.post ---
    payload = {
        "query": mutation,
        "variables": variables
    }
    # --- END FIX ---

    print(f"\n--- Initiating Monday.com API Item Creation Test ---")
    print(f"API Endpoint: {MONDAY_API_URL}")
    print(f"Using API Version: {API_VERSION}")
    print(f"Auth Header: Bearer {MONDAY_API_KEY[:8]}...{MONDAY_API_KEY[-8:]} (masked key)")
    print(f"Attempting to create item: '{ITEM_TITLE}'")
    print(f"On Board ID: {BOARD_ID}, in Group ID: {GROUP_ID}")
    print(f"GraphQL Mutation being sent:\n{mutation.strip()}\n")
    print(f"GraphQL Variables being sent:\n{json.dumps(variables, indent=2)}\n")

    try:
        print(f"Sending POST request to {MONDAY_API_URL}...")
        # Now 'payload' is correctly defined here
        response = requests.post(MONDAY_API_URL, headers=headers, json=payload, timeout=20)
        
        response.raise_for_status() 

        print(f"\n--- HTTP Request Successful (Status: {response.status_code}) ---")
        print("Attempting to parse JSON response...")

        response_data = response.json()

        if "errors" in response_data:
            print("\n!!! Monday.com API Returned GraphQL ERRORS (despite HTTP 200 OK) !!!")
            print("This indicates the API key was sent correctly, but the operation failed due to permissions or a specific GraphQL issue.")
            print("\n--- Monday.com Specific Error Details (from 'errors' array) ---")
            for error in response_data["errors"]:
                print(f"  - **Code:** {error.get('code', 'N/A')}")
                print(f"  - **Message:** {error.get('message', 'N/A')}")
                if error.get('data'):
                    print(f"  - **Data:** {error.get('data')}")
                if error.get('locations'):
                    print(f"  - **Location:** Line {error['locations'][0].get('line')}, Column {error['locations'][0].get('column')}")
                if error.get('path'):
                    print(f"  - **Path:** {' -> '.join(map(str, error['path']))}")
                print("-" * 40)
            print("-----------------------------------------------------")
            print("\nDIAGNOSIS: GraphQL Validation/Execution Error.")
            print("  - **The most likely cause here is that your JWT key lacks the necessary 'boards:write' permission (scope) or is not the correct type of token for direct write operations.**")
            print("  - Double-check the `BOARD_ID` and `GROUP_ID` for correctness and accessibility on Monday.com.")
            print("  - If this JWT doesn't work, consider using a **Personal API Token (starting `sk-proj-`)** with `boards:write` scope for this operation.")

        elif response_data.get('data', {}).get('create_item'):
            item_info = response_data['data']['create_item']
            print("\n--- Monday.com API Call SUCCESSFUL: ITEM CREATED ---")
            print(f"Item ID: {item_info.get('id')}")
            print(f"Item Name: '{item_info.get('name')}'")
            print(f"Created on Board: '{item_info.get('board', {}).get('name')}' (ID: {item_info.get('board', {}).get('id')})")
            print(f"In Group: '{item_info.get('group', {}).get('title')}' (ID: {item_info.get('group', {}).get('id')})")
            print("\nCongratulations! Your API key and connection allowed item creation.")
            print("Please check your Monday.com board to confirm 'THIS IS TEST' has been added.")
            print("\nFull JSON Response:")
            print(json.dumps(response_data, indent=2))

        else:
            print("\n--- Monday.com API Call SUCCESSFUL, BUT UNEXPECTED RESPONSE ---")
            print("The API returned 200 OK without errors, but the 'create_item' data was missing or malformed.")
            print("Full JSON Response (for debugging):")
            print(json.dumps(response_data, indent=2))
            print("\nDIAGNOSIS: The API key might have insufficient permissions that Monday.com doesn't explicitly return as an 'error' array, or there's an issue with the board/group IDs.")


    except requests.exceptions.HTTPError as http_err:
        print(f"\n!!! HTTP ERROR OCCURRED: {http_err} !!!")
        print(f"Status Code: {response.status_code}")
        print(f"Reason: {response.reason}")
        print(f"Full URL Attempted: {response.url}")
        print(f"Response Headers:\n{json.dumps(dict(response.headers), indent=2)}")
        print(f"Response Body (if available and not too large):\n{response.text[:1000]}...")
        
        if response.status_code == 400:
            print("\nDIAGNOSIS: BAD REQUEST (Check your GraphQL syntax or variable types).")
            print("  - This can happen if the GraphQL query or its variables are syntactically incorrect, or if the data types don't match Monday.com's expectations.")
            print("  - Double-check the `BOARD_ID` (should be a string) and `GROUP_ID`.")
        elif response.status_code == 401:
            print("\nDIAGNOSIS: UNAUTHORIZED (Authentication Failed).")
            print("  - Your API key (JWT) is likely incorrect, expired, revoked, or not valid for direct API calls to Monday.com's GraphQL endpoint for write operations.")
            print("  - Reconfirm you are using a **Personal API Token** (starting 'sk-proj-') if this JWT continues to fail for write operations, as JWTs may require different flows.")
        elif response.status_code == 403:
            print("\nDIAGNOSIS: FORBIDDEN (Permission Denied).")
            print("  - Your API key (JWT) is authenticated but lacks the necessary account-level or token-specific permissions to perform the requested action (create item on this board/group).")
            print("  - This is very common if the token doesn't have the 'boards:write' scope.")
        elif response.status_code == 429:
            print("\nDIAGNOSIS: TOO MANY REQUESTS (Rate Limit Exceeded).")
            print("  - You have sent too many requests in a short period. Monday.com limits API calls.")
            print(f"  - Try again after: {response.headers.get('Retry-After', 'N/A')} seconds (if provided in headers).")
        else:
            print("\nDIAGNOSIS: UNEXPECTED HTTP ERROR.")
            print("  - This is an unexpected HTTP error from Monday.com's server, or a highly malformed request.")

    except requests.exceptions.ConnectionError as conn_err:
        print(f"\n!!! CONNECTION ERROR OCCURRED: {conn_err} !!!")
        print("DIAGNOSIS: Failed to establish a network connection to Monday.com API.")
        print("  - Check your internet connection.")
        print("  - Verify that `api.monday.com` is reachable (try pinging it from your terminal).")
        print("  - Ensure no local firewall or network proxy is blocking the connection from your machine.")
        print("  - Monday.com servers might be temporarily down or experiencing issues.")
    except requests.exceptions.Timeout as timeout_err:
        print(f"\n!!! TIMEOUT ERROR OCCURRED: {timeout_err} !!!")
        print("DIAGNOSIS: The request to Monday.com API took too long to respond.")
        print("  - This could indicate network congestion, a very slow Monday.com server response, or an overly restrictive timeout setting in the script.")
        print("  - You can try increasing the 'timeout' value (currently 20 seconds) in the `requests.post` call if your network is known to be slow.")
    except requests.exceptions.RequestException as req_err:
        print(f"\n!!! AN UNEXPECTED REQUESTS LIBRARY ERROR OCCURRED: {req_err} !!!")
        print("DIAGNOSIS: A general error from the 'requests' library that wasn't more specific (e.g., invalid URL, too many redirects).")
    except json.JSONDecodeError:
        print(f"\n!!! JSON DECODE ERROR: Could not parse response as JSON !!!")
        print("DIAGNOSIS: Monday.com sent a response that was not valid JSON.")
        print("  - This often indicates a server-side error on Monday.com returning an HTML error page, a malformed JSON response, or a partial response due to connection issues.")
        if 'response' in locals():
            print(f"Raw response text (first 1000 chars):\n{response.text[:1000]}...")
    except Exception as e:
        print(f"\n!!! AN UNFORESEEN PYTHON ERROR OCCURRED: {e} !!!")
        print("DIAGNOSIS: An unhandled error within the script itself.")
        print(f"Please report this error message and the context to the script's creator if it persists.")

if __name__ == "__main__":
    test_monday_connection_and_create_item()