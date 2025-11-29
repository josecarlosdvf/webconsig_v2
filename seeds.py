# -*- coding: utf-8 -*-
"""
Script de Seeds - Povoamento inicial do banco de dados
======================================================

Este script cria:
- Configurações padrão do sistema
- Usuário administrador padrão

Uso:
    python seeds.py

Ou através do Flask CLI:
    flask seed
"""

import os
import sys

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from apps import create_app, db
from apps.config import config_dict
from apps.authentication.models import Users
from apps.settings.models import SystemSettings, DEFAULT_SETTINGS


def create_default_settings():
    """Cria as configurações padrão do sistema."""
    print("\n[1/2] Criando configurações padrão do sistema...")
    
    created = 0
    updated = 0
    
    for setting_data in DEFAULT_SETTINGS:
        key = setting_data['key']
        existing = SystemSettings.query.filter_by(key=key).first()
        
        if not existing:
            setting = SystemSettings(
                key=key,
                value=setting_data['value'],
                description=setting_data['description'],
                category=setting_data['category'],
                value_type=setting_data.get('value_type', 'string'),
                is_public=setting_data.get('is_public', False)
            )
            db.session.add(setting)
            created += 1
            print(f"  ✓ Criada: {key}")
        else:
            # Atualiza descrição e categoria se necessário
            if existing.description != setting_data['description']:
                existing.description = setting_data['description']
                updated += 1
            if existing.category != setting_data['category']:
                existing.category = setting_data['category']
                updated += 1
    
    db.session.commit()
    print(f"\n  Configurações: {created} criadas, {updated} atualizadas")


def create_admin_user():
    """Cria o usuário administrador padrão."""
    print("\n[2/2] Criando usuário administrador...")
    
    admin_username = os.getenv('ADMIN_USERNAME', 'admin')
    admin_email = os.getenv('ADMIN_EMAIL', 'admin@admin.com')
    admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
    
    # Verifica se já existe um admin
    existing_admin = Users.query.filter(
        (Users.username == admin_username) | (Users.email == admin_email)
    ).first()
    
    if existing_admin:
        print(f"  → Usuário administrador já existe: {existing_admin.username}")
        return existing_admin
    
    # Cria o novo admin
    admin = Users(
        username=admin_username,
        email=admin_email,
        first_name='Administrador',
        last_name='Sistema',
        role='admin',
        status='active'
    )
    admin.set_password(admin_password)
    
    db.session.add(admin)
    db.session.commit()
    
    print(f"  ✓ Usuário administrador criado!")
    print(f"    Usuário: {admin_username}")
    print(f"    E-mail: {admin_email}")
    print(f"    Senha: {admin_password}")
    print()
    print("  ⚠️  IMPORTANTE: Altere a senha após o primeiro acesso!")
    
    return admin


def run_seeds():
    """Executa todos os seeds."""
    print("\n" + "=" * 50)
    print("  SEEDS - Povoamento do Banco de Dados")
    print("=" * 50)
    
    # Cria as tabelas se não existirem
    print("\n  Verificando estrutura do banco de dados...")
    db.create_all()
    print("  ✓ Estrutura verificada/criada")
    
    # Executa os seeds
    create_default_settings()
    create_admin_user()
    
    print("\n" + "=" * 50)
    print("  ✓ Seeds executados com sucesso!")
    print("=" * 50)
    print()


if __name__ == '__main__':
    # Determina o ambiente
    DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 'yes')
    config_mode = 'Debug' if DEBUG else 'Production'
    
    try:
        app_config = config_dict[config_mode.capitalize()]
    except KeyError:
        app_config = config_dict['Debug']
    
    # Cria a aplicação e contexto
    app = create_app(app_config)
    
    with app.app_context():
        run_seeds()
