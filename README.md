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

API base: `http://localhost:8001/api/v1`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App base: `http://localhost:5174`

## Observação importante

Diretórios legados foram removidos e não fazem parte do runtime oficial.

## Governança

```bash
cd backend
python run_governance.py

cd ../frontend
npm run governance:check
```
