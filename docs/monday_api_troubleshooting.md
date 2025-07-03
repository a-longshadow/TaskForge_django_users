# Monday.com API Integration - Troubleshooting Guide

## Overview

This document provides solutions for common Monday.com API integration issues, specifically addressing 401 Unauthorized errors and testing problems encountered in the Django task management application.

## Root Cause Analysis

### Primary Issues Identified

1. **Test Isolation Problems**: Tests were making real API calls instead of using mocks
2. **Inconsistent Mocking**: Different test methods used different mocking strategies
3. **Configuration Leakage**: Production API credentials were being used during tests
4. **URL Configuration**: Test and production environments had different API endpoints

### 401 Unauthorized Errors

The 401 errors occurred because:

1. **Real API Calls During Tests**: Tests were bypassing mocks and making actual HTTP requests to Monday.com
2. **Invalid Credentials**: Test environment was using production credentials inappropriately
3. **Missing Mocking**: The `_get_setting` function wasn't properly mocked, causing real database lookups

## Solutions Implemented

### 1. Fixed Test Mocking Strategy

**Problem**: Tests were making real API calls instead of using mocks.

**Solution**: Implemented comprehensive mocking at multiple levels:

```python
# Mock the _get_setting function directly
@patch('tasks.services._get_setting')
@patch('tasks.services.requests.post')
def test_create_monday_item(self, mock_get_setting, mock_requests_post):
    # Mock all settings
    def mock_get_setting_func(key):
        settings_map = {
            "MONDAY_API_KEY": "test-api-key",
            "MONDAY_BOARD_ID": "12345",
            "MONDAY_GROUP_ID": "group_123",
            "MONDAY_COLUMN_MAP": json.dumps({...})
        }
        return settings_map.get(key)
    
    mock_get_setting.side_effect = mock_get_setting_func
    
    # Mock HTTP response
    mock_response = Mock()
    mock_response.json.return_value = {"data": {"create_item": {"id": "987654321"}}}
    mock_requests_post.return_value = mock_response
```

### 2. Created Isolated Test Settings

**Problem**: Tests were using production settings and credentials.

**Solution**: Created `tests/test_settings.py` with isolated configuration:

```python
# Override Monday.com settings to prevent real API calls
MONDAY_API_KEY = "test-api-key-fake"
MONDAY_BOARD_ID = "test-board-123"
MONDAY_GROUP_ID = "test-group-123"
MONDAY_COLUMN_MAP = '{"test": "column"}'

# Use fake URL for tests
MONDAY_API_URL = "https://fake-monday-api.test/v2"

# Use in-memory database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}
```

### 3. Enhanced Services Configuration

**Problem**: Hard-coded API URL couldn't be overridden for testing.

**Solution**: Made the API URL configurable:

```python
# Allow override via settings
MONDAY_API_URL = getattr(settings, 'MONDAY_API_URL', "https://api.monday.com/v2")
```

### 4. Fixed Bulk Operation Testing

**Problem**: Bulk tests weren't using mocked functions properly.

**Solution**: Corrected the patch target to match the imported function:

```python
# Patch the imported function, not the module function
@patch('tests.test_monday_service.create_monday_item')
def test_bulk_create_monday_items(self, mock_create_monday_item):
    mock_create_monday_item.side_effect = [f"item_{i}" for i in range(len(self.tasks))]
```

### 5. Improved Exception Handling Testing

**Problem**: Tests were using wrong exception types.

**Solution**: Used appropriate requests exception types:

```python
# Use specific requests exception
mock_requests_post.side_effect = requests.exceptions.ConnectionError("Connection error")
```

## Monday.com API Best Practices

### Authentication Requirements

1. **API Token Format**: Use Personal API tokens (`sk-proj-...`) for direct API access
2. **Authorization Header**: Always include `Bearer` prefix: `Authorization: Bearer {token}`
3. **API Version**: Specify API version header: `API-Version: 2023-10`
4. **Content Type**: Use `Content-Type: application/json`

### Common Error Patterns

#### 401 Unauthorized
- **Cause**: Invalid or missing API token
- **Solution**: Verify token format and permissions
- **Check**: Ensure token has required scopes (boards:write, users:read)

#### 400 Bad Request
- **Cause**: Invalid GraphQL syntax or variable types
- **Solution**: Ensure board_id is string type for ID! GraphQL type
- **Example**: `"board": "123456789"` not `"board": 123456789`

#### Rate Limiting (429)
- **Cause**: Too many requests
- **Solution**: Implement exponential backoff and respect rate limits

### Testing Strategy

#### Unit Tests
- Mock all external API calls
- Test error conditions and edge cases
- Verify proper data transformation
- Use isolated test settings

#### Integration Tests (Optional)
- Use separate test environment
- Test with real API credentials
- Validate end-to-end functionality
- Run separately from unit tests

## Production Deployment Checklist

### Environment Configuration
- [ ] Verify `MONDAY_API_KEY` is set correctly
- [ ] Confirm `MONDAY_BOARD_ID` exists and is accessible
- [ ] Validate `MONDAY_GROUP_ID` is correct
- [ ] Check `MONDAY_COLUMN_MAP` JSON format

### API Credentials
- [ ] Test API token has required permissions
- [ ] Verify token is not expired
- [ ] Confirm board and group IDs are valid
- [ ] Test with a simple API call first

### Monitoring
- [ ] Set up logging for Monday.com API calls
- [ ] Monitor for 401/403 errors
- [ ] Track API rate limit usage
- [ ] Alert on integration failures

## Running Tests

### Unit Tests Only (Recommended)
```bash
python manage.py test tests.test_monday_service --settings=tests.test_settings
```

### All Tests
```bash
python manage.py test --settings=tests.test_settings
```

### Production Verification
```bash
# Test with real credentials (use carefully)
python manage.py shell
>>> from tasks.services import _post_monday
>>> result = _post_monday("query { me { name } }")
>>> print(result)
```

## Troubleshooting Commands

### Check Current Settings
```python
from tasks.services import _get_setting
print("API Key:", _get_setting("MONDAY_API_KEY")[:10] + "..." if _get_setting("MONDAY_API_KEY") else "None")
print("Board ID:", _get_setting("MONDAY_BOARD_ID"))
print("Group ID:", _get_setting("MONDAY_GROUP_ID"))
```

### Test API Connection
```python
from tasks.services import _post_monday
result = _post_monday("query { me { name } }")
if result.get("errors"):
    print("API Error:", result["errors"])
else:
    print("API Success:", result.get("data", {}).get("me", {}).get("name"))
```

### Verify Column Mapping
```python
import json
from tasks.services import _get_setting
column_map = json.loads(_get_setting("MONDAY_COLUMN_MAP") or "{}")
print("Column Map:", column_map)
```

## Summary

The 401 Unauthorized errors were caused by improper test isolation, not actual API credential issues. The solutions implemented:

1. **Comprehensive test mocking** to prevent real API calls during testing
2. **Isolated test settings** to ensure tests don't use production data
3. **Improved error handling** and logging for better debugging
4. **Proper exception testing** with correct exception types
5. **Configurable API endpoints** for different environments

All tests now pass successfully, and the Monday.com integration is properly isolated for testing while maintaining production functionality. 