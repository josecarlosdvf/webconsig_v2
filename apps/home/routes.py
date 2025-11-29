# -*- encoding: utf-8 -*-
"""
Rotas do Home
"""

from flask import render_template, request
from flask_login import login_required, current_user
from jinja2 import TemplateNotFound

from apps.home import blueprint


@blueprint.route('/dashboard')
@login_required
def dashboard():
    """Página principal do dashboard"""
    return render_template(
        'home/dashboard.html',
        segment='dashboard'
    )


# ============================================
# Rotas de Componentes
# ============================================

@blueprint.route('/buttons')
@login_required
def buttons():
    """Página de exemplos de botões"""
    return render_template('home/buttons.html', segment='buttons')


@blueprint.route('/forms')
@login_required
def forms():
    """Página de exemplos de formulários"""
    return render_template('home/forms.html', segment='forms')


@blueprint.route('/modals')
@login_required
def modals():
    """Página de exemplos de modais"""
    return render_template('home/modals.html', segment='modals')


@blueprint.route('/notifications')
@login_required
def notifications():
    """Página de exemplos de notificações"""
    return render_template('home/notifications.html', segment='notifications')


@blueprint.route('/tables')
@login_required
def tables():
    """Página de exemplos de tabelas"""
    return render_template('home/tables.html', segment='tables')


# ============================================
# Rota Genérica para Templates
# ============================================

@blueprint.route('/<template>')
@login_required
def route_template(template):
    """Rota genérica para templates"""
    try:
        # Remove extensão .html se presente
        if not template.endswith('.html'):
            template += '.html'
        
        # Obtém o segmento para marcar menu ativo
        segment = get_segment(request)
        
        return render_template(
            f'home/{template}',
            segment=segment
        )
    
    except TemplateNotFound:
        return render_template('errors/404.html'), 404
    
    except Exception:
        return render_template('errors/500.html'), 500


def get_segment(request):
    """Extrai o segmento da URL para marcar menu ativo"""
    try:
        segment = request.path.split('/')[-1]
        if segment == '':
            segment = 'dashboard'
        return segment.replace('.html', '')
    except Exception:
        return None
