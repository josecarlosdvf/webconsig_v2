# -*- encoding: utf-8 -*-
"""
Rotas de Recursos Humanos
CRUD de Funcionários e Equipes
"""

from flask import (
    render_template, request, redirect, url_for, 
    flash, jsonify, abort
)
from flask_login import login_required, current_user

from apps import db
from apps.hr import blueprint
from apps.hr.models import Employee, Team, EmployeeStatus, TeamType
from apps.hr.forms import EmployeeForm, TeamForm, EmployeeSearchForm, TerminationForm
from apps.database.models import AuditLog
from apps.files.services import FileService


# =============================================================================
# EQUIPES / CORBANS
# =============================================================================

@blueprint.route('/equipes')
@login_required
def teams_list():
    """Lista de equipes e corbans"""
    team_type = request.args.get('type')
    
    query = Team.query_active().filter_by(is_active=True)
    if team_type:
        query = query.filter_by(type=team_type)
    
    teams = query.order_by(Team.name).all()
    
    return render_template(
        'hr/teams/list.html',
        teams=teams,
        team_type=team_type
    )


@blueprint.route('/equipes/nova', methods=['GET', 'POST'])
@login_required
def team_create():
    """Criar nova equipe/corban"""
    form = TeamForm()
    
    # Gera uma cor única que não é usada por nenhuma outra equipe
    existing_colors = [t.color for t in Team.query_active().filter(Team.color.isnot(None)).all()]
    default_colors = [
        '#206bc4', '#4299e1', '#38a169', '#2fb344', '#d69e2e', '#f59f00',
        '#d63939', '#e53e3e', '#805ad5', '#9f7aea', '#00b5ad', '#319795',
        '#e91e63', '#ed64a6', '#f56565', '#fc8181', '#667eea', '#7c3aed'
    ]
    available_color = '#206bc4'
    for color in default_colors:
        if color not in existing_colors:
            available_color = color
            break
    else:
        # Se todas as cores padrão estão em uso, gera uma aleatória
        import random
        available_color = '#%06x' % random.randint(0, 0xFFFFFF)
    
    if request.method == 'GET' and not form.color.data:
        form.color.data = available_color
    
    if form.validate_on_submit():
        team = Team()
        form.populate_obj(team)
        
        # Limpa CNPJ
        if team.cnpj:
            team.cnpj = ''.join(filter(str.isdigit, team.cnpj))
        
        db.session.add(team)
        db.session.commit()
        
        AuditLog.log(
            action='create',
            table_name='teams',
            record_id=team.id,
            description=f'Equipe criada: {team.name}'
        )
        db.session.commit()
        
        flash('Equipe criada com sucesso!', 'success')
        return redirect(url_for('hr_blueprint.teams_list'))
    
    return render_template(
        'hr/teams/form.html',
        form=form,
        title='Nova Equipe'
    )


@blueprint.route('/equipes/<int:team_id>')
@login_required
def team_view(team_id):
    """Visualizar equipe"""
    team = Team.query_active().filter_by(id=team_id).first_or_404()
    employees = Employee.get_by_team(team_id)
    
    return render_template(
        'hr/teams/view.html',
        team=team,
        employees=employees
    )


@blueprint.route('/equipes/<int:team_id>/editar', methods=['GET', 'POST'])
@login_required
def team_edit(team_id):
    """Editar equipe"""
    team = Team.query_active().filter_by(id=team_id).first_or_404()
    form = TeamForm(obj=team)
    
    if form.validate_on_submit():
        form.populate_obj(team)
        
        # Limpa CNPJ
        if team.cnpj:
            team.cnpj = ''.join(filter(str.isdigit, team.cnpj))
        
        db.session.commit()
        
        AuditLog.log(
            action='update',
            table_name='teams',
            record_id=team.id,
            description=f'Equipe atualizada: {team.name}'
        )
        db.session.commit()
        
        flash('Equipe atualizada com sucesso!', 'success')
        return redirect(url_for('hr_blueprint.team_view', team_id=team.id))
    
    return render_template(
        'hr/teams/form.html',
        form=form,
        team=team,
        title='Editar Equipe'
    )


