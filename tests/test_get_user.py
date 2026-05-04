from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.models import (
    GetUserResponse,
    Provider,
    ProviderSubAccount,
    User,
    UserProvider,
)
from app.tools import get_user


async def test_get_user_with_providers_and_accounts(mock_client):
    mock_client.get_user.return_value = GetUserResponse(
        success=True,
        user=User(
            id=123,
            email="a@b.com",
            language="fr",
            is_subscribed=True,
            providers=[
                UserProvider(
                    id=1,
                    provider=Provider.FACEBOOK,
                    provider_id="10225678901234567",
                    username="John Doe",
                    accounts=[
                        ProviderSubAccount(
                            id="123456789", name="Ma Page Facebook", type="page"
                        )
                    ],
                ),
                UserProvider(
                    id=2,
                    provider=Provider.LINKEDIN,
                    provider_id="urn:li:person:AbCdEf123",
                    username="John Doe",
                    accounts=[],
                ),
            ],
        ),
    )

    result = await get_user(mock_client, user_id=123)

    mock_client.get_user.assert_awaited_once_with(123)
    assert "123" in result
    assert "facebook" in result
    assert "linkedin" in result
    assert "Ma Page Facebook" in result
    assert "10225678901234567" in result


async def test_get_user_no_providers(mock_client):
    mock_client.get_user.return_value = GetUserResponse(
        success=True,
        user=User(id=123, email="a@b.com"),
    )

    result = await get_user(mock_client, user_id=123)

    assert "Aucun réseau" in result


@pytest.mark.parametrize("status", [403, 404, 502])
async def test_get_user_propagates_http_errors(mock_client, status):
    mock_client.get_user.side_effect = HTTPException(status_code=status, detail="x")

    with pytest.raises(HTTPException) as exc_info:
        await get_user(mock_client, user_id=999)

    assert exc_info.value.status_code == status
