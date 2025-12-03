# Sistema Web - Flask Volt Dashboard

Sistema web baseado no template Flask Volt Dashboard, configurado para uso com SQL Server e totalmente traduzido para pt-BR.

## 📋 Características

- ✅ **Flask 3.0** - Framework web moderno
- ✅ **SQL Server** - Banco de dados empresarial (via pyodbc)
- ✅ **SQLAlchemy 2.0** - ORM moderno
- ✅ **Bootstrap 5** - Framework CSS responsivo (Volt Theme)
- ✅ **Autenticação completa** - Login, registro, perfil
- ✅ **Sistema de configurações** - Configurações dinâmicas via banco
- ✅ **100% pt-BR** - Totalmente traduzido

## 🚀 Instalação

### 1. Pré-requisitos

- Python 3.10+
- SQL Server (ou SQLite para desenvolvimento)
- ODBC Driver 17 ou 18 for SQL Server

### 2. Clonar/Configurar o projeto

```bash
# Navegar até o diretório
cd Webconsig_v2

# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual (Windows)
venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt
```

### 3. Configurar variáveis de ambiente

Copie o arquivo `.env.example` para `.env` e configure:

```bash
copy .env.example .env
```

Edite o arquivo `.env` com suas configurações:

```env
# Modo de execução
DEBUG=True

# Chave secreta (gere uma nova para produção!)
SECRET_KEY=sua-chave-secreta-aqui

# Banco de dados
DB_ENGINE=mssql            # mssql, postgresql, mysql, sqlite
DB_HOST=localhost
DB_PORT=1433
DB_NAME=webconsig
DB_USERNAME=sa
DB_PASSWORD=sua-senha
ODBC_DRIVER=ODBC Driver 17 for SQL Server
```

### 4. Inicializar o banco de dados

```bash
# Criar tabelas e dados iniciais
python seeds.py
```

### 5. Executar a aplicação

```bash
python run.py
```

Acesse: http://localhost:5000

## 👤 Credenciais Padrão

- **Usuário:** admin
- **Senha:** admin123

⚠️ **IMPORTANTE:** Altere a senha após o primeiro acesso!

## 📁 Estrutura do Projeto

```
Webconsig_v2/
├── apps/
│   ├── __init__.py         # App factory
│   ├── config.py           # Configurações
│   ├── messages.py         # Mensagens pt-BR
│   ├── authentication/     # Blueprint de autenticação
│   │   ├── __init__.py
│   │   ├── forms.py
│   │   ├── models.py
│   │   ├── routes.py
│   │   └── util.py
│   ├── home/               # Blueprint principal
│   │   ├── __init__.py
│   │   └── routes.py
│   └── settings/           # Blueprint de configurações
│       ├── __init__.py
│       ├── forms.py
│       ├── models.py
│       ├── routes.py
│       └── utils.py
├── templates/
│   ├── accounts/           # Templates de autenticação
│   ├── errors/             # Páginas de erro
│   ├── home/               # Templates principais
│   ├── includes/           # Componentes reutilizáveis
│   ├── layouts/            # Layouts base
│   └── settings/           # Templates de configuração
├── static/
│   └── assets/
│       ├── css/            # Estilos
│       ├── js/             # Scripts
│       └── img/            # Imagens
├── .env                    # Variáveis de ambiente
├── .env.example            # Exemplo de configuração
├── .gitignore
├── requirements.txt
├── run.py                  # Ponto de entrada
├── seeds.py                # Script de povoamento
└── README.md
```

## 🔧 Configuração do SQL Server

### Criar o banco de dados

```sql
CREATE DATABASE webconsig;
GO
```

### Verificar o ODBC Driver instalado

```powershell
# Listar drivers ODBC instalados
Get-OdbcDriver | Where-Object {$_.Name -like "*SQL Server*"}
```

### Instalar o ODBC Driver (se necessário)

Baixe de: https://docs.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server

## 🎨 Personalização

### Configurações do Sistema

Acesse: **Menu > Configurações** (como administrador)

Categorias disponíveis:
- **Sistema** - Nome, versão, descrição
- **Empresa** - Dados da empresa
- **Desenvolvedor** - Créditos
- **Aparência** - Cores e logos
- **Localização** - Idioma, fuso horário
- **Segurança** - Políticas de senha

### Adicionar novos módulos

1. Crie um blueprint em `apps/seu_modulo/`
2. Registre em `apps/__init__.py`
3. Adicione ao menu em `templates/includes/sidebar.html`

## 🔐 Segurança

- Senhas hasheadas com bcrypt
- Proteção CSRF em todos os formulários
- Sessões seguras com Flask-Login
- Sanitização de inputs

## 📦 Dependências Principais

| Pacote | Versão | Descrição |
|--------|--------|-----------|
| Flask | 3.0.0 | Framework web |
| SQLAlchemy | 2.0.23 | ORM |
| Flask-Login | 0.6.3 | Autenticação |
| pyodbc | 5.0.1 | Driver SQL Server |
| bcrypt | 4.1.1 | Hash de senhas |

## 🐛 Solução de Problemas

### Erro de conexão com SQL Server

1. Verifique se o SQL Server está rodando
2. Confirme o ODBC Driver instalado
3. Teste a conexão no `.env`

### Erro de encoding

Certifique-se que os arquivos estão em UTF-8.

## 🤝 Contribuição e Fluxo de PRs

Siga o guia em `CONTRIBUTING.md` para manter uma única linha de desenvolvimento (`main`) e evitar branches paralelos longos. Resumo:
- Use branches curtas `feature/*` ou `fix/*`
- Abra PRs pequenos com base em `main`
- Resolva conflitos localmente antes de abrir o PR
- Após o merge, apague a branch remota e aplique tags de versão quando necessário

Comandos úteis com GitHub CLI estão documentados no `CONTRIBUTING.md`.

### Migrações de banco

```bash
flask db init      # Primeira vez
flask db migrate   # Gerar migração
flask db upgrade   # Aplicar migração
```

## 🧪 Testes Automatizados

O projeto inclui uma suite de testes automatizados usando pytest. Isso elimina a necessidade de testes manuais com confirmações repetitivas.

### Executar testes

```bash
# Executar todos os testes
python run_tests.py

# Modo verbose (detalhado)
python run_tests.py -v

# Com relatório de cobertura de código
python run_tests.py --cov

# Apenas testes específicos (ex: autenticação)
python run_tests.py -k auth

# Parar no primeiro erro
python run_tests.py -x
```

### Usando pytest diretamente

```bash
# Todos os testes
pytest tests/ -v

# Com cobertura
pytest tests/ -v --cov=apps --cov-report=term-missing

# Testes específicos
pytest tests/test_authentication.py -v
pytest tests/test_routes.py -v
```

### Estrutura de testes

```
tests/
├── __init__.py
├── conftest.py              # Fixtures e configurações
├── test_authentication.py   # Testes de login/logout/registro
└── test_routes.py           # Testes de rotas
```

## 📄 Licença

MIT License - Livre para uso comercial e pessoal.

## 👨‍💻 Desenvolvimento

Para contribuir:

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

---

Desenvolvido com ❤️ em Python
