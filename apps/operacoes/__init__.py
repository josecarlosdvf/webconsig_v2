# -*- encoding: utf-8 -*-
"""
Módulo de Operações/Contratos de Empréstimo
Blueprint para gestão completa de propostas, tabelas e contratos
"""

from flask import Blueprint

blueprint = Blueprint(
    'operacoes_blueprint',
    __name__,
    url_prefix='/operacoes'
)
