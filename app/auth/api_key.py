from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader

_api_key_header = APIKeyHeader(name="X-Api-Key", auto_error=False)


async def get_api_key(
    api_key: Annotated[str | None, Depends(_api_key_header)],
) -> str:
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Header X-Api-Key manquant",
        )
    return api_key


ApiKeyDep = Annotated[str, Depends(get_api_key)]
