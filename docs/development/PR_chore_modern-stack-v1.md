# PR: Baseline modern stack v1.0.0

## Tipo de mudança

- [x] Arquitetural
- [x] Refactor
- [x] CI
- [x] Documentação

## Resumo

Consolida a base modern-only do Webconsig com `backend/` + `frontend/`, remove runtime legado, padroniza governança e estabelece baseline de release `v1.0.0`.

## Principais entregas

- Migração para stack moderna com FastAPI + React/Vite.
- Remoção operacional do legado (`apps/`, `templates/`, `static/` não participam mais do runtime).
- `.env` único na raiz.
- Docker/Compose para API/Web e infra local opcional.
- Workflows de CI/CD e governança no GitHub Actions.
- Guia de versionamento Git (`VERSION`, `CHANGELOG.md`, `docs/development/GIT_VERSIONING.md`).

## Checklist de governança

- [x] Não há lógica de banco em endpoint/controller
- [x] Dependências entre camadas continuam válidas
- [x] Não houve duplicação de arquivo/função
- [x] Logs/auditoria/debug foram atualizados
- [x] Contratos/documentação foram atualizados
- [x] ADR criada/atualizada (se necessário)

## Validação executada

- `backend/python run_governance.py`
- `backend/alembic upgrade head`
- `frontend/npm run build`
- `docker compose config`

## Impacto

- Alto impacto positivo em padronização, manutenção e readiness de produção.
- Mudança estrutural sem compatibilidade com fluxo legado.

## Plano de rollback

- Reverter para commit/tag anterior estável em `main`.
- Reaplicar configuração anterior de runtime caso necessário.
