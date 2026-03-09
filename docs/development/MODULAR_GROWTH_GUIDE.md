# Guia de Crescimento Modular

## Objetivo

Permitir evolução contínua sem transformar o sistema em colcha de retalhos.

## Regras práticas para novas features

1. Criar caso de uso em `application/services`.
2. Expor via endpoint fino em `api/v1/endpoints`.
3. Persistência/integrações somente em `adapters/gateways`.
4. Adicionar contratos em `domain/schemas`.
5. Garantir observabilidade (audit + debug).

## Fluxo obrigatório

1. Issue -> escopo e impacto
2. ADR (se estrutural)
3. Implementação por módulo
4. `python run_governance.py`
5. PR com checklist de governança

## Critérios para plugin/modulo futuro

- Sem alteração direta no core em cada novo recurso.
- Registro por interface/contrato.
- Ciclo de vida (habilitar, desabilitar, versionar) definido.
