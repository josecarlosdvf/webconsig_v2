# -*- encoding: utf-8 -*-
"""
Factory de Aplicação Flask
"""

import os
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from importlib import import_module

# Extensões
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()


def register_extensions(app):
    """Registra extensões do Flask"""
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # Configurações do Login Manager
    login_manager.login_view = 'authentication_blueprint.login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'warning'


def register_blueprints(app):
    """Registra blueprints da aplicação"""
    blueprints = (
        'authentication',
        'home',
        'settings',
        'admin',
        'hr',
        'files',
        'messaging',
        'clientes',
        'propostas',
    )
    
    for module_name in blueprints:
        module = import_module(f'apps.{module_name}.routes')
        app.register_blueprint(module.blueprint)
    
    # Registra blueprint de API
    from apps.api import blueprint as api_blueprint
    app.register_blueprint(api_blueprint)


def configure_database(app):
    """Configura banco de dados e executa seed se necessário"""
    from apps.database import init_database
    
    # Inicializa o banco de dados (cria tabelas e faz seed se necessário)
    init_database(app)


def configure_session_validation(app):
    """Configura validação de sessão única"""
    from flask import session, redirect, url_for, request
    from flask_login import current_user, logout_user
    
    @app.before_request
    def validate_session():
        """Verifica se a sessão atual ainda é válida"""
        # TEMPORARIAMENTE DESABILITADO PARA DEBUG
        # TODO: Reativar após resolver problema de sessão
        return
        
        # Rotas que não precisam de validação de sessão
        exempt_endpoints = [
            'authentication_blueprint.login',
            'authentication_blueprint.register',
            'authentication_blueprint.logout',
            'authentication_blueprint.session_expired',
            'authentication_blueprint.check_session',
            'authentication_blueprint.debug_session',
            'static',
            None
        ]
        
        # Ignora rotas de API e estáticas
        if request.endpoint in exempt_endpoints:
            return
        
        # Ignora se o endpoint começa com '_'
        if request.endpoint and request.endpoint.startswith('_'):
            return
        
        # Se o usuário está autenticado, valida o token da sessão
        if current_user.is_authenticated:
            session_token = session.get('session_token')
            
            # Se o usuário não tem token no banco (migração/seed), gera um novo
            if current_user.session_token is None:
                new_token = current_user.generate_session_token()
                session['session_token'] = new_token
                return  # Continua normalmente
            
            # Se não tem token na sessão, mas tem no banco, invalida
            if not session_token:
                logout_user()
                return redirect(url_for('authentication_blueprint.session_expired'))
            
            # Se o token da sessão não corresponde ao do banco, invalida
            if not current_user.verify_session_token(session_token):
                session.pop('session_token', None)
                logout_user()
                return redirect(url_for('authentication_blueprint.session_expired'))


def register_context_processors(app):
    """Registra context processors globais"""
    
    @app.context_processor
    def inject_settings():
        """Injeta configurações do sistema em todos os templates"""
        from apps.settings.utils import get_system_settings
        settings = get_system_settings()
        return {
            'system': settings,
            'system_settings': settings,  # Alias para compatibilidade
        }
    
    @app.context_processor
    def inject_assets():
        """Injeta caminho dos assets"""
        return {'ASSETS_ROOT': app.config.get('ASSETS_ROOT', '/static/assets')}
    
    @app.context_processor
    def inject_permission_context():
        """Injeta contexto de permissões em templates"""
        from apps.authentication.decorators import PermissionContext
        from flask_login import current_user
        
        perm_context = PermissionContext(current_user)
        
        def user_has_permission(permission_code):
            """Função helper para verificar permissão no template"""
            return perm_context.can(permission_code)
        
        return {
            'perm': perm_context,
            'user_has_permission': user_has_permission
        }


def create_app(config):
    """Cria e configura a aplicação Flask"""
    
    # Diretórios base
    templates_dir = os.path.dirname(config.BASE_DIR)
    static_dir = os.path.dirname(config.BASE_DIR)
    
    TEMPLATES_FOLDER = os.path.join(templates_dir, 'templates')
    STATIC_FOLDER = os.path.join(static_dir, 'static')
    
    # Cria aplicação
    app = Flask(
        __name__,
        static_url_path='/static',
        template_folder=TEMPLATES_FOLDER,
        static_folder=STATIC_FOLDER
    )
    
    # Carrega configurações
    app.config.from_object(config)
    
    # Registra extensões
    register_extensions(app)
    
    # Configura sistema de logs
    from apps.logs import setup_logging, register_error_handlers, log_info
    setup_logging(app)
    
    # Registra blueprints
    register_blueprints(app)
    
    # Configura banco de dados
    configure_database(app)
    
    # Configura validação de sessão única
    configure_session_validation(app)
    
    # Registra context processors
    register_context_processors(app)
    
    # Inicializa suporte HTMX
    from apps.htmx import init_htmx
    init_htmx(app)
    
    # Registra rota para servir arquivos de upload (avatars, etc.)
    from flask import send_from_directory
    
    @app.route('/uploads/<path:filename>')
    def serve_uploads(filename):
        """Serve arquivos da pasta de uploads"""
        upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
        return send_from_directory(upload_folder, filename)
    
    # Registra error handlers com logging
    register_error_handlers(app)
    
    # Log de inicialização
    log_info(f'Aplicação inicializada', extra={
        'templates_folder': TEMPLATES_FOLDER,
        'static_folder': STATIC_FOLDER,
        'database': app.config.get('SQLALCHEMY_DATABASE_URI', 'N/A')[:50] + '...'
    })
    
    return app