@blueprint.route('/equipes/<int:team_id>/excluir', methods=['POST'])
@login_required
def team_delete(team_id):
    """Excluir equipe (soft delete)"""
    team = Team.query_active().filter_by(id=team_id).first_or_404()
    
    # Verifica se tem funcionários vinculados
    if team.employee_count > 0:
        flash('Não é possível excluir equipe com funcionários vinculados.', 'danger')
        return redirect(url_for('hr_blueprint.team_view', team_id=team.id))
    
    team.soft_delete(current_user.id)
    
    AuditLog.log(
        action='delete',
        table_name='teams',
        record_id=team.id,
        description=f'Equipe excluída: {team.name}'
    )
    db.session.commit()
    
    flash('Equipe excluída com sucesso!', 'success')
    return redirect(url_for('hr_blueprint.teams_list'))


# =============================================================================
# FUNCIONÁRIOS
# =============================================================================

@blueprint.route('/funcionarios')
@login_required
def employees_list():
    """Lista de funcionários"""
    form = EmployeeSearchForm(request.args)
    
    query = Employee.query_active()
    
    # Filtros
    if form.search.data:
        term = form.search.data.strip()
        cpf_term = ''.join(filter(str.isdigit, term))
        if cpf_term and len(cpf_term) >= 3:
            query = query.filter(Employee.cpf.like(f'%{cpf_term}%'))
        else:
            query = query.filter(Employee.name.ilike(f'%{term}%'))
    
    if form.team_id.data:
        query = query.filter_by(team_id=form.team_id.data)
    
    if form.status.data:
        query = query.filter_by(status=form.status.data)
    
    # Paginação
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    pagination = query.order_by(Employee.name).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template(
        'hr/employees/list.html',
        employees=pagination.items,
        pagination=pagination,
        form=form
    )


@blueprint.route('/funcionarios/novo', methods=['GET', 'POST'])
@login_required
def employee_create():
    """Criar novo funcionário"""
    form = EmployeeForm()
    
    if form.validate_on_submit():
        # Verifica se CPF já existe
        cpf = ''.join(filter(str.isdigit, form.cpf.data))
        existing = Employee.get_by_cpf(cpf)
        if existing:
            flash('Já existe um funcionário com este CPF.', 'danger')
            return render_template('hr/employees/form.html', form=form, title='Novo Funcionário')
        
        employee = Employee()
        form.populate_obj(employee)
        
        # Limpa CPF
        employee.cpf = cpf
        
        # Limpa CEP
        if employee.address_zipcode:
            employee.address_zipcode = ''.join(filter(str.isdigit, employee.address_zipcode))
        
        db.session.add(employee)
        db.session.commit()
        
        # Processa upload de foto se enviada
        photo_file = request.files.get('photo')
        if photo_file and photo_file.filename:
            try:
                from apps.files.services import FileService
                FileService.upload(
                    file=photo_file,
                    category_code='FOTO_3X4',
                    entity_type='employee',
                    entity_id=employee.id,
                    uploaded_by_id=current_user.id,
                    description=f'Foto do funcionário {employee.name}'
                )
            except Exception as e:
                flash(f'Funcionário criado, mas houve erro no upload da foto: {str(e)}', 'warning')
        
        AuditLog.log(
            action='create',
            table_name='employees',
            record_id=employee.id,
            description=f'Funcionário criado: {employee.name}'
        )
        db.session.commit()
        
        flash('Funcionário criado com sucesso!', 'success')
        return redirect(url_for('hr_blueprint.employee_view', employee_id=employee.id))
    
    return render_template(
        'hr/employees/form.html',
        form=form,
        title='Novo Funcionário'
    )
    
    return render_template(
        'hr/employees/form.html',
        form=form,
        title='Novo Funcionário'
    )


@blueprint.route('/funcionarios/<int:employee_id>')
@login_required
def employee_view(employee_id):
    """Visualizar funcionário"""
    employee = Employee.query_active().filter_by(id=employee_id).first_or_404()
    
    # Busca arquivos do funcionário
    files = FileService.get_entity_files('employee', employee_id)
    missing_files = FileService.get_missing_required('employee', employee_id)
    
    return render_template(
        'hr/employees/view.html',
        employee=employee,
        files=files,
        missing_files=missing_files
    )


