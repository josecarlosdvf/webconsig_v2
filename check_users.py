#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para verificar usuários no banco"""

from apps import create_app
from apps.authentication.models import Users

app = create_app()

with app.app_context():
    users = Users.query.all()
    print("=" * 50)
    print("USUARIOS CADASTRADOS NO BANCO")
    print("=" * 50)
    for u in users:
        print(f"Username: {u.username}")
        print(f"Email: {u.email}")
        print(f"Active: {u.is_active}")
        print(f"Admin: {u.is_admin}")
        print("-" * 30)
    
    if not users:
        print("NENHUM USUARIO ENCONTRADO!")
    
    # Testa login
    print("\n=== TESTE DE LOGIN ===")
    admin = Users.query.filter_by(username='admin').first()
    if admin:
        print(f"Usuario 'admin' encontrado: {admin.email}")
        # Testa senha
        if admin.check_password('admin123'):
            print("Senha 'admin123' CORRETA!")
        else:
            print("Senha 'admin123' INCORRETA!")
    else:
        print("Usuario 'admin' NAO encontrado!")
