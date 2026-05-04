from app.services import PlusTardClient


async def get_user(client: PlusTardClient, user_id: int) -> str:
    """Récupère les informations d'un utilisateur Plus Tard par son id,
    incluant ses providers connectés (Facebook, Instagram, LinkedIn, etc.)
    et leurs sous-comptes (pages Facebook, comptes Instagram pro...).
    Utilise ce tool avant schedule_post pour identifier le bon page_id
    à utiliser : pour Facebook/Instagram, c'est l'id du sous-compte
    (providers[].accounts[].id) ; pour les autres providers (LinkedIn,
    Twitter, TikTok, Threads, Bluesky), c'est providers[].providerId.
    """
    response = await client.get_user(user_id)
    user = response.user

    lines = [f"Utilisateur #{user.id}"]
    if user.email:
        lines.append(f"Email : {user.email}")
    if user.language:
        lines.append(f"Langue : {user.language}")
    if user.is_subscribed is not None:
        lines.append(f"Abonné : {'oui' if user.is_subscribed else 'non'}")

    if not user.providers:
        lines.append("")
        lines.append("Aucun réseau social connecté.")
        return "\n".join(lines)

    lines.append("")
    lines.append(f"{len(user.providers)} provider(s) connecté(s) :")
    for p in user.providers:
        header = f"- {p.provider.value}"
        if p.username:
            header += f" — {p.username}"
        if p.provider_id:
            header += f" (providerId : {p.provider_id})"
        lines.append(header)
        if p.accounts:
            for sub in p.accounts:
                type_part = f", type: {sub.type}" if sub.type else ""
                lines.append(f"    • {sub.name} (id : {sub.id}{type_part})")

    return "\n".join(lines)
