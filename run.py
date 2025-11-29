# -*- coding: utf-8 -*-
"""
Ponto de entrada da aplicação Flask
===================================

Execute este arquivo para iniciar o servidor de desenvolvimento:
    python run.py

Para produção, use um servidor WSGI como Gunicorn:
    gunicorn -w 4 -b 0.0.0.0:5000 run:app
"""

import os
from apps import create_app, db
from apps.config import config_dict

# Determina o ambiente de execução
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 'yes')
get_config_mode = 'Debug' if DEBUG else 'Production'

try:
    # Obtém a configuração apropriada
    app_config = config_dict[get_config_mode.capitalize()]
except KeyError:
    print(f"Modo de configuração '{get_config_mode}' não encontrado. Usando 'Debug'.")
    app_config = config_dict['Debug']

# Cria a aplicação Flask
app = create_app(app_config)

if __name__ == '__main__':
    # Informações de inicialização
    print("=" * 50)
    print("  Sistema Web - Flask Application")
    print("=" * 50)
    print(f"  Modo: {'Desenvolvimento' if DEBUG else 'Produção'}")
    print(f"  Debug: {DEBUG}")
    print(f"  Database: {app.config.get('SQLALCHEMY_DATABASE_URI', 'N/A')[:50]}...")
    print("=" * 50)
    print()
    
    # Inicia o servidor de desenvolvimento
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=DEBUG,
        use_reloader=DEBUG
    )
