from dataclasses import dataclass

from app.models import Provider, User
from app.services import PlusTardClient


@dataclass(frozen=True)
class PublishableAccount:
    """A target `schedule_post` can publish to: (provider, page_id)."""

    provider: str
    name: str
    page_id: str


def publishable_accounts(user: User) -> list[PublishableAccount]:
    """Flatten a user's providers into the accounts posts can target.

    Facebook pages and Instagram accounts are sub-accounts of a provider,
    and their `type` ("facebook" / "instagram") is the provider to publish
    with. Every other network (TikTok, LinkedIn, X, Threads, Bluesky,
    Google) has no sub-account: the provider itself is the account,
    identified by its `providerId`.
    """
    accounts: list[PublishableAccount] = []
    for p in user.providers:
        if p.accounts:
            for sub in p.accounts:
                provider = p.provider
                if sub.type is not None and sub.type in Provider._value2member_map_:
                    provider = Provider(sub.type)
                accounts.append(
                    PublishableAccount(
                        provider=provider.value,
                        name=sub.name,
                        page_id=sub.id,
                    )
                )
        elif p.provider_id:
            # User responses say "googlemybusiness"; POST /api/post expects "google".
            provider = (
                Provider.GOOGLE
                if p.provider is Provider.GOOGLE_MY_BUSINESS
                else p.provider
            )
            accounts.append(
                PublishableAccount(
                    provider=provider.value,
                    name=p.username or provider.value,
                    page_id=p.provider_id,
                )
            )
    return accounts


async def list_accounts(client: PlusTardClient) -> str:
    """Liste tous les comptes réseaux sociaux connectés à Plus Tard.
    Utilise ce tool pour savoir quels comptes sont disponibles
    avant de planifier un post.

    Pour chaque compte, `provider` et `page_id` sont les valeurs à
    passer telles quelles aux paramètres `provider` et `page_id` de
    `schedule_post`.
    """
    response = await client.get_me()
    accounts = publishable_accounts(response.user)

    if not accounts:
        return "Aucun compte réseau social n'est connecté à Plus Tard."

    lines = [f"{len(accounts)} compte(s) connecté(s) à Plus Tard :", ""]
    for account in accounts:
        lines.append(
            f"- {account.name}\n"
            f"    provider : {account.provider}\n"
            f"    page_id (à utiliser pour schedule_post) : {account.page_id}"
        )
    return "\n".join(lines)
