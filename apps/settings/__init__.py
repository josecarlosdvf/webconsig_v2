# -*- encoding: utf-8 -*-
"""
Blueprint de Configurações do Sistema
"""

from flask import Blueprint

blueprint = Blueprint(
    'settings_blueprint',
    __name__,
    url_prefix='/admin/settings'
)
