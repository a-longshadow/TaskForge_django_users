"""Test settings for Django tests - isolated from production."""

from taskforge.settings import *

# Override database to use in-memory SQLite for tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Override Monday.com settings to prevent real API calls
MONDAY_API_KEY = "test-api-key-fake"
MONDAY_BOARD_ID = "test-board-123"
MONDAY_GROUP_ID = "test-group-123"
MONDAY_COLUMN_MAP = '{"test": "column"}'

# Disable logging during tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {
        'handlers': ['null'],
    },
}

# Use faster password hasher for tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable migrations during tests
class DisableMigrations:
    def __contains__(self, item):
        return True
    
    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Disable caching during tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Ensure no real external API calls are made
MONDAY_API_URL = "https://fake-monday-api.test/v2"  # Fake URL for tests 