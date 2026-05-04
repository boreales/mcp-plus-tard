from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends

from app.auth.api_key import ApiKeyDep
from app.services import PlusTardClient


async def get_plus_tard_client(
    api_key: ApiKeyDep,
) -> AsyncIterator[PlusTardClient]:
    """Yield a PlusTardClient bound to the caller's API key.

    The httpx connection is closed at the end of the request.
    """
    client = PlusTardClient(token=api_key)
    try:
        yield client
    finally:
        await client.aclose()


PlusTardClientDep = Annotated[PlusTardClient, Depends(get_plus_tard_client)]
