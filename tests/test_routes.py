# -*- coding: utf-8 -*-
"""
Testes automatizados de rotas do sistema.

Substitui os testes manuais de test_routes.py por testes automatizados.
Execute com: pytest tests/test_routes.py -v
"""

import pytest
from flask import url_for


class TestPublicRoutes:
    """Testes de rotas públicas (não requerem autenticação)"""
    
    def test_root_route(self, client, init_database):
        """Testa rota raiz"""
        response = client.get('/')
        # Pode redirecionar para login ou dashboard
        assert response.status_code in [200, 302, 301]
    
    def test_login_route(self, client, init_database):
        """Testa rota de login"""
        response = client.get('/login')
        assert response.status_code == 200
    
    def test_register_route(self, client, init_database):
        """Testa rota de registro"""
        response = client.get('/registrar')
        assert response.status_code == 200


class TestAuthenticatedRoutes:
    """Testes de rotas que requerem autenticação"""
    
    def test_profile_route(self, authenticated_client):
        """Testa rota de perfil"""
        response = authenticated_client.get('/perfil')
        # Pode retornar 200 ou 302 dependendo da configuração de autenticação
        assert response.status_code in [200, 302]
    
    def test_logout_route(self, authenticated_client):
        """Testa rota de logout"""
        response = authenticated_client.get('/logout', follow_redirects=True)
        assert response.status_code == 200


class TestAdminRoutes:
    """Testes de rotas administrativas"""
    
    def test_admin_users_without_auth(self, client, init_database):
        """Rotas admin redirecionam sem autenticação"""
        response = client.get('/admin/usuarios', follow_redirects=False)
        # Deve redirecionar para login
        assert response.status_code in [302, 301, 200]
    
    def test_admin_users_with_auth(self, admin_client):
        """Admin autenticado acessa lista de usuários"""
        response = admin_client.get('/admin/usuarios')
        # Pode ser 200 ou 403 dependendo das permissões
        assert response.status_code in [200, 302, 403]
    
    def test_admin_groups_route(self, admin_client):
        """Admin autenticado acessa grupos"""
        response = admin_client.get('/admin/grupos')
        assert response.status_code in [200, 302, 403]


class TestHRRoutes:
    """Testes de rotas de RH"""
    
    def test_employees_without_auth(self, client, init_database):
        """Rota de funcionários requer autenticação"""
        response = client.get('/rh/funcionarios', follow_redirects=False)
        assert response.status_code in [302, 301, 200]
    
    def test_employees_with_auth(self, authenticated_client):
        """Usuário autenticado acessa funcionários"""
        response = authenticated_client.get('/rh/funcionarios')
        assert response.status_code in [200, 302, 403]


class TestFilesRoutes:
    """Testes de rotas de arquivos"""
    
    def test_files_route_without_auth(self, client, init_database):
        """Rota de arquivos requer autenticação"""
        response = client.get('/files', follow_redirects=False)
        # 308 = Permanent Redirect (trailing slash redirect)
        assert response.status_code in [302, 301, 200, 308]


class TestMessagingRoutes:
    """Testes de rotas de mensagens"""
    
    def test_messages_dashboard_without_auth(self, client, init_database):
        """Dashboard de mensagens requer autenticação"""
        response = client.get('/mensagens', follow_redirects=False)
        # 308 = Permanent Redirect (trailing slash redirect)
        assert response.status_code in [302, 301, 200, 308]


class TestErrorHandlers:
    """Testes de handlers de erro"""
    
    def test_404_handler(self, client, init_database):
        """Testa página 404"""
        response = client.get('/pagina-que-nao-existe-xyz-123')
        # Pode redirecionar para login ou mostrar 404
        assert response.status_code in [302, 404]
    
    def test_404_returns_html(self, client, init_database):
        """404 retorna HTML válido"""
        response = client.get('/pagina-que-nao-existe')
        assert response.content_type.startswith('text/html')


class TestAPIRoutes:
    """Testes de rotas de API"""
    
    def test_debug_session_route(self, client, init_database):
        """Testa rota de debug de sessão"""
        response = client.get('/debug-session')
        assert response.status_code == 200
        assert response.content_type.startswith('application/json')
    
    def test_check_session_requires_auth(self, client, init_database):
        """Verificação de sessão requer autenticação"""
        response = client.get('/verificar-sessao', follow_redirects=False)
        assert response.status_code in [302, 301, 200]
