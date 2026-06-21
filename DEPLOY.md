# Internal staging — one server (Docker Compose)

Suitable for your team to try the platform on a **single VM or machine** on the LAN.

## Prerequisites

- Docker Desktop or Docker Engine + Compose v2
- Ports **3000** (UI) and **8000** (API + WebSocket) open on the server firewall

## Deploy

1. Copy environment file and edit:

   ```bash
   cp .env.docker.example .env
   ```

   Edit `.env`:

   - `SECRET_KEY` — run `openssl rand -hex 32` (or any long random string)
   - `POSTGRES_PASSWORD` — strong password
   - `CORS_ORIGINS` — add your server URL, e.g. `http://192.168.1.50:3000`

2. Build and start:

   ```bash
   docker compose up --build -d
   ```

3. Check status:

   ```bash
   docker compose ps
   docker compose logs -f api
   ```

4. Open in browser (from any machine on the network):

   - **App:** `http://<SERVER-IP>:3000`
   - **API docs:** `http://<SERVER-IP>:8000/docs`

5. First use: **Register** → **Sign in** on the login page.

## How traffic flows

```text
Team browser → http://SERVER:3000/api/*  →  web container  →  api:8000
Team browser → ws://SERVER:8000/ws/live  →  api container (direct)
```

Do **not** set `NEXT_PUBLIC_API_URL` unless you intentionally want the browser to call port 8000 directly (then `CORS_ORIGINS` must include your frontend URL).

## Health checks

```bash
curl http://localhost:8000/healthz
curl http://localhost:3000/api/health
```

Both should return `{"status":"ok"}`.

## Stop / reset

```bash
docker compose down          # stop
docker compose down -v       # stop + delete DB volumes (fresh start)
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Web shows API offline | `docker compose logs api` — wait for Postgres healthy |
| Login fails | Register first; check `api` logs |
| Live charts empty | Port **8000** must be reachable for WebSocket |
| Port in use | Stop local `uvicorn` / `npm run dev` before compose |

## Not included (production later)

- HTTPS / reverse proxy (use Nginx or Caddy in front of 3000/8000)
- Backups for Postgres volume
- Real metrics (still simulated in this build)
