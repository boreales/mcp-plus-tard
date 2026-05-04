from __future__ import annotations

import contextvars
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Request
from mcp.server.fastmcp import FastMCP

from app.config import get_settings
from app.services import PlusTardClient
from app.tools import (
    get_user as tool_get_user,
    list_accounts as tool_list_accounts,
    register_user as tool_register_user,
    schedule_post as tool_schedule_post,
    validate_api_key as tool_validate_api_key,
)

# Per-request token, captured by middleware before MCP dispatch.
_api_key_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "plus_tard_api_key", default=None
)


def _current_api_key() -> str:
    api_key = _api_key_var.get()
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Header X-Api-Key manquant",
        )
    return api_key


def _build_client() -> PlusTardClient:
    return PlusTardClient(token=_current_api_key())


mcp = FastMCP("plus-tard", streamable_http_path="/")


@mcp.tool()
async def validate_api_key() -> str:
    """Vérifie que la clef API Plus Tard fournie est valide.
    Utilise ce tool si l'utilisateur veut diagnostiquer un problème
    d'authentification ou simplement confirmer que sa clef est active.
    Retourne aussi la date de création et d'expiration de la clef.
    """
    async with _build_client() as client:
        return await tool_validate_api_key(client)


@mcp.tool()
async def list_accounts() -> str:
    """Liste tous les comptes réseaux sociaux connectés à Plus Tard.
    Utilise ce tool pour savoir quels comptes sont disponibles
    avant de planifier un post.
    """
    async with _build_client() as client:
        return await tool_list_accounts(client)


@mcp.tool()
async def schedule_post(
    provider: Literal[
        "facebook",
        "instagram",
        "linkedin",
        "twitter",
        "tiktok",
        "threads",
        "bluesky",
        "google",
    ],
    page_id: str,
    planned_at: datetime,
    text: str | None = None,
    image_posts: list[Any] | None = None,
    twitter_params: dict[str, Any] | None = None,
    tiktok_params: dict[str, Any] | None = None,
) -> str:
    """Planifie un post sur un seul réseau social via Plus Tard.
    Utilise ce tool quand l'utilisateur veut programmer, publier ou
    scheduler du contenu sur Facebook, Instagram, LinkedIn, X/Twitter,
    TikTok, Threads, Bluesky ou Google My Business.

    IMPORTANT :
    - Un appel = un réseau. Pour publier sur plusieurs réseaux, appelle
      ce tool plusieurs fois.
    - AVANT D'APPELER ce tool : appelle d'abord list_accounts (ou
      get_user pour la vue détaillée) pour obtenir le page_id correct.
    - Le `page_id` à passer ici est l'identifiant EXTERNE du compte sur
      le réseau social (champ `accountId` / `page_id` retourné par
      list_accounts, ex. "1097653263583548"), PAS l'identifiant interne
      Plus Tard (champ `id` / `internal_id`, ex. "34"). Confondre les
      deux crée un post mal rattaché et apparaissant comme "compte
      déconnecté".
    - Pour les providers sans sous-comptes (Twitter, LinkedIn, TikTok,
      Threads, Bluesky, Google), utilise le `providerId` retourné par
      get_user.
    - Instagram exige au moins une image ou vidéo dans image_posts.
    - planned_at doit être une date/heure UTC future au format ISO8601
      (ex: 2026-05-01T10:00:00Z).
    """
    async with _build_client() as client:
        return await tool_schedule_post(
            client,
            provider=provider,
            page_id=page_id,
            planned_at=planned_at.isoformat(),
            text=text,
            image_posts=image_posts,
            twitter_params=twitter_params,
            tiktok_params=tiktok_params,
        )


@mcp.tool()
async def register_user(
    email: str | None = None,
    language: str | None = None,
) -> str:
    """Crée un nouvel utilisateur Plus Tard et retourne une URL OAuth
    permettant de connecter ses comptes de réseaux sociaux.
    Utilise ce tool quand l'utilisateur veut onboarder un nouveau client
    ou se créer un compte. Email et langue sont optionnels — la langue
    par défaut est 'fr'.
    L'URL OAuth doit être ouverte dans un navigateur par l'utilisateur
    final pour qu'il connecte ses réseaux. Elle est valable 24h.
    """
    async with _build_client() as client:
        return await tool_register_user(client, email=email, language=language)


@mcp.resource(
    "plus-tard://accounts",
    name="Comptes Plus Tard",
    title="Liste des comptes connectés",
    description=(
        "Liste JSON des comptes réseaux sociaux connectés à Plus Tard pour "
        "la clef API courante. Utile pour identifier un page_id avant un "
        "schedule_post."
    ),
    mime_type="application/json",
)
async def accounts_resource() -> str:
    import json

    async with _build_client() as client:
        response = await client.list_accounts()
    payload = [
        {
            "name": a.name,
            "page_id": a.account_id,
            "internal_id": a.id,
            "_hint": (
                "page_id is the value to pass to schedule_post; "
                "internal_id is the Plus Tard internal id and must NOT "
                "be used as page_id."
            ),
        }
        for a in response.accounts
    ]
    return json.dumps(payload, ensure_ascii=False, indent=2)


@mcp.resource(
    "plus-tard://users/{user_id}",
    name="Utilisateur Plus Tard",
    title="Détail d'un utilisateur (providers + sous-comptes)",
    description=(
        "Détail JSON d'un utilisateur Plus Tard, incluant les providers "
        "connectés et leurs sous-comptes — pratique pour identifier un "
        "page_id par provider avant un schedule_post."
    ),
    mime_type="application/json",
)
async def user_resource(user_id: str) -> str:
    import json

    async with _build_client() as client:
        response = await client.get_user(int(user_id))
    user = response.user
    payload = {
        "id": user.id,
        "email": user.email,
        "language": user.language,
        "is_subscribed": user.is_subscribed,
        "providers": [
            {
                "provider": p.provider.value,
                "provider_id": p.provider_id,
                "username": p.username,
                "accounts": [
                    {"id": s.id, "name": s.name, "type": s.type}
                    for s in p.accounts
                ],
            }
            for p in user.providers
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


@mcp.tool()
async def get_user(user_id: int) -> str:
    """Récupère les informations d'un utilisateur Plus Tard par son id,
    incluant ses providers connectés (Facebook, Instagram, LinkedIn, etc.)
    et leurs sous-comptes (pages Facebook, comptes Instagram pro...).
    Utilise ce tool avant schedule_post pour identifier le bon page_id
    à utiliser : pour Facebook/Instagram, c'est l'id du sous-compte
    (providers[].accounts[].id) ; pour les autres providers (LinkedIn,
    Twitter, TikTok, Threads, Bluesky), c'est providers[].providerId.
    """
    async with _build_client() as client:
        return await tool_get_user(client, user_id=user_id)


@asynccontextmanager
async def _lifespan(_: FastAPI):
    async with mcp.session_manager.run():
        yield


app = FastAPI(
    title="Plus Tard MCP",
    description="MCP server exposing Plus Tard scheduling API to AI agents.",
    version="0.1.0",
    lifespan=_lifespan,
)


@app.middleware("http")
async def capture_api_key(request: Request, call_next):
    token = _api_key_var.set(request.headers.get("X-Api-Key"))
    try:
        return await call_next(request)
    finally:
        _api_key_var.reset(token)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


# Mount the MCP Streamable HTTP transport at /mcp
app.mount("/mcp", mcp.streamable_http_app())


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.mcp_host,
        port=settings.mcp_port,
        reload=False,
    )
