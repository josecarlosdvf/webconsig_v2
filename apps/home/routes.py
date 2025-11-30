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
    
    # Verificação de sistema para admins
    system_warnings = []
    system_status = None
    
    if current_user.is_admin:
        try:
            from apps.system_check import SystemCheck
            system_status = SystemCheck.get_system_status()
            system_warnings = system_status.get('warnings', [])
        except Exception as e:
            # Se falhar, não bloqueia o dashboard
            pass
    
    return render_template(
        'home/dashboard.html',
        segment='dashboard',
        system_warnings=system_warnings,
        system_status=system_status
    )


@blueprint.route('/system-status')
@login_required
def system_status():
    """Página de status do sistema (apenas admin)"""
    if not current_user.is_admin:
        from flask import abort
        abort(403)
    
    from apps.system_check import SystemCheck
    
    dependencies = SystemCheck.check_all_dependencies()
    status = SystemCheck.get_system_status()
    
    return render_template(
        'home/system_status.html',
        segment='system-status',
        dependencies=dependencies,
        status=status
    )


# ============================================
# Consulta Lemit - Dados Cadastrais por CPF
# ============================================

@blueprint.route('/consulta-cpf')
@login_required
def consulta_cpf():
    """Página de consulta de CPF via Lemit"""
    from apps.services.lemit import LemitService
    
    # Estatísticas para exibir no dashboard
    stats = LemitService.get_estatisticas()
    
    # Histórico recente (últimas 20 consultas)
    historico = LemitService.get_historico(limit=20)
    
    return render_template(
        'home/consulta_cpf.html',
        segment='consulta-cpf',
        stats=stats,
        historico=historico
    )


@blueprint.route('/consulta-cpf/logs')
@login_required
def consulta_cpf_logs():
    """Página de logs/auditoria de consultas Lemit"""
    if not current_user.is_admin:
        from flask import abort
        abort(403)
    
    from apps.services.lemit import LemitService, ConsultaLog
    
    # Parâmetros de filtro
    cpf = request.args.get('cpf', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    # Query
    query = ConsultaLog.query
    
    if cpf:
        cpf_clean = ''.join(filter(str.isdigit, cpf))
        if cpf_clean:
            query = query.filter(ConsultaLog.cpf.like(f'%{cpf_clean}%'))
    
    # Paginação
    pagination = query.order_by(ConsultaLog.data_consulta.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Estatísticas
    stats = LemitService.get_estatisticas()
    
    return render_template(
        'home/consulta_cpf_logs.html',
        segment='consulta-cpf-logs',
        consultas=pagination.items,
        pagination=pagination,
        stats=stats,
        cpf_filter=cpf
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
