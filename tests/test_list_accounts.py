from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.models import Account, AccountsResponse
from app.tools import list_accounts


async def test_list_accounts_nominal(mock_client):
    mock_client.list_accounts.return_value = AccountsResponse(
        accounts=[
            Account(id="34", name="Boréales Créations", accountId="1097653263583548"),
            Account(id="35", name="Neartrip", accountId="219806935292378"),
        ]
    )

    result = await list_accounts(mock_client)

    assert "Boréales Créations" in result
    assert "Neartrip" in result
    assert "34" in result
    assert "1097653263583548" in result


async def test_list_accounts_empty(mock_client):
    mock_client.list_accounts.return_value = AccountsResponse(accounts=[])

    result = await list_accounts(mock_client)

    assert "Aucun compte" in result


@pytest.mark.parametrize("status", [401, 422, 502])
async def test_list_accounts_propagates_http_errors(mock_client, status):
    mock_client.list_accounts.side_effect = HTTPException(status_code=status, detail="x")

    with pytest.raises(HTTPException) as exc_info:
        await list_accounts(mock_client)

    assert exc_info.value.status_code == status
