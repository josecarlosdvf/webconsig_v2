# -*- encoding: utf-8 -*-
"""
Módulo Admin - Administração de Usuários, Grupos e Permissões
"""

from flask import Blueprint

blueprint = Blueprint(
    'admin_blueprint',
    __name__,
    url_prefix='/admin'
)
