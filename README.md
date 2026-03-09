# Webconsig v2 — Modern-Only

Este repositório opera exclusivamente com stack moderna:

- Backend: FastAPI + SQLAlchemy + Alembic + PostgreSQL + Redis
- Frontend: React + Vite + Tailwind + Headless UI

## Execução oficial

Arquivo de configuração único: `.env` na raiz do repositório.

### Backend

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
python run_api.py
```

API base (dev direto): `http://localhost:8001/api/v1`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App base (dev direto): `http://localhost:5174`

## Acesso seguro (HTTPS)

O acesso recomendado em ambiente container é via gateway TLS:

```bash
cp .env.docker.example .env.docker.local
docker compose up -d --build
```

URL segura padrão:

- `https://localhost:15443`

Credenciais de acesso (Basic Auth) via `.env`:

- `HTTPS_ADMIN_USER`
- `HTTPS_ADMIN_PASSWORD`

No frontend, a API usa caminho relativo `/api/v1`, mantendo tráfego seguro no mesmo domínio HTTPS.

## Observação importante

Diretórios legados foram removidos e não fazem parte do runtime oficial.

## Governança

```bash
cd backend
python run_governance.py

cd ../frontend
npm run governance:check
```

## Tempo real (WebSocket + HTMX)

- WebSocket: `/api/v1/realtime/ws`
- REST fallback: `/api/v1/realtime/events`
- Fragmento HTMX: `/api/v1/realtime/htmx/audit-feed`

Contrato detalhado em:

- `docs/development/REALTIME_CONTRACTS.md`
