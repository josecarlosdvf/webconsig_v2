# -*- encoding: utf-8 -*-
"""
Blueprint de Recursos Humanos
Gestão de funcionários e equipes/corbans
"""

from flask import Blueprint

blueprint = Blueprint(
    'hr_blueprint',
    __name__,
    url_prefix='/rh'
)
