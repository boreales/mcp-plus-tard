# Déploiement MCP sur VPS Ubuntu (Nginx + Docker)

## 1. Préparer le serveur (une fois)

```bash
# Sur le VPS, dans le répertoire où tu héberges tes services Docker
cd /srv  # ou /opt, /var/www — adapte au standard de ton VPS
sudo git clone <url-du-repo> mcp-plustard
cd mcp-plustard
```

## 2. Configurer l'environnement

```bash
cp .env.example .env
# Édite .env :
#   PLUS_TARD_BASE_URL=https://plus-tard.com   (ou l'URL interne du conteneur Symfony)
#   MCP_HOST=0.0.0.0
#   MCP_PORT=8001
nano .env
```

> **Note** : si tu veux que le MCP appelle Plus Tard via le réseau Docker
> interne (plus rapide, ne sort pas sur internet), partage le même
> network entre le conteneur Symfony et celui-ci, et utilise le nom de
> service Docker comme host (ex. `PLUS_TARD_BASE_URL=http://plustard-app`).
> Pour démarrer simple, garde l'URL publique : ça marche tout de suite.

## 3. Lancer le conteneur

```bash
sudo docker compose up -d --build
sudo docker compose logs -f mcp   # vérifie le démarrage, Ctrl+C pour quitter
curl http://127.0.0.1:8001/health
# → {"status":"ok"}
```

## 4. Configurer Nginx

```bash
sudo cp deploy/nginx.conf.example /etc/nginx/sites-available/mcp.plus-tard.com
sudo ln -s /etc/nginx/sites-available/mcp.plus-tard.com /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 5. Obtenir le certificat TLS

```bash
sudo certbot --nginx -d mcp.plus-tard.com
```

certbot édite la config Nginx pour pointer vers les bons fichiers. Le
renouvellement est automatique (vérifie avec `systemctl list-timers | grep certbot`).

## 6. Tester depuis l'extérieur

```bash
# Depuis ta machine, pas le VPS
curl https://mcp.plus-tard.com/health
# → {"status":"ok"}

# Test MCP initialize
curl -i -X POST https://mcp.plus-tard.com/mcp/ \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "X-Api-Key: ta_clef" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"curl","version":"0"}}}'
# Statut attendu: 200 OK + content-type: text/event-stream
```

## 7. Mettre à jour le serveur

```bash
cd /srv/mcp-plustard
sudo git pull
sudo docker compose up -d --build
```

Pas besoin de toucher Nginx — il proxie un port local fixe.

## Vérifier que tout va bien

```bash
# logs récents
sudo docker compose logs --tail=200 mcp

# état du conteneur
sudo docker compose ps

# stats
sudo docker stats plus-tard-mcp --no-stream
```

## Pare-feu

Le port 8001 doit rester **fermé** sur l'interface publique (le bind
`127.0.0.1:8001` du `docker-compose.yml` le garantit). Seuls 80 + 443
sont exposés, et c'est Nginx qui parle au conteneur en local.
