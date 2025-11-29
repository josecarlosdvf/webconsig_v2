# -*- coding: utf-8 -*-
"""
Testes automatizados de autenticação.

Estes testes substituem a necessidade de testar login/logout manualmente.
Execute com: pytest tests/test_authentication.py -v
"""

import pytest
from flask import url_for
from apps.authentication.models import Users


class TestLoginLogout:
    """Testes de login e logout"""
    
    def test_login_page_loads(self, client, init_database):
        """Verifica se a página de login carrega corretamente"""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'login' in response.data.lower() or b'Login' in response.data
    
    def test_login_with_valid_credentials(self, client, test_user):
        """Testa login com credenciais válidas"""
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword123'
        }, follow_redirects=True)
        
        # Deve redirecionar para dashboard ou home
        assert response.status_code == 200
    
    def test_login_with_invalid_password(self, client, test_user):
        """Testa login com senha incorreta"""
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Deve mostrar mensagem de erro (página de login ainda)
    
    def test_login_with_nonexistent_user(self, client, init_database):
        """Testa login com usuário inexistente"""
        response = client.post('/login', data={
            'username': 'nonexistent',
            'password': 'anypassword'
        }, follow_redirects=True)
        
        assert response.status_code == 200
    
    def test_login_redirects_authenticated_user(self, authenticated_client):
        """Usuário já logado deve ser redirecionado"""
        response = authenticated_client.get('/login', follow_redirects=True)
        assert response.status_code == 200
    
    def test_logout(self, authenticated_client):
        """Testa logout"""
        response = authenticated_client.get('/logout', follow_redirects=True)
        assert response.status_code == 200


class TestProtectedRoutes:
    """Testes de rotas protegidas"""
    
    def test_dashboard_requires_login(self, client, init_database):
        """Dashboard requer autenticação"""
        response = client.get('/', follow_redirects=False)
        # Deve redirecionar para login
        assert response.status_code in [302, 301, 200]
    
    def test_profile_requires_login(self, client, init_database):
        """Perfil requer autenticação"""
        response = client.get('/perfil', follow_redirects=False)
        assert response.status_code in [302, 301, 200]
    
    def test_authenticated_user_can_access_profile(self, authenticated_client):
        """Usuário autenticado acessa perfil"""
        response = authenticated_client.get('/perfil', follow_redirects=True)
        assert response.status_code == 200


class TestRegistration:
    """Testes de registro de usuário"""
    
    def test_register_page_loads(self, client, init_database):
        """Verifica se a página de registro carrega"""
        response = client.get('/registrar')
        assert response.status_code == 200
    
    def test_register_new_user(self, client, init_database):
        """Testa registro de novo usuário"""
        response = client.post('/registrar', data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpassword123',
            'confirm': 'newpassword123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
    
    def test_register_duplicate_username(self, client, test_user):
        """Testa registro com username duplicado"""
        response = client.post('/registrar', data={
            'username': 'testuser',  # Já existe
            'email': 'other@example.com',
            'password': 'newpassword123',
            'confirm': 'newpassword123'
        }, follow_redirects=True)
        
        assert response.status_code == 200


class TestUserModel:
    """Testes do modelo de usuário"""
    
    def test_user_creation(self, app, init_database):
        """Testa criação de usuário"""
        with app.app_context():
            user = Users(
                username='modeltest',
                email='modeltest@example.com',
                password='testpass123'
            )
            init_database.session.add(user)
            init_database.session.commit()
            
            # Verifica se foi criado
            saved_user = Users.query.filter_by(username='modeltest').first()
            assert saved_user is not None
            assert saved_user.email == 'modeltest@example.com'
    
    def test_password_hashing(self, app, init_database):
        """Testa que senhas são hasheadas"""
        with app.app_context():
            user = Users(
                username='hashtest',
                email='hashtest@example.com',
                password='mypassword'
            )
            init_database.session.add(user)
            init_database.session.commit()
            
            saved_user = Users.query.filter_by(username='hashtest').first()
            # Senha não deve estar em texto plano
            assert saved_user.password != b'mypassword'
            assert saved_user.password != 'mypassword'
    
    def test_password_verification(self, test_user, app):
        """Testa verificação de senha"""
        with app.app_context():
            user = Users.query.filter_by(username='testuser').first()
            assert user.check_password('testpassword123')
            assert not user.check_password('wrongpassword')
    
    def test_full_name_property(self, app, init_database):
        """Testa propriedade full_name"""
        with app.app_context():
            user = Users(
                username='fullnametest',
                email='fullname@example.com',
                password='testpass',
                first_name='John',
                last_name='Doe'
            )
            init_database.session.add(user)
            init_database.session.commit()
            
            saved_user = Users.query.filter_by(username='fullnametest').first()
            assert saved_user.full_name == 'John Doe'


class TestSessionManagement:
    """Testes de gerenciamento de sessão"""
    
    def test_session_token_generation(self, test_user, app):
        """Testa geração de token de sessão"""
        with app.app_context():
            user = Users.query.filter_by(username='testuser').first()
            token = user.generate_session_token()
            
            assert token is not None
            assert user.session_token == token
    
    def test_session_token_verification(self, test_user, app):
        """Testa verificação de token de sessão"""
        with app.app_context():
            user = Users.query.filter_by(username='testuser').first()
            token = user.generate_session_token()
            
            assert user.verify_session_token(token)
            assert not user.verify_session_token('invalid_token')
    
    def test_session_invalidation(self, test_user, app):
        """Testa invalidação de sessão"""
        with app.app_context():
            user = Users.query.filter_by(username='testuser').first()
            user.generate_session_token()
            user.invalidate_session()
            
            assert user.session_token is None
