# -*- encoding: utf-8 -*-
"""
Rotas de Configurações do Sistema
"""

from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from apps.settings import blueprint
from apps.settings.models import SystemSettings
from apps.settings.utils import SETTINGS_CATEGORIES, refresh_settings_cache
from apps.settings.forms import (
    SystemInfoForm, CompanyForm, DeveloperForm,
    AppearanceForm, LocalizationForm, SecurityForm
)
from apps import db
from apps.files.models import FileCategory


@blueprint.route('/')
@login_required
def index():
    """Página principal de configurações"""
    settings = SystemSettings.get_all_grouped()
    
    return render_template(
        'settings/index.html',
        segment='settings',
        settings=settings,
        categories=SETTINGS_CATEGORIES
    )


@blueprint.route('/sistema', methods=['GET', 'POST'])
@login_required
def sistema():
    """Configurações do sistema"""
    form = SystemInfoForm()
    
    if request.method == 'GET':
        form.app_name.data = SystemSettings.get('app_name', '')
        form.app_description.data = SystemSettings.get('app_description', '')
        form.app_version.data = SystemSettings.get('app_version', '')
    
    if form.validate_on_submit():
        SystemSettings.set('app_name', form.app_name.data)
        SystemSettings.set('app_description', form.app_description.data)
        SystemSettings.set('app_version', form.app_version.data)
        refresh_settings_cache()
        flash('Configurações do sistema atualizadas com sucesso!', 'success')
        return redirect(url_for('settings_blueprint.sistema'))
    
    return render_template(
        'settings/sistema.html',
        segment='settings',
        form=form,
        title='Informações do Sistema',
        category='sistema'
    )


@blueprint.route('/empresa', methods=['GET', 'POST'])
@login_required
def empresa():
    """Configurações da empresa"""
    form = CompanyForm()
    
    if request.method == 'GET':
        form.company_name.data = SystemSettings.get('company_name', '')
        form.company_cnpj.data = SystemSettings.get('company_cnpj', '')
        form.company_address.data = SystemSettings.get('company_address', '')
        form.company_phone.data = SystemSettings.get('company_phone', '')
        form.company_email.data = SystemSettings.get('company_email', '')
    
    if form.validate_on_submit():
        SystemSettings.set('company_name', form.company_name.data)
        SystemSettings.set('company_cnpj', form.company_cnpj.data)
        SystemSettings.set('company_address', form.company_address.data)
        SystemSettings.set('company_phone', form.company_phone.data)
        SystemSettings.set('company_email', form.company_email.data)
        refresh_settings_cache()
        flash('Dados da empresa atualizados com sucesso!', 'success')
        return redirect(url_for('settings_blueprint.empresa'))
    
    return render_template(
        'settings/empresa.html',
        segment='settings',
        form=form,
        title='Dados da Empresa',
        category='empresa'
    )


@blueprint.route('/desenvolvedor', methods=['GET', 'POST'])
@login_required
def desenvolvedor():
    """Configurações do desenvolvedor"""
    form = DeveloperForm()
    
    if request.method == 'GET':
        form.developer_name.data = SystemSettings.get('developer_name', '')
        form.developer_url.data = SystemSettings.get('developer_url', '')
        form.developer_email.data = SystemSettings.get('developer_email', '')
    
    if form.validate_on_submit():
        SystemSettings.set('developer_name', form.developer_name.data)
        SystemSettings.set('developer_url', form.developer_url.data)
        SystemSettings.set('developer_email', form.developer_email.data)
        refresh_settings_cache()
        flash('Dados do desenvolvedor atualizados com sucesso!', 'success')
        return redirect(url_for('settings_blueprint.desenvolvedor'))
    
    return render_template(
        'settings/desenvolvedor.html',
        segment='settings',
        form=form,
        title='Dados do Desenvolvedor',
        category='desenvolvedor'
    )


@blueprint.route('/aparencia', methods=['GET', 'POST'])
@login_required
def aparencia():
    """Configurações de aparência"""
    form = AppearanceForm()
    
    if request.method == 'GET':
        form.logo_url.data = SystemSettings.get('logo_url', '')
        form.logo_dark_url.data = SystemSettings.get('logo_dark_url', '')
        form.favicon_url.data = SystemSettings.get('favicon_url', '')
        form.primary_color.data = SystemSettings.get('primary_color', '#1F2937')
        form.secondary_color.data = SystemSettings.get('secondary_color', '#6B7280')
    
    if form.validate_on_submit():
        SystemSettings.set('logo_url', form.logo_url.data)
        SystemSettings.set('logo_dark_url', form.logo_dark_url.data)
        SystemSettings.set('favicon_url', form.favicon_url.data)
        SystemSettings.set('primary_color', form.primary_color.data)
        SystemSettings.set('secondary_color', form.secondary_color.data)
        refresh_settings_cache()
        flash('Configurações de aparência atualizadas com sucesso!', 'success')
        return redirect(url_for('settings_blueprint.aparencia'))
    
    return render_template(
        'settings/aparencia.html',
        segment='settings',
        form=form,
        title='Aparência',
        category='aparencia'
    )


