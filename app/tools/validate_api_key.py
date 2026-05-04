from app.services import PlusTardClient


async def validate_api_key(client: PlusTardClient) -> str:
    """Vérifie que la clef API Plus Tard fournie est valide.
    Utilise ce tool si l'utilisateur veut diagnostiquer un problème
    d'authentification ou simplement confirmer que sa clef est active.
    Retourne aussi la date de création et d'expiration de la clef.
    """
    response = await client.validate_api_key()

    if not response.valid:
        return "❌ La clef API n'est pas valide."

    info = response.api_key
    if info is None:
        return "✅ La clef API est valide."

    parts = ["✅ La clef API est valide."]
    if info.created_at:
        parts.append(f"Créée le : {info.created_at.strftime('%d/%m/%Y')}")
    if info.expires_at:
        parts.append(f"Expire le : {info.expires_at.strftime('%d/%m/%Y')}")
    if info.last_used_at:
        parts.append(
            f"Dernière utilisation : {info.last_used_at.strftime('%d/%m/%Y %H:%M UTC')}"
        )
    return "\n".join(parts)