@blueprint.route('/funcionarios/<int:employee_id>/editar', methods=['GET', 'POST'])
@login_required
def employee_edit(employee_id):
    """Editar funcionário"""
    employee = Employee.query_active().filter_by(id=employee_id).first_or_404()
    form = EmployeeForm(obj=employee)
    
    if form.validate_on_submit():
        # Verifica se CPF já existe (exceto o próprio)
        cpf = ''.join(filter(str.isdigit, form.cpf.data))
        existing = Employee.get_by_cpf(cpf)
        if existing and existing.id != employee.id:
            flash('Já existe outro funcionário com este CPF.', 'danger')
            return render_template(
                'hr/employees/form.html', 
                form=form, 
                employee=employee,
                title='Editar Funcionário'
            )
        
        form.populate_obj(employee)
        
        # Limpa CPF
        employee.cpf = cpf
        
        # Limpa CEP
        if employee.address_zipcode:
            employee.address_zipcode = ''.join(filter(str.isdigit, employee.address_zipcode))
        
        # Processa upload de foto se enviada
        photo_file = request.files.get('photo')
        if photo_file and photo_file.filename:
            try:
                from apps.files.services import FileService
                FileService.upload(
                    file=photo_file,
                    category_code='FOTO_3X4',
                    entity_type='employee',
                    entity_id=employee.id,
                    uploaded_by_id=current_user.id,
                    description=f'Foto do funcionário {employee.name}'
                )
            except Exception as e:
                flash(f'Dados atualizados, mas houve erro no upload da foto: {str(e)}', 'warning')
        
        db.session.commit()
        
        AuditLog.log(
            action='update',
            table_name='employees',
            record_id=employee.id,
            description=f'Funcionário atualizado: {employee.name}'
        )
        db.session.commit()
        
        flash('Funcionário atualizado com sucesso!', 'success')
        return redirect(url_for('hr_blueprint.employee_view', employee_id=employee.id))
    
    return render_template(
        'hr/employees/form.html',
        form=form,
        employee=employee,
        title='Editar Funcionário'
    )


@blueprint.route('/funcionarios/<int:employee_id>/desligar', methods=['GET', 'POST'])
@login_required
def employee_terminate(employee_id):
    """Desligar funcionário"""
    employee = Employee.query_active().filter_by(id=employee_id).first_or_404()
    
    if employee.is_terminated:
        flash('Este funcionário já está desligado.', 'warning')
        return redirect(url_for('hr_blueprint.employee_view', employee_id=employee.id))
    
    form = TerminationForm()
    
    if form.validate_on_submit():
        employee.termination_date = form.termination_date.data
        employee.termination_reason = form.termination_reason.data
        employee.status = EmployeeStatus.TERMINATED
        
        if form.notes.data:
            if employee.notes:
                employee.notes += f'\n\nDesligamento: {form.notes.data}'
            else:
                employee.notes = f'Desligamento: {form.notes.data}'
        
        db.session.commit()
        
        AuditLog.log(
            action='terminate',
            table_name='employees',
            record_id=employee.id,
            description=f'Funcionário desligado: {employee.name}',
            new_values={
                'termination_date': str(form.termination_date.data),
                'termination_reason': form.termination_reason.data
            }
        )
        db.session.commit()
        
        flash('Funcionário desligado com sucesso.', 'success')
        return redirect(url_for('hr_blueprint.employee_view', employee_id=employee.id))
    
    return render_template(
        'hr/employees/terminate.html',
        form=form,
        employee=employee
    )


@blueprint.route('/funcionarios/<int:employee_id>/reativar', methods=['POST'])
@login_required
def employee_reactivate(employee_id):
    """Reativar funcionário desligado"""
    employee = Employee.query_active().filter_by(id=employee_id).first_or_404()
    
    if not employee.is_terminated:
        flash('Este funcionário não está desligado.', 'warning')
        return redirect(url_for('hr_blueprint.employee_view', employee_id=employee.id))
    
    old_termination = {
        'date': str(employee.termination_date),
        'reason': employee.termination_reason
    }
    
    employee.reactivate()
    
    AuditLog.log(
        action='reactivate',
        table_name='employees',
        record_id=employee.id,
        description=f'Funcionário reativado: {employee.name}',
        old_values=old_termination
    )
    db.session.commit()
    
    flash('Funcionário reativado com sucesso!', 'success')
    return redirect(url_for('hr_blueprint.employee_view', employee_id=employee.id))


@blueprint.route('/funcionarios/<int:employee_id>/excluir', methods=['POST'])
@login_required
def employee_delete(employee_id):
    """Excluir funcionário (soft delete)"""
    employee = Employee.query_active().filter_by(id=employee_id).first_or_404()
    
    employee.soft_delete(current_user.id)
    
    AuditLog.log(
        action='delete',
        table_name='employees',
        record_id=employee.id,
        description=f'Funcionário excluído: {employee.name}'
    )
    db.session.commit()
    
    flash('Funcionário excluído com sucesso!', 'success')
    return redirect(url_for('hr_blueprint.employees_list'))


