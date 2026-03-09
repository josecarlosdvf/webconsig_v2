# Arquitetura Alvo e Regras de Evolução

## Princípios

- Separação clara entre transporte, aplicação, domínio e infraestrutura.
- Contratos explícitos.
- Observabilidade por padrão (audit + debug).
- Evolução incremental com compatibilidade.

## Regras de dependência

- `api -> application -> adapters/domain/core`
- `application -> adapters/domain/core`
- `adapters -> domain/core`
- `domain` não depende de `api`.

## Antipadrões proibidos

- SQL em endpoint.
- Acesso direto a gateway pelo endpoint.
- Duplicação de caso de uso já existente.
- Acoplamento circular entre módulos.

## Versionamento de contratos

- Mudanças incompatíveis: criar nova versão (`/api/v2`) ou compatibilização por período definido.

## Critério de modularização

Criar novo módulo quando:

- novo bounded context,
- nova integração externa crítica,
- novo ciclo de deploy desejado.
