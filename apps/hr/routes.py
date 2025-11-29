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
    team = Team.query_active().get_or_404(team_id)
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
    team = Team.query_active().get_or_404(team_id)
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
    team = Team.query_active().get_or_404(team_id)
    
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


@blueprint.route('/funcionarios/<int:employee_id>')
@login_required
def employee_view(employee_id):
    """Visualizar funcionário"""
    employee = Employee.query_active().get_or_404(employee_id)
    
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
    employee = Employee.query_active().get_or_404(employee_id)
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
    employee = Employee.query_active().get_or_404(employee_id)
    
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
    employee = Employee.query_active().get_or_404(employee_id)
    
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
    employee = Employee.query_active().get_or_404(employee_id)
    
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
    limit = request.args.get('limit', 10, type=int)
    
    if len(term) < 2:
        return jsonify([])
    
    employees = Employee.search(term, limit=limit)
    
    return jsonify([{
        'id': e.id,
        'name': e.name,
        'cpf': e.cpf_formatted,
        'team': e.team.display_name if e.team else None,
        'position': e.position
    } for e in employees])


@blueprint.route('/api/equipes')
@login_required
def api_teams_list():
    """Lista de equipes para selects"""
    team_type = request.args.get('type')
    
    query = Team.query_active().filter_by(is_active=True)
    if team_type:
        query = query.filter_by(type=team_type)
    
    teams = query.order_by(Team.name).all()
    
    return jsonify([{
        'id': t.id,
        'name': t.display_name,
        'type': t.type,
        'employee_count': t.employee_count
    } for t in teams])


@blueprint.route('/api/cep/<cep>')
@login_required
def api_cep_lookup(cep):
    """Busca endereço por CEP (via ViaCEP)"""
    import requests
    
    cep_clean = ''.join(filter(str.isdigit, cep))
    
    if len(cep_clean) != 8:
        return jsonify({'error': 'CEP inválido'}), 400
    
    try:
        response = requests.get(f'https://viacep.com.br/ws/{cep_clean}/json/', timeout=5)
        data = response.json()
        
        if 'erro' in data:
            return jsonify({'error': 'CEP não encontrado'}), 404
        
        return jsonify({
            'street': data.get('logradouro', ''),
            'neighborhood': data.get('bairro', ''),
            'city': data.get('localidade', ''),
            'state': data.get('uf', ''),
            'zipcode': cep_clean
        })
    
    except Exception as e:
        return jsonify({'error': 'Erro ao buscar CEP'}), 500
