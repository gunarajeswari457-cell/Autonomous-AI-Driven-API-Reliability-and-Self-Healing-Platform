# Autonomous AI-Driven API Reliability and Self-Healing Platform

Enterprise-style observability dashboard (Next.js) + control API (FastAPI).

## Connect frontend ↔ backend (local)

```text
Browser (localhost:3000)
    │
    ├─ REST  →  /api/*  →  Next.js proxy  →  http://127.0.0.1:8000/api/*
    ├─ Auth  →  /api/auth/login|register  →  Next route handlers  →  backend
    └─ WS    →  ws://localhost:8000/ws/live  (direct to API)
```

### 1. Start backend

```powershell
cd backend
.\run.ps1
```

API: http://127.0.0.1:8000 · Health: http://127.0.0.1:8000/healthz

### 2. Start frontend

```powershell
cd frontend
npm install
npm run dev
```

App: http://localhost:3000

### 3. Sign in

1. Open http://localhost:3000/login  
2. **Register** once (demo fields are prefilled)  
3. **Sign in** → dashboard loads live metrics over WebSocket  

### Configuration

| File | Purpose |
|------|---------|
| `frontend/.env.local` | `API_PROXY_TARGET` → where Next proxies `/api/*` |
| `frontend/.env.example` | Template for frontend env |
| `backend/.env.example` | `CORS_ORIGINS`, `SECRET_KEY`, `DATABASE_URL` |

After changing `.env.local`, **restart** `npm run dev`.

### Verify connection

- http://localhost:3000/api/health → `{"status":"ok"}`  
- http://127.0.0.1:8000/healthz → `{"status":"ok"}`  

### Docker — internal team on one server

See **[DEPLOY.md](./DEPLOY.md)** for full steps.

```bash
cp .env.docker.example .env
# edit SECRET_KEY, POSTGRES_PASSWORD, CORS_ORIGINS (add your server IP)
docker compose up --build -d
```

Open `http://<server-ip>:3000` (WebSocket uses port **8000** on the same host).
