from typing import Any

from app.models import Provider, SchedulePostRequest
from app.services import PlusTardClient


async def schedule_post(
    client: PlusTardClient,
    provider: str,
    page_id: str,
    planned_at: str,
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
    - Avant d'appeler, utilise list_accounts ou get_user pour obtenir le
      page_id correct (pour Facebook/Instagram, c'est l'id du sous-compte ;
      pour les autres providers, c'est le providerId du compte connecté).
    - Instagram exige au moins une image ou vidéo dans image_posts.
    - planned_at doit être en ISO8601 UTC (ex: 2026-05-01T10:00:00Z).
    """
    payload = SchedulePostRequest(
        provider=Provider(provider),
        page_id=page_id,
        planned_at=planned_at,  # type: ignore[arg-type]
        text=text,
        image_posts=image_posts,
        twitter_params=twitter_params,
        tiktok_params=tiktok_params,
    )

    result = await client.schedule_post(payload)

    when = payload.planned_at.strftime("%d/%m/%Y à %H:%M UTC")
    medias = f" avec {len(image_posts)} média(s)" if image_posts else ""
    return (
        f"✅ Post #{result.post_id} planifié sur {provider} (compte {page_id}) "
        f"pour le {when}{medias}."
    )
