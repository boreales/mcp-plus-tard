from __future__ import annotations

import os
from unittest.mock import AsyncMock

import pytest

# Ensure required env vars exist before app.config is imported anywhere.
os.environ.setdefault("PLUS_TARD_BASE_URL", "https://api.plus-tard.test")


@pytest.fixture
def mock_client() -> AsyncMock:
    """An AsyncMock standing in for a PlusTardClient.

    Each method is itself an AsyncMock; tests configure return values or
    side effects per case.
    """
    from app.services import PlusTardClient

    client = AsyncMock(spec=PlusTardClient)
    return client
