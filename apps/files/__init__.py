# -*- encoding: utf-8 -*-
"""
Blueprint de Gestão de Arquivos
"""

from flask import Blueprint

blueprint = Blueprint(
    'files_blueprint',
    __name__,
    url_prefix='/files'
)
