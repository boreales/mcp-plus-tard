from app.services import PlusTardClient


async def list_accounts(client: PlusTardClient) -> str:
    """Liste tous les comptes réseaux sociaux connectés à Plus Tard.
    Utilise ce tool pour savoir quels comptes sont disponibles
    avant de planifier un post.

    Pour chaque compte, le champ `page_id` retourné est la valeur à
    passer telle quelle au paramètre `page_id` de `schedule_post`.
    NE PAS utiliser le champ `internal_id` (identifiant interne Plus
    Tard) comme page_id — cela créerait un post mal rattaché.
    """
    response = await client.list_accounts()

    if not response.accounts:
        return "Aucun compte réseau social n'est connecté à Plus Tard."

    lines = [f"{len(response.accounts)} compte(s) connecté(s) à Plus Tard :", ""]
    for account in response.accounts:
        lines.append(
            f"- {account.name}\n"
            f"    page_id (à utiliser pour schedule_post) : {account.account_id}\n"
            f"    internal_id (Plus Tard, NE PAS utiliser pour planifier) : {account.id}"
        )
    return "\n".join(lines)
