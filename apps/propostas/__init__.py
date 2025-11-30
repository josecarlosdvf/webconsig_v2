# -*- encoding: utf-8 -*-
"""
Módulo de Propostas/Contratos de Empréstimo
Blueprint para gestão completa de propostas, tabelas e contratos
"""

from flask import Blueprint

blueprint = Blueprint(
    'propostas_blueprint',
    __name__,
    url_prefix='/propostas'
)
