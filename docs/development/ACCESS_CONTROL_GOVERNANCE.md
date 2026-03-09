# Governança de Acesso (Keycloak + Casbin)

## Objetivo

Garantir autorização dinâmica e auditável sem alteração de código para cada nova regra.

## Componentes

- **Keycloak**: autenticação, usuários, grupos e papéis.
- **Casbin**: decisão de autorização por política dinâmica.
- **Catálogo de recursos** (`access_resources`): inventário de recursos protegidos (API/UI/menu/componentes).
- **Auditoria**: toda alteração de políticas e catálogo gera evento em trilha de auditoria.

## Fluxo de autorização

1. Frontend autentica com Keycloak (OIDC) e envia `Authorization: Bearer <token>`.
2. Backend valida assinatura e issuer do token via JWKS do Keycloak.
3. Backend extrai sujeitos (`user:*`, `role:*`, `group:*`).
4. Casbin avalia política por prioridade (`deny` tem precedência via prioridade de política).
5. Endpoint retorna `403` quando negado e registra evento de auditoria.

## Endpoints de governança

- `GET /api/v1/access-control/whoami`
- `POST /api/v1/access-control/authorize`
- `POST /api/v1/access-control/authorize/batch`
- `GET /api/v1/access-control/resources`
- `POST /api/v1/access-control/resources/upsert`
- `POST /api/v1/access-control/resources/sync-api`
- `GET /api/v1/access-control/policies`
- `POST /api/v1/access-control/policies`
- `DELETE /api/v1/access-control/policies`
- `GET /api/v1/access-control/grouping`
- `POST /api/v1/access-control/grouping`
- `DELETE /api/v1/access-control/grouping`
- `POST /api/v1/access-control/check`

## Plugin Chat (dinâmico)

- Plugin: `chat-hub` (manifesto em `backend/plugins/chat_hub/manifest.json`)
- Endpoints:
  - `POST /api/v1/plugins/chat/messages`
  - `POST /api/v1/plugins/chat/messages/list`
  - `GET /api/v1/plugins/chat/rooms`
- Permissões recomendadas:
  - `ui:/plugins/chat` + `view`
  - `ui:/plugins/chat/send` + `create`
  - `api:/api/v1/plugins/chat/messages` + `create`
  - `api:/api/v1/plugins/chat/messages/list` + `view`
  - `api:/api/v1/plugins/chat/rooms` + `view`

## Convenções de política

- `subject`: `user:admin`, `role:manager`, `group:financeiro`
- `resource_regex`: regex sobre recurso (ex.: `api:/financial/transactions`)
- `action_regex`: regex sobre ação (ex.: `view|create|edit|delete|execute`)
- `effect`: `allow` ou `deny`
- `priority`: menor número = maior precedência

## Operação inicial

1. Subir stack com Keycloak:
   - `docker compose --env-file .env.docker.local up -d --build`
2. Aplicar migrações:
   - `docker compose --env-file .env.docker.local exec api alembic upgrade head`
3. Sincronizar catálogo API:
   - `POST /api/v1/access-control/resources/sync-api`
4. Inserir políticas iniciais para perfis de negócio.

## Governança contínua

- `python run_governance.py` agora inclui `tools/authz_guard.py`, que falha se endpoints HTTP ficarem sem `require_permission`.
- Toda mudança de política é auditada com área `security`.
