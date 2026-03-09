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

## Rebuild completo do stack

Para garantir que mudanças de código fiquem ativas nas imagens/containers:

```powershell
./scripts/rebuild_all.ps1
```

Opções úteis:

- `./scripts/rebuild_all.ps1 -NoCache`
- `./scripts/rebuild_all.ps1 -SkipMigrations`
- `./scripts/rebuild_all.ps1 -DryRun`

## Aplicação incremental (sem recriar tudo)

Para aplicar mudanças apenas nos serviços afetados:

```powershell
./scripts/apply_changes.ps1
```

Exemplos:

- Só backend: `./scripts/apply_changes.ps1 -Services api`
- Backend + migração: `./scripts/apply_changes.ps1 -Services api`
- Só frontend+gateway: `./scripts/apply_changes.ps1 -Services web,gateway -SkipMigrations`
- Apenas restart (sem build): `./scripts/apply_changes.ps1 -Services api -OnlyRestart`
- Simular comandos: `./scripts/apply_changes.ps1 -DryRun`

## IAM e Autorização dinâmica (Keycloak + Casbin)

- Keycloak (OIDC) é o provedor de autenticação e papéis/grupos.
- Casbin é o motor de autorização dinâmica orientado por políticas.
- Governança: recursos e políticas podem ser gerenciados sem alteração de código.

Subida local com IAM:

```bash
cp .env.docker.example .env.docker.local
docker compose --env-file .env.docker.local up -d --build
docker compose --env-file .env.docker.local exec api alembic upgrade head
```

URLs padrão:

- App seguro: `https://localhost:15443`
- Keycloak (via gateway): `https://localhost:15443/auth`

Credenciais iniciais do realm importado:

- Usuário: `admin`
- Senha: `Admin@123!ChangeMe`

Detalhes de governança em `docs/development/ACCESS_CONTROL_GOVERNANCE.md`.

Rotas administrativas adicionadas no frontend:

- `/admin/permissoes` (matriz visual de políticas e agrupamentos)
- `/plugins/chat` (chat como plugin com permissão dinâmica)

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
