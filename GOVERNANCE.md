# Governança de Engenharia - Webconsig

## Objetivo

Garantir crescimento homogêneo, sem quebra de core, sem duplicação indevida e com evolução orientada por arquitetura.

## Regras mandatórias

1. **Sem mudanças no core sem ADR**: qualquer alteração estrutural exige ADR aprovada.
2. **Sem lógica de banco em endpoints/controllers**.
3. **Sem dependência invertida entre camadas**.
4. **Sem duplicação de arquivos/funções**: reutilizar módulo existente ou justificar no PR.
5. **Sem merge sem passar checks de governança**.

## Camadas e responsabilidades

- `app/api`: transporte HTTP, autenticação de borda e contratos.
- `app/application`: casos de uso e regras de negócio.
- `app/adapters`: acesso a infra (db, filas, integrações).
- `app/domain`: modelos e contratos de domínio.
- `app/core`: cross-cutting (config, db, logging, debug).

## Fluxo de mudança

1. Abrir issue com contexto e impacto.
2. Se estrutural, criar ADR em `docs/adr`.
3. Implementar em branch curta.
4. Abrir PR usando template e checklist.
5. Passar `governance_check` + build.
6. Merge com `CODEOWNERS`.

## Política de extensibilidade

- Novos recursos devem entrar como módulos isolados, sem alterar APIs internas existentes sem versionamento.
- Toda expansão deve depender de interfaces/gateways e não de implementação concreta.
- Alterações breaking exigem:
  - ADR
  - Migração de dados versionada
  - Plano de rollback

## Definition of Done

- Arquitetura preservada.
- Sem duplicação introduzida.
- Logs/auditoria atualizados para o novo fluxo.
- Contratos atualizados.
- Documentação de operação e troubleshooting atualizada.
