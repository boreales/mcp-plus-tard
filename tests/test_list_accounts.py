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
from app.tools import list_accounts
from app.tools.list_accounts import PublishableAccount, publishable_accounts


def _me(*providers: UserProvider) -> GetUserResponse:
    return GetUserResponse(success=True, user=User(id=1, providers=list(providers)))


async def test_list_accounts_reads_the_api_key_owner(mock_client):
    mock_client.get_me.return_value = _me()

    await list_accounts(mock_client)

    mock_client.get_me.assert_awaited_once_with()


async def test_list_accounts_lists_facebook_and_instagram_sub_accounts(mock_client):
    mock_client.get_me.return_value = _me(
        UserProvider(
            id=1,
            provider=Provider.FACEBOOK,
            provider_id="10225678901234567",
            accounts=[
                ProviderSubAccount(
                    id="1097653263583548", name="Boréales Créations", type="facebook"
                ),
                ProviderSubAccount(
                    id="17841411845686701", name="boreales", type="instagram"
                ),
            ],
        )
    )

    result = await list_accounts(mock_client)

    assert "2 compte(s)" in result
    assert "Boréales Créations" in result
    assert "1097653263583548" in result
    assert "provider : instagram" in result
    assert "17841411845686701" in result
    # The Facebook user id is not a publishable target when pages exist.
    assert "10225678901234567" not in result


async def test_list_accounts_lists_providers_without_sub_accounts(mock_client):
    mock_client.get_me.return_value = _me(
        UserProvider(
            id=2,
            provider=Provider.TIKTOK,
            provider_id="tt-123",
            username="boreales.tiktok",
            accounts=[],
        )
    )

    result = await list_accounts(mock_client)

    assert "1 compte(s)" in result
    assert "boreales.tiktok" in result
    assert "provider : tiktok" in result
    assert "tt-123" in result


async def test_list_accounts_empty(mock_client):
    mock_client.get_me.return_value = _me()

    result = await list_accounts(mock_client)

    assert "Aucun compte" in result


@pytest.mark.parametrize("status", [401, 422, 502])
async def test_list_accounts_propagates_http_errors(mock_client, status):
    mock_client.get_me.side_effect = HTTPException(status_code=status, detail="x")

    with pytest.raises(HTTPException) as exc_info:
        await list_accounts(mock_client)

    assert exc_info.value.status_code == status


def test_publishable_accounts_maps_google_my_business_to_google():
    user = User(
        id=1,
        providers=[
            UserProvider(
                id=3,
                provider=Provider.GOOGLE_MY_BUSINESS,
                provider_id="locations/42",
                accounts=[],
            )
        ],
    )

    assert publishable_accounts(user) == [
        PublishableAccount(provider="google", name="google", page_id="locations/42")
    ]


def test_publishable_accounts_falls_back_to_parent_provider_for_unknown_type():
    user = User(
        id=1,
        providers=[
            UserProvider(
                id=1,
                provider=Provider.FACEBOOK,
                accounts=[ProviderSubAccount(id="123", name="Ma Page", type="page")],
            )
        ],
    )

    assert publishable_accounts(user) == [
        PublishableAccount(provider="facebook", name="Ma Page", page_id="123")
    ]


def test_publishable_accounts_skips_provider_without_id_or_sub_accounts():
    user = User(
        id=1,
        providers=[UserProvider(id=4, provider=Provider.TWITTER, accounts=[])],
    )

    assert publishable_accounts(user) == []
