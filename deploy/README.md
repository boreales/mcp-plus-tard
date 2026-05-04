# Déploiement MCP sur VPS Ubuntu (nginx-proxy + Docker)

Ce projet est conçu pour s'intégrer dans un stack VPS qui utilise déjà
[nginx-proxy](https://github.com/nginx-proxy/nginx-proxy) +
[acme-companion](https://github.com/nginx-proxy/acme-companion) pour
servir plusieurs sites Docker en HTTPS automatique (comme le projet
Plus Tard principal).

Aucun fichier vhost manuel : nginx-proxy détecte le conteneur et publie
le sous-domaine tout seul à partir des variables d'environnement.

## 1. Prérequis sur le VPS

- nginx-proxy déjà en place avec son réseau externe `nginx-proxy_proxy`
- acme-companion (Let's Encrypt) déjà en place
- Le DNS `mcp.plus-tard.com` pointe sur le VPS (DNS only, voir notes)

## 2. Cloner et configurer

```bash
cd /srv  # ou ton emplacement habituel
sudo git clone <url-du-repo> mcp-plustard
cd mcp-plustard

cp .env.example .env
sudo nano .env
# PLUS_TARD_BASE_URL=https://plus-tard.com
# MCP_HOST=0.0.0.0
# MCP_PORT=8001
```

## 3. Installer le snippet Nginx pour le SSE (une fois)

Le MCP utilise Server-Sent Events. Sans désactiver le buffering, les
sessions sont coupées. nginx-proxy permet d'ajouter un fichier de config
par vhost dans `/etc/nginx/vhost.d/<hostname>` du conteneur nginx-proxy.

Le stack nginx-proxy de Plus Tard utilise un **volume Docker nommé**
(`vhost`) pour `/etc/nginx/vhost.d`, donc on copie le fichier directement
dans le conteneur :

```bash
sudo docker cp deploy/vhost.d/mcp.plus-tard.com \
               nginx-proxy:/etc/nginx/vhost.d/mcp.plus-tard.com

sudo docker exec nginx-proxy nginx -s reload
```

> Le volume `vhost` étant persistant, le fichier survit aux redémarrages
> et upgrades du conteneur nginx-proxy. Si tu recrées **complètement**
> le stack nginx-proxy (ex. `docker compose down -v`), il faudra
> réappliquer cette étape.

## 4. Démarrer le conteneur MCP

```bash
sudo docker compose up -d --build
sudo docker compose logs -f mcp   # vérifie le démarrage
```

nginx-proxy détecte le conteneur via les vars `VIRTUAL_HOST` /
`VIRTUAL_PORT` et acme-companion demande le certificat à Let's Encrypt
via `LETSENCRYPT_HOST`. Compte ~30 s pour que le certificat soit délivré
au premier démarrage.

## 5. Tester depuis l'extérieur

```bash
curl https://mcp.plus-tard.com/health
# → {"status":"ok"}

# Test MCP initialize complet
curl -i -X POST https://mcp.plus-tard.com/mcp/ \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "X-Api-Key: ta_clef" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"curl","version":"0"}}}'
# Statut attendu: 200 OK + content-type: text/event-stream
```

## 6. Mettre à jour le serveur

```bash
cd /srv/mcp-plustard
sudo git pull
sudo docker compose up -d --build
```

Pas besoin de toucher nginx-proxy. Le snippet vhost.d reste en place.

## Notes utiles

### Pare-feu

Aucun port à ouvrir pour le MCP : il n'est pas exposé directement
(`expose: 8001` rend le port visible uniquement aux conteneurs partageant
le network). Seuls 80 + 443 du nginx-proxy sont accessibles, et c'est
nginx-proxy qui parle au conteneur via le réseau Docker.

### Cloudflare

Garde `mcp.plus-tard.com` en **DNS only** (nuage gris) au moins au
démarrage, pour que SSE passe sans buffering proxy ni timeout
artificiel. Tu pourras passer en proxied plus tard si tu prends un plan
Business / Enterprise.

### Diagnostic

```bash
# Logs du MCP
sudo docker compose logs --tail=200 mcp

# Logs du nginx-proxy (depuis son stack)
sudo docker logs <nom-conteneur-nginx-proxy> --tail=200

# Logs d'acme-companion (si le certif n'arrive pas)
sudo docker logs <nom-conteneur-acme-companion> --tail=200
```

### Plus Tard sur le même VPS

`PLUS_TARD_BASE_URL=https://plus-tard.com` (URL publique) est le plus
simple et marche tout de suite. Si tu veux que le MCP appelle Symfony
via le réseau Docker interne (un hop en moins), ajoute le réseau du
stack Plus Tard dans `docker-compose.yml` et utilise
`PLUS_TARD_BASE_URL=http://<nom-service-symfony>` — mais ce n'est pas
prioritaire.
