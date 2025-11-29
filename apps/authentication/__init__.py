# -*- encoding: utf-8 -*-
"""
Blueprint de Autenticação
"""

from flask import Blueprint

blueprint = Blueprint(
    'authentication_blueprint',
    __name__,
    url_prefix=''
)
