from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from app.models import ApiKeyInfo, ValidateApiKeyResponse
from app.tools import validate_api_key


async def test_validate_api_key_valid_with_info(mock_client):
    mock_client.validate_api_key.return_value = ValidateApiKeyResponse(
        valid=True,
        api_key=ApiKeyInfo(
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            expires_at=datetime(2027, 1, 1, tzinfo=timezone.utc),
            last_used_at=datetime(2026, 1, 28, 10, 30, tzinfo=timezone.utc),
        ),
    )

    result = await validate_api_key(mock_client)

    assert "valide" in result
    assert "01/01/2026" in result
    assert "01/01/2027" in result


async def test_validate_api_key_invalid(mock_client):
    mock_client.validate_api_key.return_value = ValidateApiKeyResponse(valid=False)

    result = await validate_api_key(mock_client)

    assert "pas valide" in result


@pytest.mark.parametrize("status", [401, 502])
async def test_validate_api_key_propagates_http_errors(mock_client, status):
    mock_client.validate_api_key.side_effect = HTTPException(
        status_code=status, detail="x"
    )

    with pytest.raises(HTTPException) as exc_info:
        await validate_api_key(mock_client)

    assert exc_info.value.status_code == status