@blueprint.route('/localizacao', methods=['GET', 'POST'])
@login_required
def localizacao():
    """Configurações de localização"""
    form = LocalizationForm()
    
    if request.method == 'GET':
        form.language.data = SystemSettings.get('language', 'pt-BR')
        form.timezone.data = SystemSettings.get('timezone', 'America/Sao_Paulo')
        form.date_format.data = SystemSettings.get('date_format', 'DD/MM/YYYY')
        form.currency.data = SystemSettings.get('currency', 'BRL')
    
    if form.validate_on_submit():
        SystemSettings.set('language', form.language.data)
        SystemSettings.set('timezone', form.timezone.data)
        SystemSettings.set('date_format', form.date_format.data)
        SystemSettings.set('currency', form.currency.data)
        refresh_settings_cache()
        flash('Configurações de localização atualizadas com sucesso!', 'success')
        return redirect(url_for('settings_blueprint.localizacao'))
    
    return render_template(
        'settings/localizacao.html',
        segment='settings',
        form=form,
        title='Localização',
        category='localizacao'
    )


@blueprint.route('/seguranca', methods=['GET', 'POST'])
@login_required
def seguranca():
    """Configurações de segurança"""
    form = SecurityForm()
    
    if request.method == 'GET':
        form.session_timeout.data = str(SystemSettings.get('session_timeout', 3600))
        form.max_login_attempts.data = str(SystemSettings.get('max_login_attempts', 5))
        form.password_min_length.data = str(SystemSettings.get('password_min_length', 8))
        form.maintenance_mode.data = SystemSettings.get('maintenance_mode', False)
    
    if form.validate_on_submit():
        SystemSettings.set('session_timeout', form.session_timeout.data, value_type='int')
        SystemSettings.set('max_login_attempts', form.max_login_attempts.data, value_type='int')
        SystemSettings.set('password_min_length', form.password_min_length.data, value_type='int')
        SystemSettings.set('maintenance_mode', 'true' if form.maintenance_mode.data else 'false', value_type='bool')
        refresh_settings_cache()
        flash('Configurações de segurança atualizadas com sucesso!', 'success')
        return redirect(url_for('settings_blueprint.seguranca'))
    
    return render_template(
        'settings/seguranca.html',
        segment='settings',
        form=form,
        title='Segurança',
        category='seguranca'
    )


# =============================================================================
# TIPOS DE ARQUIVO
# =============================================================================

@blueprint.route('/tipos-arquivo')
@login_required
def tipos_arquivo():
    """Configuração de tipos de arquivo permitidos"""
    if not current_user.is_admin:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home_blueprint.dashboard'))
    
    categories = FileCategory.query_active().order_by(FileCategory.display_order).all()
    
    return render_template(
        'settings/tipos_arquivo.html',
        segment='settings',
        categories=categories,
        title='Tipos de Arquivo'
    )


@blueprint.route('/tipos-arquivo/criar', methods=['POST'])
@login_required
def tipo_arquivo_criar():
    """Criar novo tipo de arquivo"""
    if not current_user.is_admin:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home_blueprint.dashboard'))
    
    code = request.form.get('code', '').upper().replace(' ', '_')
    name = request.form.get('name')
    
    if not name or not code:
        flash('Nome e código são obrigatórios.', 'danger')
        return redirect(url_for('settings_blueprint.tipos_arquivo'))
    
    # Verifica se já existe
    existing = FileCategory.query.filter_by(code=code).first()
    if existing:
        flash('Já existe um tipo de arquivo com este código.', 'danger')
        return redirect(url_for('settings_blueprint.tipos_arquivo'))
    
    category = FileCategory(
        code=code,
        name=name,
        description=request.form.get('description'),
        allowed_extensions=request.form.get('allowed_extensions', 'jpg,jpeg,png,pdf'),
        max_size_mb=float(request.form.get('max_size_mb', 5)),
        is_required='is_required' in request.form,
        requires_validation='requires_validation' in request.form,
        allow_multiple='allow_multiple' in request.form,
        is_active='is_active' in request.form,
        entity_types=request.form.get('entity_types', 'employee'),
        display_order=int(request.form.get('display_order', 0))
    )
    
    db.session.add(category)
    db.session.commit()
    
    flash(f'Tipo de arquivo "{name}" criado com sucesso!', 'success')
    return redirect(url_for('settings_blueprint.tipos_arquivo'))


@blueprint.route('/tipos-arquivo/<int:id>/editar', methods=['POST'])
@login_required
def tipo_arquivo_editar(id):
    """Editar tipo de arquivo"""
    if not current_user.is_admin:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home_blueprint.dashboard'))
    
    category = FileCategory.query_active().get_or_404(id)
    
    category.name = request.form.get('name', category.name)
    category.description = request.form.get('description')
    category.allowed_extensions = request.form.get('allowed_extensions', category.allowed_extensions)
    category.max_size_mb = float(request.form.get('max_size_mb', category.max_size_mb))
    category.is_required = 'is_required' in request.form
    category.requires_validation = 'requires_validation' in request.form
    category.allow_multiple = 'allow_multiple' in request.form
    category.is_active = 'is_active' in request.form
    category.entity_types = request.form.get('entity_types', category.entity_types)
    category.display_order = int(request.form.get('display_order', category.display_order))
    
    db.session.commit()
    
    flash(f'Tipo de arquivo "{category.name}" atualizado com sucesso!', 'success')
    return redirect(url_for('settings_blueprint.tipos_arquivo'))


@blueprint.route('/tipos-arquivo/<int:id>/excluir', methods=['POST'])
@login_required
def tipo_arquivo_excluir(id):
    """Excluir tipo de arquivo"""
    if not current_user.is_admin:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home_blueprint.dashboard'))
    
    category = FileCategory.query_active().get_or_404(id)
    
    # Sempre usa soft delete para consistência
    category.soft_delete(current_user.id)
    
    db.session.commit()
    
    flash(f'Tipo de arquivo excluído com sucesso!', 'success')
    return redirect(url_for('settings_blueprint.tipos_arquivo'))
