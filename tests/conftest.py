# -*- coding: utf-8 -*-
"""
Configurações e fixtures para testes automatizados com pytest.

Este módulo fornece fixtures compartilhadas para todos os testes:
- Aplicação Flask configurada para testes
- Cliente de teste com sessão
- Banco de dados de teste limpo
- Usuário de teste autenticado

Uso:
    Execute os testes com: pytest tests/ -v
    Com cobertura: pytest tests/ -v --cov=apps
"""

import os
import sys
import pytest
import tempfile

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configura ambiente de teste ANTES de importar a aplicação
os.environ['DEBUG'] = 'True'
os.environ['TESTING'] = 'True'

from apps import create_app, db
from apps.config import config_dict
from apps.authentication.models import Users
# Import all models to ensure they are registered with SQLAlchemy
from apps.clientes.models import (
    Cliente, Telefone, Endereco, Email,
    Identidade, DadosBancarios, Matricula, DataNascimento
)


class TestConfig:
    """Configuração específica para testes"""
    TESTING = True
    DEBUG = True
    WTF_CSRF_ENABLED = False  # Desabilita CSRF para testes
    SECRET_KEY = 'test-secret-key-for-testing-only'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOGIN_DISABLED = False
    SERVER_NAME = 'localhost.localdomain'


@pytest.fixture(scope='session')
def app():
    """
    Cria instância da aplicação Flask configurada para testes.
    Usa escopo 'session' para reutilizar entre todos os testes.
    """
    # Usa configuração de Debug como base (ou outra via variável de ambiente)
    config_name = os.environ.get('FLASK_CONFIG', 'Debug')
    config = config_dict.get(config_name, config_dict['Debug'])
    
    # Sobrescreve configurações para teste
    config.TESTING = True
    config.WTF_CSRF_ENABLED = False
    config.SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    config.SERVER_NAME = 'localhost.localdomain'
    config.SECRET_KEY = 'test-secret-key'
    
    # Cria aplicação
    flask_app = create_app(config)
    flask_app.config['TESTING'] = True
    flask_app.config['WTF_CSRF_ENABLED'] = False
    
    # Cria contexto de aplicação
    with flask_app.app_context():
        yield flask_app


@pytest.fixture(scope='function')
def client(app):
    """
    Cliente de teste Flask.
    Novo cliente para cada função de teste.
    """
    return app.test_client()


@pytest.fixture(scope='function')
def init_database(app):
    """
    Inicializa banco de dados limpo para cada teste.
    Cria todas as tabelas e limpa após o teste.
    """
    with app.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def test_user(app, init_database):
    """
    Cria um usuário de teste para autenticação.
    Retorna o objeto usuário criado.
    """
    with app.app_context():
        user = Users(
            username='testuser',
            email='test@example.com',
            password='testpassword123',
            first_name='Test',
            last_name='User',
            is_active=True
        )
        db.session.add(user)
        db.session.commit()
        
        # Busca novamente para garantir que está vinculado à sessão
        user = Users.query.filter_by(username='testuser').first()
        yield user


@pytest.fixture(scope='function')
def admin_user(app, init_database):
    """
    Cria ou obtém um usuário administrador de teste.
    """
    with app.app_context():
        try:
            # Tenta obter o admin existente primeiro
            admin = Users.query.filter_by(username='admin').first()
            if not admin:
                admin = Users(
                    username='admin',
                    email='admin@example.com',
                    password='admin123',
                    first_name='Admin',
                    last_name='User',
                    is_active=True,
                    is_admin=True
                )
                db.session.add(admin)
                db.session.commit()
                admin = Users.query.filter_by(username='admin').first()
        except Exception:
            db.session.rollback()
            # Em caso de erro, tenta obter novamente
            admin = Users.query.filter_by(username='admin').first()
        
        yield admin


@pytest.fixture(scope='function')
def authenticated_client(client, test_user):
    """
    Cliente de teste já autenticado com usuário de teste.
    """
    with client.session_transaction() as session:
        session['_user_id'] = test_user.id
        session['_fresh'] = True
    
    yield client


@pytest.fixture(scope='function')
def admin_client(client, admin_user):
    """
    Cliente de teste autenticado como administrador.
    """
    with client.session_transaction() as session:
        session['_user_id'] = admin_user.id
        session['_fresh'] = True
    
    yield client


def login_user(client, username='testuser', password='testpassword123'):
    """
    Helper para fazer login durante os testes.
    
    Args:
        client: Cliente de teste Flask
        username: Nome de usuário
        password: Senha
    
    Returns:
        Response do login
    """
    return client.post('/login', data={
        'username': username,
        'password': password
    }, follow_redirects=True)


def logout_user(client):
    """
    Helper para fazer logout durante os testes.
    """
    return client.get('/logout', follow_redirects=True)
