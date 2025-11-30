# -*- encoding: utf-8 -*-
"""
Módulo de Gestão de Clientes
"""

from flask import Blueprint

blueprint = Blueprint(
    'clientes_blueprint',
    __name__,
    url_prefix='/clientes'
)
