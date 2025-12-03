# Documentação Técnica - Webconsig v2

## 1. Visão Geral
O **Webconsig v2** é um sistema web de gestão de crédito consignado e CRM, desenvolvido com Flask e Bootstrap 5 (Volt Dashboard). O sistema oferece funcionalidades completas para gestão de clientes, propostas de empréstimo, integração com WhatsApp e ferramentas administrativas.

## 2. Arquitetura e Tecnologias

### Backend
- **Linguagem:** Python 3.10+
- **Framework:** Flask 3.0
- **ORM:** SQLAlchemy 2.0
- **Banco de Dados:** SQL Server (Produção) / SQLite (Desenvolvimento)
- **Autenticação:** Flask-Login
- **Formulários:** Flask-WTF

### Frontend
- **Framework CSS:** Bootstrap 5 (Volt Theme)
- **Template Engine:** Jinja2
- **JavaScript:** Vanilla JS (com alguns scripts específicos nos templates)

### Integrações
- **WhatsApp:** Integração via API externa (Rocha Promotora)
- **CEP:** ViaCEP
- **CPF:** Lemit (Consulta de dados)

## 3. Estrutura de Diretórios

```
Webconsig_v2/
├── apps/                   # Núcleo da aplicação (Blueprints)
│   ├── admin/              # Administração do sistema
│   ├── api/                # APIs utilitárias (CEP, CPF)
│   ├── authentication/     # Login e gestão de usuários
│   ├── clientes/           # Gestão de Clientes (CRM)
│   ├── database/           # Configuração de DB e Seeds
│   ├── files/              # Gestão de Arquivos/Uploads
│   ├── home/               # Dashboard principal
│   ├── hr/                 # Recursos Humanos
│   ├── messaging/          # Integração WhatsApp
│   ├── propostas/          # Gestão de Empréstimos
│   ├── services/           # Serviços externos (ViaCEP, Lemit)
│   ├── settings/           # Configurações do sistema
│   ├── __init__.py         # App Factory
│   └── config.py           # Configurações gerais
├── instance/               # Dados de instância (SQLite)
├── static/                 # Arquivos estáticos (CSS, JS, Imagens)
├── templates/              # Templates HTML (Jinja2)
├── uploads/                # Diretório de uploads
├── run.py                  # Entry point da aplicação
└── requirements.txt        # Dependências Python
```

## 4. Módulos Principais

### 4.1. Clientes (`apps/clientes`)
Responsável pelo cadastro e gestão de clientes.
- **Entidade Principal:** `Cliente` (Chave Primária: CPF)
- **Dados Relacionados:**
  - Telefones, Emails, Endereços
  - Identidade, Dados Bancários
  - Matrículas, Data de Nascimento
- **Funcionalidades:**
  - CRUD completo de clientes.
  - Formulário unificado para cadastro de dados relacionados.
  - Validação e formatação de CPF.

### 4.2. Propostas (`apps/propostas`)
Gerencia o ciclo de vida das propostas de empréstimo.
- **Entidades Principais:** `Proposta`, `Tabela`, `RPCProposta`, `BoletoProposta`.
- **Fluxo de Status:** O sistema implementa um fluxo complexo de status (`PropostaStatus`), incluindo:
  - `AGUARD_DIGITACAO` -> `DIGITADO_BANCO` -> `AVERBADO` -> `PAGO_BANCO`
  - Status de erro/cancelamento: `CANCELADA`, `PENDENTE`.
- **Funcionalidades:**
  - Gestão de Tabelas de Empréstimo (com fatores diários).
  - Acompanhamento de etapas (Comercial, Averbação, Financeiro).

### 4.3. Messaging (`apps/messaging`)
Módulo de integração com WhatsApp para comunicação com clientes.
- **Entidades Principais:** `WhatsAppConnection`, `WhatsAppMessage`.
- **Funcionalidades:**
  - Gestão de múltiplas conexões WhatsApp.
  - Envio de mensagens de texto e mídia.
  - Controle de Rate Limiting (mensagens por minuto/hora).
  - Dashboard de estatísticas de mensagens.

### 4.4. API (`apps/api`)
Fornece endpoints utilitários para o frontend e uso interno.
- **Endpoints:**
  - `/api/cep/<cep>`: Consulta de endereço via ViaCEP.
  - `/api/cep/validar/<cep>`: Validação de formato de CEP.
  - `/api/cep/buscar`: Busca de CEP por endereço.
  - Rotas de consulta Lemit (CPF).

## 5. Banco de Dados

O sistema utiliza SQLAlchemy como ORM. As principais tabelas são:

- **`clientes`**: Tabela central de clientes.
- **`propostas`**: Registros de empréstimos vinculados a clientes e tabelas.
- **`tabelas`**: Definições de condições de empréstimo (taxas, prazos).
- **`whatsapp_connections`**: Configurações de conexão com API WhatsApp.
- **`whatsapp_messages`**: Log de mensagens enviadas/recebidas.
- **`users`**: Usuários do sistema (autenticação).

## 6. Configuração

As configurações são gerenciadas via variáveis de ambiente (`.env`) e classe `Config` em `apps/config.py`.

**Principais Variáveis (.env):**
- `DB_ENGINE`: Tipo de banco (mssql, sqlite).
- `DB_HOST`, `DB_NAME`, `DB_USERNAME`, `DB_PASSWORD`: Credenciais do banco.
- `SECRET_KEY`: Chave de segurança do Flask.

## 7. Instalação e Execução

1.  **Ambiente Virtual:** Criar e ativar (`python -m venv venv`).
2.  **Dependências:** Instalar (`pip install -r requirements.txt`).
3.  **Configuração:** Criar `.env` baseado no `.env.example`.
4.  **Banco de Dados:** Inicializar (`python seeds.py`).
5.  **Execução:** Rodar (`python run.py`).
