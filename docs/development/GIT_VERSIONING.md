# Git Versioning (Webconsig)

## Estratégia de branches

- `main`: branch estável de produção.
- `develop` (opcional): integração contínua de features.
- `feature/*`: novas funcionalidades.
- `fix/*`: correções de bug.
- `hotfix/*`: correções urgentes em produção.

## Convenção de commit

Formato:

`tipo(escopo): descrição curta`

Tipos recomendados:

- `feat`: nova funcionalidade
- `fix`: correção de bug
- `refactor`: refatoração sem mudança funcional
- `docs`: documentação
- `chore`: manutenção técnica
- `ci`: pipeline/workflow
- `perf`: melhoria de performance
- `test`: testes

Exemplos:

- `feat(api): adiciona endpoint de auditoria`
- `fix(frontend): corrige envio de idempotency-key`
- `ci(docker): ajusta build da imagem web`

## Versionamento SemVer

Padrão: `MAJOR.MINOR.PATCH`

- `MAJOR`: quebra de compatibilidade.
- `MINOR`: funcionalidade nova compatível.
- `PATCH`: correção compatível.

## Fluxo de release

1. Atualizar `VERSION`.
2. Atualizar `CHANGELOG.md`.
3. Criar commit de release:
   - `chore(release): vX.Y.Z`
4. Criar tag anotada:
   - `git tag -a vX.Y.Z -m "release vX.Y.Z"`
5. Publicar tag:
   - `git push origin vX.Y.Z`

## Regras mínimas antes de merge

- Passar checks de CI.
- Não introduzir mudanças em camadas proibidas.
- Atualizar documentação quando houver mudança de contrato.
