# -*- encoding: utf-8 -*-
"""
Blueprint de Mensageria - WhatsApp Integration
"""

from flask import Blueprint

blueprint = Blueprint(
    'messaging_blueprint',
    __name__,
    url_prefix='/mensagens'
)