# =============================================================================
# API / AJAX
# =============================================================================

@blueprint.route('/api/funcionarios/buscar')
@login_required
def api_employee_search():
    """Busca de funcionários (autocomplete)"""
    term = request.args.get('term', '')
    limit = request.args.get('limit', 50, type=int)
    
    # Se não há termo, retorna lista de funcionários ativos
    if len(term) < 2:
        employees = Employee.query_active().filter_by(
            status=EmployeeStatus.ACTIVE
        ).order_by(Employee.name).limit(limit).all()
    else:
        employees = Employee.search(term, limit=limit)
    
    return jsonify({
        'results': [{
            'id': e.id,
            'text': e.name,
            'name': e.name,
            'cpf': e.cpf_formatted,
            'team': e.team.display_name if e.team else None,
            'position': e.position
        } for e in employees]
    })


@blueprint.route('/api/equipes')
@login_required
def api_teams_list():
    """Lista de equipes para selects"""
    team_type = request.args.get('type')
    
    query = Team.query_active().filter_by(is_active=True)
    if team_type:
        query = query.filter_by(type=team_type)
    
    teams = query.order_by(Team.name).all()
    
    return jsonify({
        'results': [{
            'id': t.id,
            'text': t.display_name,
            'name': t.display_name,
            'type': t.type,
            'employee_count': t.employee_count
        } for t in teams]
    })


@blueprint.route('/api/cep/<cep>')
@login_required
def api_cep_lookup(cep):
    """Busca endereço por CEP (via ViaCEP)"""
    from apps.services.viacep import ViaCepService
    
    address = ViaCepService.get_address_dict(cep)
    
    if address:
        # Retorna no formato esperado pelo frontend legado
        return jsonify({
            'street': address.get('logradouro', ''),
            'neighborhood': address.get('bairro', ''),
            'city': address.get('localidade', ''),
            'state': address.get('uf', ''),
            'zipcode': ViaCepService._clean_cep(cep),
            # Também inclui dados completos
            **address
        })
    
    return jsonify({'error': 'CEP não encontrado'}), 404


@blueprint.route('/funcionarios/<int:employee_id>/upload', methods=['POST'])
@login_required
def employee_upload_document(employee_id):
    """Upload de documento do funcionário"""
    employee = Employee.query_active().filter_by(id=employee_id).first_or_404()
    
    file = request.files.get('file')
    category_code = request.form.get('category', 'DOC_OUTROS')
    description = request.form.get('description', '')
    
    if not file or not file.filename:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Nenhum arquivo selecionado'}), 400
        flash('Nenhum arquivo selecionado.', 'danger')
        return redirect(url_for('hr_blueprint.employee_view', employee_id=employee_id))
    
    try:
        from apps.files.services import FileService
        
        file_record = FileService.upload(
            file=file,
            category_code=category_code,
            entity_type='employee',
            entity_id=employee_id,
            uploaded_by_id=current_user.id,
            description=description or f'Documento de {employee.name}'
        )
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'file': {
                    'id': file_record.id,
                    'name': file_record.original_name,
                    'category': file_record.category.name if file_record.category else None,
                    'size': file_record.size_formatted
                }
            })
        
        flash('Documento enviado com sucesso!', 'success')
        
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': str(e)}), 400
        flash(f'Erro ao enviar documento: {str(e)}', 'danger')
    
    return redirect(url_for('hr_blueprint.employee_view', employee_id=employee_id))


@blueprint.route('/funcionarios/<int:employee_id>/documentos')
@login_required
def employee_documents(employee_id):
    """Lista de documentos do funcionário (JSON)"""
    employee = Employee.query_active().filter_by(id=employee_id).first_or_404()
    
    files = employee.get_files()
    missing = employee.get_missing_documents()
    
    return jsonify({
        'employee': {
            'id': employee.id,
            'name': employee.name,
            'documents_complete': employee.documents_complete
        },
        'files': [{
            'id': f.id,
            'name': f.original_name,
            'category': f.category.name if f.category else None,
            'category_code': f.category.code if f.category else None,
            'size': f.size_formatted,
            'uploaded_at': f.created_at.isoformat() if f.created_at else None,
            'is_image': f.is_image,
            'thumbnail_url': url_for('files_blueprint.thumbnail', file_id=f.id) if f.is_image else None
        } for f in files],
        'missing': [{
            'code': c.code,
            'name': c.name,
            'is_required': c.is_required
        } for c in missing]
    })
