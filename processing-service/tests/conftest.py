import os

# Set dummy env vars before any app module is imported.
# Tests that need real services (DB, Claude API) should be integration tests with real creds.
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test_db")
os.environ.setdefault("CLAUDE_API_KEY", "sk-ant-test-key")
os.environ.setdefault("MISTRAL_API_KEY", "test-mistral-key")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")

import pytest  # noqa: E402

pytest_plugins = ["pytest_asyncio"]
