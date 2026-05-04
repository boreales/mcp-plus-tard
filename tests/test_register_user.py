from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.models import RegisterUserResponse, User
from app.tools import register_user


async def test_register_user_nominal(mock_client):
    mock_client.register_user.return_value = RegisterUserResponse(
        success=True,
        user=User(id=123, email="a@b.com", language="fr", is_subscribed=True),
        oauth_url="https://plus-tard.com/api/auth/connect/eyJ...",
    )

    result = await register_user(mock_client, email="a@b.com", language="fr")

    mock_client.register_user.assert_awaited_once_with(email="a@b.com", language="fr")
    assert "123" in result
    assert "a@b.com" in result
    assert "https://plus-tard.com/api/auth/connect/" in result


@pytest.mark.parametrize("status", [400, 409, 502])
async def test_register_user_propagates_http_errors(mock_client, status):
    mock_client.register_user.side_effect = HTTPException(status_code=status, detail="x")

    with pytest.raises(HTTPException) as exc_info:
        await register_user(mock_client)

    assert exc_info.value.status_code == status
