from __future__ import annotations

from types import TracebackType
from typing import Any, Self

import httpx
from fastapi import HTTPException

from app.config import get_settings
from app.models import (
    AccountsResponse,
    GetUserResponse,
    OAuthUrlResponse,
    RegisterUserResponse,
    SchedulePostRequest,
    SchedulePostResponse,
    ValidateApiKeyResponse,
)


class PlusTardClient:
    """Async client wrapping the Plus Tard Symfony API.

    One instance per incoming MCP request — bound to a single user token.
    Most endpoints speak plain JSON; `/api/accounts` is auto-exposed by
    API Platform and only speaks JSON-LD/Hydra.
    """

    def __init__(self, token: str) -> None:
        settings = get_settings()
        self._client = httpx.AsyncClient(
            base_url=str(settings.plus_tard_base_url).rstrip("/"),
            timeout=settings.http_timeout_seconds,
            headers={
                "X-Api-Key": token,
                # Accept anything: some Symfony endpoints only emit ld+json,
                # others emit plain json. We parse whatever JSON comes back.
                "Accept": "*/*",
                "Content-Type": "application/json",
            },
        )

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _request(
        self,
        method: str,
        url: str,
        *,
        extra_headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        try:
            response = await self._client.request(
                method, url, headers=extra_headers, **kwargs
            )
        except httpx.TimeoutException as exc:
            raise HTTPException(
                status_code=504,
                detail="L'API Plus Tard n'a pas répondu dans le délai imparti",
            ) from exc
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=502,
                detail="Impossible de contacter l'API Plus Tard",
            ) from exc

        self._raise_for_status(response)
        return response

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        if response.is_success:
            return

        status = response.status_code

        if status == 401:
            raise HTTPException(status_code=401, detail="Token invalide ou expiré")

        # The API uses a uniform error envelope:
        # {success: false, error: "code", error_description: "..."}
        if status in (400, 403, 404, 409, 422):
            detail = f"Erreur {status}"
            try:
                payload = response.json()
            except ValueError:
                payload = None
            if isinstance(payload, dict):
                detail = (
                    payload.get("error_description")
                    or payload.get("message")
                    or payload.get("detail")
                    or payload.get("error")
                    or detail
                )
            raise HTTPException(status_code=status, detail=detail)

        if 500 <= status < 600:
            raise HTTPException(
                status_code=502,
                detail="L'API Plus Tard est indisponible",
            )

        raise HTTPException(
            status_code=status,
            detail=f"Erreur inattendue de l'API Plus Tard ({status})",
        )

    # ---- Endpoints ----------------------------------------------------

    async def validate_api_key(self) -> ValidateApiKeyResponse:
        response = await self._request("GET", "/api/auth/validate")
        return ValidateApiKeyResponse.model_validate(response.json())

    async def list_accounts(self) -> AccountsResponse:
        # API Platform auto-exposed resource — JSON-LD only.
        response = await self._request(
            "GET",
            "/api/accounts",
            extra_headers={"Accept": "application/ld+json"},
        )
        return AccountsResponse.model_validate(response.json())

    async def schedule_post(
        self, payload: SchedulePostRequest
    ) -> SchedulePostResponse:
        response = await self._request(
            "POST",
            "/api/post",
            json=payload.model_dump(mode="json", by_alias=True, exclude_none=True),
        )
        return SchedulePostResponse.model_validate(response.json())

    async def register_user(
        self, email: str | None = None, language: str | None = None
    ) -> RegisterUserResponse:
        body: dict[str, Any] = {}
        if email is not None:
            body["email"] = email
        if language is not None:
            body["language"] = language
        response = await self._request("POST", "/api/auth/register", json=body)
        return RegisterUserResponse.model_validate(response.json())

    async def get_user(self, user_id: int) -> GetUserResponse:
        response = await self._request("GET", f"/api/auth/user/{user_id}")
        return GetUserResponse.model_validate(response.json())

    async def get_oauth_url(self, user_id: int) -> OAuthUrlResponse:
        response = await self._request(
            "GET", f"/api/auth/user/{user_id}/oauth-url"
        )
        return OAuthUrlResponse.model_validate(response.json())
