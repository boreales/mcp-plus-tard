from app.services import PlusTardClient


async def register_user(
    client: PlusTardClient,
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
    response = await client.register_user(email=email, language=language)

    user = response.user
    lines = [
        f"✅ Utilisateur créé — id : {user.id}",
    ]
    if user.email:
        lines.append(f"Email : {user.email}")
    if user.language:
        lines.append(f"Langue : {user.language}")
    lines.append("")
    lines.append("URL de connexion OAuth (à ouvrir dans un navigateur, valide 24h) :")
    lines.append(response.oauth_url)
    return "\n".join(lines)
