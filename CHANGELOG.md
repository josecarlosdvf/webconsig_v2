# Changelog

Todas as mudanças relevantes deste projeto serão documentadas aqui.

O formato segue Keep a Changelog e o versionamento segue SemVer.

## [1.0.0] - 2026-03-09

### Added

- Estrutura canônica `backend/` e `frontend/` com stack moderna.
- `.env` único na raiz com configuração centralizada.
- Base de Docker/Compose para API, Web e infraestrutura local opcional.
- Workflows de governança e build Docker no GitHub Actions.
- Regras de governança, ADR e arquitetura em `docs/`.

### Changed

- Padronização de naming e execução para runtime moderno apenas.

### Removed

- Fluxo operacional legado baseado em `apps/`, `templates/` e `static/`.
