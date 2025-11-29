# -*- encoding: utf-8 -*-
"""
Database Seeder
Popula o banco de dados com dados iniciais
"""

import os
from datetime import datetime
from apps import db
# Lazy imports para evitar importação circular
# Users e SystemSettings são importados dentro das funções que os utilizam
from apps.logs import log_info, log_warning, log_error


def check_database_exists(app):
    """Verifica se o banco de dados existe"""
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    
    # Para SQLite, verifica se o arquivo existe
    if 'sqlite' in db_uri:
        # Extrai o caminho do arquivo do URI
        # formato: sqlite:///caminho/para/arquivo.db
        db_path = db_uri.replace('sqlite:///', '')
        return os.path.exists(db_path)
    
    # Para outros bancos, tenta uma query simples
    try:
        with app.app_context():
            db.session.execute(db.text('SELECT 1'))
        return True
    except Exception:
        return False


def seed_system_settings():
    """Popula as configurações padrão do sistema"""
    # Lazy import para evitar importação circular
    from apps.settings.models import SystemSettings, DEFAULT_SETTINGS
    
    created_count = 0
    
    for setting_data in DEFAULT_SETTINGS:
        # Verifica se a configuração já existe
        existing = SystemSettings.query.filter_by(key=setting_data['key']).first()
        
        if not existing:
            setting = SystemSettings(
                key=setting_data['key'],
                value=setting_data.get('value'),
                value_type=setting_data.get('value_type', 'string'),
                category=setting_data.get('category', 'geral'),
                label=setting_data.get('label', setting_data['key']),
                description=setting_data.get('description'),
                is_public=setting_data.get('is_public', False),
                is_editable=setting_data.get('is_editable', True),
                order=setting_data.get('order', 0)
            )
            db.session.add(setting)
            created_count += 1
    
    if created_count > 0:
        db.session.commit()
        log_info(f'Seed: {created_count} configurações do sistema criadas')
    
    return created_count


def seed_admin_user():
    """Cria o usuário administrador padrão"""
    # Lazy import para evitar importação circular
    from apps.authentication.models import Users
    
    # Verifica se já existe algum admin
    admin = Users.query.filter_by(is_admin=True).first()
    
    if not admin:
        admin = Users(
            username='admin',
            email='admin@sistema.local',
            password='admin123',  # Será hasheado automaticamente no __init__
            first_name='Administrador',
            last_name='do Sistema',
            is_active=True,
            is_admin=True,
            role_id=1
        )
        
        if admin.save():
            log_info('Seed: Usuário administrador criado (admin/admin123)')
            return True
        else:
            log_error('Seed: Falha ao criar usuário administrador')
            return False
    
    return False


def seed_demo_users():
    """Cria usuários de demonstração (opcional)"""
    # Lazy import para evitar importação circular
    from apps.authentication.models import Users
    
    demo_users = [
        {
            'username': 'gerente',
            'email': 'gerente@sistema.local',
            'password': 'gerente123',
            'first_name': 'Gerente',
            'last_name': 'Demo',
            'is_active': True,
            'is_admin': False,
            'role_id': 2
        },
        {
            'username': 'usuario',
            'email': 'usuario@sistema.local',
            'password': 'usuario123',
            'first_name': 'Usuário',
            'last_name': 'Demo',
            'is_active': True,
            'is_admin': False,
            'role_id': 3
        }
    ]
    
    created_count = 0
    
    for user_data in demo_users:
        existing = Users.query.filter_by(username=user_data['username']).first()
        
        if not existing:
            user = Users(**user_data)
            if user.save():
                created_count += 1
    
    if created_count > 0:
        log_info(f'Seed: {created_count} usuários de demonstração criados')
    
    return created_count


def run_all_seeds(app, include_demo=True):
    """Executa todos os seeds"""
    with app.app_context():
        log_info('='*50)
        log_info('Iniciando processo de seed do banco de dados')
        log_info('='*50)
        
        try:
            # Cria todas as tabelas
            db.create_all()
            log_info('Tabelas do banco de dados criadas/verificadas')
            
            # Seed das configurações do sistema
            settings_count = seed_system_settings()
            
            # Seed do usuário admin
            admin_created = seed_admin_user()
            
            # Seed de usuários demo (opcional)
            if include_demo:
                demo_count = seed_demo_users()
            
            log_info('='*50)
            log_info('Processo de seed concluído com sucesso')
            log_info('='*50)
            
            return True
            
        except Exception as e:
            log_error(f'Erro durante o seed: {str(e)}')
            db.session.rollback()
            return False


def init_database(app):
    """
    Inicializa o banco de dados.
    Chamado automaticamente ao iniciar a aplicação.
    """
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    
    # Para SQLite, verifica se o arquivo existe
    if 'sqlite' in db_uri:
        db_path = db_uri.replace('sqlite:///', '')
        
        # Se o banco não existe, cria e faz seed
        if not os.path.exists(db_path):
            log_info(f'Banco de dados não encontrado. Criando: {db_path}')
            return run_all_seeds(app, include_demo=True)
        else:
            # Banco existe, apenas garante que as tabelas existem
            with app.app_context():
                db.create_all()
                
                # Verifica se precisa fazer seed (banco vazio)
                try:
                    # Lazy imports para evitar importação circular
                    from apps.settings.models import SystemSettings
                    from apps.authentication.models import Users
                    
                    settings_count = SystemSettings.query.count()
                    users_count = Users.query.count()
                    
                    if settings_count == 0 or users_count == 0:
                        log_info('Banco existe mas está vazio. Executando seed...')
                        return run_all_seeds(app, include_demo=True)
                except Exception as e:
                    log_warning(f'Erro ao verificar banco: {e}. Tentando criar tabelas...')
                    db.create_all()
                    return run_all_seeds(app, include_demo=True)
    else:
        # Para outros bancos (SQL Server, PostgreSQL, etc.)
        with app.app_context():
            try:
                db.create_all()
                
                # Lazy imports para evitar importação circular
                from apps.settings.models import SystemSettings
                from apps.authentication.models import Users
                
                # Verifica se precisa seed
                settings_count = SystemSettings.query.count()
                users_count = Users.query.count()
                
                if settings_count == 0 or users_count == 0:
                    log_info('Executando seed inicial...')
                    return run_all_seeds(app, include_demo=True)
                    
            except Exception as e:
                log_error(f'Erro ao inicializar banco: {e}')
                return False
    
    return True
