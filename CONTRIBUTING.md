# Fluxo de Contribuição e Operação do Copilot (GitHub)

Objetivo: manter uma única linha de desenvolvimento estável (`main`), evitar ramos paralelos abandonados e garantir PRs pequenos, revisáveis e sem conflitos.

## Linha Única de Verdade
- Branch padrão: `main`.
- Releases marcadas com tags semânticas: `vX.Y.Z` (ex.: `v0.2.0`).
- Evite manter branches long-lived paralelas. Use branches curtas de feature e PRs pequenos.

## Naming de Branches
- Features: `feature/<escopo>-<descricao-curta>`
  - Exemplos: `feature/hr-team-color`, `feature/auth-avatar-upload`.
- Fixes: `fix/<area>-<descricao-curta>`
  - Exemplos: `fix/ui-sidebar-logo`, `fix/js-bootstrap-modal`.
- Hotfix (prod): `hotfix/<descricao-curta>`

Evitar usar prefixos `copilot/*` para desenvolvimento contínuo. Reservar `copilot/*` apenas para execuções automatizadas efêmeras (ver seção Copilot Agent).

## Política de Pull Requests
- Base sempre `main`.
- Tamanho reduzido: até ~300 LOC alteradas e foco em um tópico.
- Descrição clara: objetivo, arquivos tocados, impacto, testes.
- Labels obrigatórias: `consolidation` (para PRs de consolidação), `feature`, `fix` conforme o caso.
- Assign: `@josecarlosdvf`.
- Checks: executar testes e lint antes de abrir PR.

## Integração Contínua (Checks)
- Executar testes: `pytest -q`.
- Verificar estilo JS/CSS se aplicável.
- Construção local: subir app e navegar em rotas tocadas.

## Estratégia de Merge
- Preferir `Merge commit` para manter histórico de PRs.
- Resolver conflitos antes do push do PR:
  ```bash
  git fetch origin
  git checkout <branch>
  git merge origin/main
  # resolver conflitos
  git add -A
  git commit -m "merge: resolve conflicts with main"
  git push
  ```

## Limpeza de Branches
- Após merge, deletar branch remoto:
  ```bash
  gh pr merge <num> --merge --delete-branch
  # ou
  git push origin --delete <branch>
  git fetch --prune origin
  ```

## Versionamento
- Tag após merge em `main` para releases estáveis:
  ```bash
  git checkout main
  git pull
  git tag -a vX.Y.Z -m "release: vX.Y.Z"
  git push origin vX.Y.Z
  ```

## Diretrizes para o GitHub Copilot Agent

Estas regras orientam o agente para abrir PRs consistentes e evitar múltiplas linhas de desenvolvimento.

1. Branch de trabalho
   - Criar branches sempre com `feature/` ou `fix/`.
   - Não usar `copilot/*` para trabalhos persistentes. Se necessário, usar `copilot/<id>-temp` e deletar ao final automaticamente.

2. Base e destino
   - Base do PR: `main`.
   - Nunca abrir PRs entre `copilot/*`.

3. Passos ao criar PR
   - `git fetch origin && git merge origin/main` antes de abrir PR.
   - Se houver conflitos, resolver localmente; não abrir PR conflitado.
   - Adicionar label: `consolidation` ou `feature`/`fix` conforme o caso.
   - Atribuir `@josecarlosdvf`.

4. Pós-merge automático
   - Executar `--delete-branch` no merge.
   - Rodar `git fetch --prune origin` para limpar referências.
   - Criar tag de versão apenas quando solicitado explicitamente (não automático), ex.: `v0.2.1`.

5. Tamanho e escopo
   - Limitar alterações a um tema por PR.
   - Evitar edição de arquivos não relacionados.

6. Documentação de PR
   - Descrever: problema, solução, arquivos, riscos, testes.
   - Incluir instruções de verificação manual (rotas/pages afetadas).

## Comandos Úteis

Abrir PR:
```bash
gh pr create --base main --head feature/<nome> \
  --title "feat: <titulo curto>" \
  --body "<descricao>"
```

Marcar pronto, label e assign:
```bash
gh pr ready <num>
gh label create consolidation -d "Consolidation to main" -c "0366d6" # uma vez
gh pr edit <num> --add-label consolidation --add-assignee josecarlosdvf
```

Mesclar e deletar branch:
```bash
gh pr merge <num> --merge --delete-branch
git fetch --prune origin
```

## Checklist para Abrir PR
- [ ] Branch baseada em `main` e atualizada
- [ ] Testes locais OK
- [ ] Descrição clara e label aplicada
- [ ] Assign para revisão
- [ ] Sem conflitos

---

Dúvidas ou exceções: abrir issue com contexto e proposta de fluxo.
