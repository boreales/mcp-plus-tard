# Plus Tard MCP

[![Python](https://img.shields.io/badge/python-3.12+-3776ab.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![MCP](https://img.shields.io/badge/MCP-Streamable_HTTP-7c3aed.svg)](https://modelcontextprotocol.io/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](#license)

> Connectez votre assistant IA (Claude, Cursor, n8n…) à
> [Plus Tard](https://plus-tard.com) pour planifier vos publications
> Facebook, Instagram, LinkedIn, X/Twitter, TikTok, Threads, Bluesky et
> Google My Business par simple conversation.

**Production endpoint** : `https://mcp.plus-tard.com/mcp/`
**Documentation utilisateur** : https://plus-tard.com/api-mcp

---

## Démo en 30 secondes

> **Vous** : « Programme un post Facebook sur ma page Boréales demain à 10h : "Hello le monde !" »
>
> **Claude** appelle automatiquement :
> 1. `list_accounts` → trouve l'identifiant Facebook de "Boréales"
> 2. `schedule_post(provider="facebook", page_id="…", planned_at="2026-05-05T10:00:00Z", text="Hello le monde !")`
>
> **Plus Tard** : ✅ Post #1432 planifié pour le 05/05/2026 à 10h00.

---

## Tools (5)

| Tool | Description |
|---|---|
| `validate_api_key` | Vérifie qu'une clef API est active et retourne ses métadonnées. |
| `list_accounts` | Liste tous les comptes réseaux sociaux connectés à Plus Tard. |
| `schedule_post` | Planifie un post sur un seul réseau (1 appel = 1 réseau). |
| `register_user` | Crée un nouvel utilisateur et retourne une URL OAuth. |
| `get_user` | Détail d'un utilisateur : providers connectés et sous-comptes. |

## Resources (2)

| URI | Contenu |
|---|---|
| `plus-tard://accounts` | Liste JSON des comptes connectés. |
| `plus-tard://users/{id}` | Détail JSON d'un utilisateur. |

---

## Installation côté client

### Claude Desktop

Ajoutez à `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) :

```json
{
  "mcpServers": {
    "plus-tard": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "https://mcp.plus-tard.com/mcp/",
        "--header",
        "X-Api-Key:${PLUS_TARD_TOKEN}"
      ],
      "env": {
        "PLUS_TARD_TOKEN": "your_plus_tard_api_key"
      }
    }
  }
}
```

### Claude Code (CLI)

```bash
claude mcp add plus-tard \
  --transport http https://mcp.plus-tard.com/mcp/ \
  --header "X-Api-Key: your_plus_tard_api_key"
```

### Claude.ai (web)

Settings → Connectors → Add custom connector — URL `https://mcp.plus-tard.com/mcp/`, header `X-Api-Key: your_key`.

### Cursor / n8n

Mêmes URL et header. Voir la [doc complète](https://plus-tard.com/api-mcp).

---

## Self-host (pour développeurs)

### Stack

- Python 3.12 · FastAPI · `mcp[fastapi]` (Streamable HTTP transport)
- httpx · pydantic v2 · pydantic-settings
- pytest · pytest-asyncio · respx

### Architecture

```
Client (Claude/Cursor/n8n)
   │  Streamable HTTP + X-Api-Key header
   ▼
MCP server (this repo)
   │  X-Api-Key forwarded as-is
   ▼
Plus Tard Symfony API
```

Chaque requête MCP arrive avec `X-Api-Key`, qui est propagé tel quel à
l'API Plus Tard. Pas de session, pas de stockage côté serveur — chaque
client utilise sa propre clef.

### Développement local

```bash
git clone https://github.com/<votre-org>/plus-tard-mcp.git
cd plus-tard-mcp

python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

cp .env.example .env
# Édite .env : PLUS_TARD_BASE_URL=https://plus-tard.com

uvicorn main:app --reload --port 8001
```

Le serveur écoute sur `http://127.0.0.1:8001/mcp/`. Test rapide avec le
[MCP Inspector](https://github.com/modelcontextprotocol/inspector) :

```bash
npx @modelcontextprotocol/inspector
# Transport: Streamable HTTP
# URL: http://127.0.0.1:8001/mcp/
# Header: X-Api-Key = ta_clef_plus_tard
```

### Tests

```bash
pytest
# 24 passed
```

### Déploiement Docker (production)

Le dépôt fournit `Dockerfile` + `docker-compose.yml` prêts pour un VPS
avec [nginx-proxy](https://github.com/nginx-proxy/nginx-proxy) +
[acme-companion](https://github.com/nginx-proxy/acme-companion) :

```bash
sudo docker compose up -d --build
```

Voir [`deploy/README.md`](deploy/README.md) pour le détail (snippet
nginx-proxy SSE-friendly, gestion TLS Let's Encrypt, mise à jour).

---

## Configuration

| Variable | Description | Défaut |
|---|---|---|
| `PLUS_TARD_BASE_URL` | URL de base de l'API Plus Tard | *(requis)* |
| `MCP_HOST` | Bind host pour uvicorn | `0.0.0.0` |
| `MCP_PORT` | Bind port pour uvicorn | `8001` |

L'authentification se fait par requête via le header `X-Api-Key` —
**aucun token n'est stocké côté serveur**.

### Hosts autorisés

Le SDK MCP active une protection anti-DNS rebinding qui n'autorise que
les hôtes whitelistés. Les hôtes par défaut sont :

- `mcp.plus-tard.com`
- `localhost`, `127.0.0.1` (pour le dev)

Pour ajouter votre propre domaine, éditez la liste dans `main.py`
(`TransportSecuritySettings.allowed_hosts`).

---

## Structure du projet

```
.
├── main.py                # FastAPI + FastMCP + middleware X-Api-Key
├── app/
│   ├── config.py          # Settings via pydantic-settings
│   ├── auth/              # Dependency X-Api-Key (réutilisable hors MCP)
│   ├── models/            # Schémas pydantic v2 (post, account, user)
│   ├── services/          # PlusTardClient async (httpx)
│   └── tools/             # 5 tools métier (str → str)
├── tests/                 # 24 tests pytest-asyncio
├── deploy/
│   ├── README.md          # Guide déploiement VPS
│   ├── vhost.d/           # Snippet nginx-proxy SSE
│   └── twig/              # Template Symfony pour la doc utilisateur
├── docs/index.html        # Doc utilisateur statique (HTML)
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

---

## Sécurité

- **HTTPS uniquement** en production (TLS via Let's Encrypt).
- **Pas de log** du contenu des posts ni des tokens API.
- **Anti-DNS rebinding** via `TransportSecuritySettings` du SDK MCP.
- **Multi-tenancy isolée** : chaque requête est traitée avec son propre
  client httpx, fermé en fin de requête (pas de pooling cross-user).
- Si vous suspectez qu'une clef a fuité, révoquez-la depuis votre
  espace Plus Tard.

---

## Roadmap

- [ ] Logging structuré (JSON, sans tokens ni contenus)
- [ ] Rate limiting par clef API
- [ ] Métriques Prometheus
- [ ] OAuth flow pour les connecteurs (au lieu d'une clef API copy-paste)
- [ ] Support `completion/complete` MCP pour suggestions de `page_id`
  (en attente d'un SDK Python qui expose `ToolReference`)

Idées et contributions bienvenues — ouvrez une issue ou une PR.

---

## Liens utiles

- [Documentation utilisateur](https://plus-tard.com/api-mcp)
- [API Plus Tard](https://plus-tard.com/api-documentation) (v1.2)
- [Spécification MCP](https://modelcontextprotocol.io/)
- [MCP Inspector](https://github.com/modelcontextprotocol/inspector)
- [mcp-remote](https://www.npmjs.com/package/mcp-remote) (pont stdio↔HTTP pour Claude Desktop)

---

## License

MIT © 2026 [Plus Tard](https://plus-tard.com) — Boréales Créations.

Made with ❤️ in France.
