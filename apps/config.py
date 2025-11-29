# -*- encoding: utf-8 -*-
"""
Configurações do Sistema
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()


class Config(object):
    """Configurações base"""
    
    BASE_DIR = Path(__file__).resolve().parent
    
    # Chave secreta para sessões
    SECRET_KEY = os.getenv('SECRET_KEY', 'chave-secreta-padrao-mude-em-producao')
    
    # ===========================================
    # Roles e Status de Usuário
    # ===========================================
    USERS_ROLES = {
        'ADMIN': 1,
        'MANAGER': 2,
        'USER': 3
    }
    
    USERS_STATUS = {
        'ACTIVE': 1,
        'INACTIVE': 2,
        'SUSPENDED': 3
    }
    
    # ===========================================
    # Configurações de Localização
    # ===========================================
    BABEL_DEFAULT_LOCALE = 'pt_BR'
    BABEL_DEFAULT_TIMEZONE = 'America/Sao_Paulo'
    
    # ===========================================
    # Celery (Opcional)
    # ===========================================
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379')
    
    # ===========================================
    # OAuth (Opcional)
    # ===========================================
    SOCIAL_AUTH_GITHUB = False
    SOCIAL_AUTH_GOOGLE = False
    
    GITHUB_ID = os.getenv('GITHUB_ID', None)
    GITHUB_SECRET = os.getenv('GITHUB_SECRET', None)
    
    if GITHUB_ID and GITHUB_SECRET:
        SOCIAL_AUTH_GITHUB = True
    
    GOOGLE_ID = os.getenv('GOOGLE_ID', None)
    GOOGLE_SECRET = os.getenv('GOOGLE_SECRET', None)
    
    if GOOGLE_ID and GOOGLE_SECRET:
        SOCIAL_AUTH_GOOGLE = True
    
    # ===========================================
    # Configurações de Sessão (base - sobrescrita em Production)
    # ===========================================
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False  # Importante: False para desenvolvimento
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = False
    REMEMBER_COOKIE_DURATION = 86400  # 24 horas
    
    # ===========================================
    # Configurações de SQLAlchemy
    # ===========================================
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # ===========================================
    # Configuração do Banco de Dados
    # ===========================================
    DB_ENGINE = os.getenv('DB_ENGINE', 'sqlite')
    DB_USERNAME = os.getenv('DB_USERNAME', None)
    DB_PASS = os.getenv('DB_PASS', None)
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', None)
    DB_NAME = os.getenv('DB_NAME', None)
    DB_DRIVER = os.getenv('DB_DRIVER', 'ODBC Driver 17 for SQL Server')
    DB_TRUST_CERTIFICATE = os.getenv('DB_TRUST_CERTIFICATE', 'yes')
    DB_ENCRYPT = os.getenv('DB_ENCRYPT', 'no')
    
    # Flag para usar SQLite como fallback
    USE_SQLITE = True
    SQLALCHEMY_DATABASE_URI = None
    
    if DB_ENGINE == 'sqlite':
        # SQLite para desenvolvimento
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + str(BASE_DIR / 'db.sqlite3')
        USE_SQLITE = True
        
    elif DB_ENGINE == 'mssql+pyodbc' and DB_NAME and DB_USERNAME:
        # SQL Server com pyodbc
        try:
            import urllib.parse
            params = urllib.parse.quote_plus(
                f"DRIVER={{{DB_DRIVER}}};"
                f"SERVER={DB_HOST},{DB_PORT or 1433};"
                f"DATABASE={DB_NAME};"
                f"UID={DB_USERNAME};"
                f"PWD={DB_PASS};"
                f"TrustServerCertificate={DB_TRUST_CERTIFICATE};"
                f"Encrypt={DB_ENCRYPT};"
            )
            SQLALCHEMY_DATABASE_URI = f"mssql+pyodbc:///?odbc_connect={params}"
            USE_SQLITE = False
        except Exception as e:
            print(f'> Erro ao configurar SQL Server: {e}')
            print('> Usando SQLite como fallback')
            SQLALCHEMY_DATABASE_URI = 'sqlite:///' + str(BASE_DIR / 'db.sqlite3')
            USE_SQLITE = True
            
    elif DB_ENGINE in ('postgresql', 'mysql+pymysql') and DB_NAME and DB_USERNAME:
        # PostgreSQL ou MySQL
        try:
            port = DB_PORT or ('5432' if DB_ENGINE == 'postgresql' else '3306')
            SQLALCHEMY_DATABASE_URI = f'{DB_ENGINE}://{DB_USERNAME}:{DB_PASS}@{DB_HOST}:{port}/{DB_NAME}'
            USE_SQLITE = False
        except Exception as e:
            print(f'> Erro ao configurar {DB_ENGINE}: {e}')
            print('> Usando SQLite como fallback')
            SQLALCHEMY_DATABASE_URI = 'sqlite:///' + str(BASE_DIR / 'db.sqlite3')
            USE_SQLITE = True
    else:
        # Fallback para SQLite
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + str(BASE_DIR / 'db.sqlite3')
        USE_SQLITE = True
    
    # ===========================================
    # DataTables Dinâmicas
    # ===========================================
    DYNAMIC_DATATB = {
        # "produtos": "apps.models.Produto"
    }
    
    # ===========================================
    # CDN e Assets
    # ===========================================
    CDN_DOMAIN = os.getenv('CDN_DOMAIN', None)
    CDN_HTTPS = os.getenv('CDN_HTTPS', 'True').lower() == 'true'
    ASSETS_ROOT = os.getenv('ASSETS_ROOT', '/static/assets')
    
    # ===========================================
    # Upload de Arquivos
    # ===========================================
    UPLOAD_FOLDER = str(BASE_DIR.parent / 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'xls', 'xlsx'}
    
    # ===========================================
    # Configurações de Logs
    # ===========================================
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')
    LOG_DIR = str(BASE_DIR.parent / 'logs')
    LOG_TO_FILE = os.getenv('LOG_TO_FILE', 'False').lower() == 'true'
    LOG_TO_CONSOLE = os.getenv('LOG_TO_CONSOLE', 'True').lower() == 'true'
    
    # ===========================================
    # Configurações de Pagamentos (exemplo)
    # ===========================================
    CURRENCY = {
        'BRL': 'Real Brasileiro',
        'USD': 'Dólar Americano',
        'EUR': 'Euro'
    }
    
    PAYMENT_TYPE = {
        'pix': 'PIX',
        'boleto': 'Boleto Bancário',
        'cartao': 'Cartão de Crédito',
        'transferencia': 'Transferência Bancária'
    }
    
    STATE = {
        'pendente': 'Pendente',
        'processando': 'Processando',
        'concluido': 'Concluído',
        'cancelado': 'Cancelado'
    }


class ProductionConfig(Config):
    """Configurações de Produção"""
    DEBUG = False
    
    # Log menos verboso em produção
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'WARNING')
    LOG_TO_FILE = os.getenv('LOG_TO_FILE', 'True').lower() == 'true'
    LOG_TO_CONSOLE = os.getenv('LOG_TO_CONSOLE', 'False').lower() == 'true'
    
    # Segurança de cookies
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 3600
    REMEMBER_COOKIE_SECURE = True
    
    # CSRF
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600


class DebugConfig(Config):
    """Configurações de Desenvolvimento"""
    DEBUG = True
    
    # Log verboso em desenvolvimento
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')
    LOG_TO_FILE = os.getenv('LOG_TO_FILE', 'False').lower() == 'true'
    LOG_TO_CONSOLE = os.getenv('LOG_TO_CONSOLE', 'True').lower() == 'true'
    
    # Menos restritivo para desenvolvimento
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 86400  # 24 horas


# Dicionário de configurações
config_dict = {
    'Production': ProductionConfig,
    'Debug': DebugConfig
}
