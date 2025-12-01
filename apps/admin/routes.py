# -*- encoding: utf-8 -*-
"""
Rotas de Administração - Usuários, Grupos e Permissões
"""

from flask import (
    render_template, redirect, url_for, flash, request, jsonify, abort
)
from flask_login import login_required, current_user
from sqlalchemy import or_, and_
from datetime import datetime

from apps import db
from apps.admin import blueprint
from apps.authentication.models import (
    Users, UserGroup, Permission, UserGroupMembership, 
    LoginHistory, UserInvitation, DEFAULT_PERMISSIONS, DEFAULT_GROUPS
)
from apps.authentication.forms_admin import (
    UserForm, UserGroupForm, InvitationForm, UnlockUserForm,
    ResetPasswordAdminForm, UserSearchForm, CompleteRegistrationForm
)
from apps.authentication.decorators import permission_required, admin_required
from apps.database.models import AuditLog


# =============================================================================
# DASHBOARD ADMIN
# =============================================================================

@blueprint.route('/')
@login_required
@permission_required('users.view', 'groups.view', 'audit.view')
def index():
    """Dashboard de administração"""
    
    # Estatísticas
    stats = {
        'total_users': Users.query_active().count(),
        'active_users': Users.query_active().filter_by(is_active=True).count(),
        'locked_users': Users.query_active().filter(
            Users.locked_until > datetime.utcnow()
        ).count(),
        'total_groups': UserGroup.query_active().count(),
        'pending_invitations': UserInvitation.query_active().filter(
            UserInvitation.used_at.is_(None),
            UserInvitation.expires_at > datetime.utcnow()
        ).count()
    }
    
    # Últimos logins
    recent_logins = LoginHistory.query.filter_by(success=True).order_by(
        LoginHistory.created_at.desc()
    ).limit(10).all()
    
    # Últimas atividades
    recent_activities = AuditLog.query.order_by(
        AuditLog.created_at.desc()
    ).limit(10).all()
    
    return render_template(
        'admin/index.html',
        stats=stats,
        recent_logins=recent_logins,
        recent_activities=recent_activities
    )


# =============================================================================
# USUÁRIOS
# =============================================================================

@blueprint.route('/usuarios')
@login_required
@permission_required('users.view')
def users_list():
    """Lista de usuários"""
    
    form = UserSearchForm(request.args)
    
    query = Users.query_active()
    
    # Filtros
    if form.search.data:
        search = f'%{form.search.data}%'
        query = query.filter(or_(
            Users.username.ilike(search),
            Users.email.ilike(search),
            Users.first_name.ilike(search),
            Users.last_name.ilike(search)
        ))
    
    if form.status.data == 'active':
        query = query.filter(Users.is_active == True)
    elif form.status.data == 'inactive':
        query = query.filter(Users.is_active == False)
    elif form.status.data == 'locked':
        query = query.filter(Users.locked_until > datetime.utcnow())
    
    if form.is_admin.data:
        query = query.filter(Users.is_admin == (form.is_admin.data == '1'))
    
    if form.group_id.data:
        query = query.join(
            UserGroupMembership, 
            Users.id == UserGroupMembership.user_id
        ).filter(
            UserGroupMembership.group_id == form.group_id.data,
            UserGroupMembership.deleted_at.is_(None)
        )
    
    # Paginação
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    pagination = query.order_by(Users.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template(
        'admin/users/list.html',
        users=pagination.items,
        pagination=pagination,
        form=form
    )


@blueprint.route('/usuarios/novo', methods=['GET', 'POST'])
@login_required
@permission_required('users.create')
def users_create():
    """Criar novo usuário"""
    
    form = UserForm()
    
    # Carrega funcionários disponíveis para vinculação
    from apps.hr.models import Employee, EmployeeStatus
    employees = Employee.query_active().filter_by(
        status=EmployeeStatus.ACTIVE,
        user_id=None
    ).order_by(Employee.name).all()
    form.employee_id.choices = [(0, '-- Nenhum --')] + [
        (e.id, e.name) for e in employees
    ]
    
    if form.validate_on_submit():
        try:
            user = Users(
                username=form.username.data.lower().strip(),
                email=form.email.data.lower().strip(),
                password=form.password.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                phone=form.phone.data,
                login_type_allowed=form.login_type_allowed.data,
                is_active=form.is_active.data,
                is_admin=form.is_admin.data,
                bio=form.bio.data
            )
            
            db.session.add(user)
            db.session.flush()  # Para obter o ID
            
            # Adiciona aos grupos selecionados
            for group_id in form.groups.data:
                group = UserGroup.query.get(group_id)
                if group:
                    user.add_to_group(group, current_user.id)
            
            # Vincula funcionário
            if form.employee_id.data:
                employee = Employee.query.get(form.employee_id.data)
                if employee:
                    employee.user_id = user.id
            
            db.session.commit()
            
            AuditLog.log(
                action='user.created',
                table_name='user',
                record_id=user.id,
                description=f'Usuário {user.username} criado',
                user_id=current_user.id
            )
            
            flash('Usuário criado com sucesso!', 'success')
            return redirect(url_for('admin_blueprint.users_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar usuário: {str(e)}', 'danger')
    
    return render_template('admin/users/form.html', form=form, is_new=True)


@blueprint.route('/usuarios/<int:user_id>')
@login_required
@permission_required('users.view')
def users_view(user_id):
    """Visualizar detalhes do usuário"""
    
    user = Users.find_by_id(user_id)
    if not user:
        flash('Usuário não encontrado.', 'warning')
        return redirect(url_for('admin_blueprint.users_list'))
    
    # Histórico de login
    login_history = LoginHistory.get_user_history(user_id, limit=20)
    
    # Atividades recentes
    activities = AuditLog.query.filter_by(user_id=user_id).order_by(
        AuditLog.created_at.desc()
    ).limit(20).all()
    
    return render_template(
        'admin/users/view.html',
        user=user,
        login_history=login_history,
        activities=activities
    )


@blueprint.route('/usuarios/<int:user_id>/editar', methods=['GET', 'POST'])
@login_required
@permission_required('users.edit')
def users_edit(user_id):
    """Editar usuário"""
    
    user = Users.find_by_id(user_id)
    if not user:
        flash('Usuário não encontrado.', 'warning')
        return redirect(url_for('admin_blueprint.users_list'))
    
    form = UserForm(obj=user)
    
    # Carrega funcionários disponíveis
    from apps.hr.models import Employee, EmployeeStatus
    employees = Employee.query_active().filter(
        or_(
            Employee.user_id.is_(None),
            Employee.user_id == user.id
        ),
        Employee.status == EmployeeStatus.ACTIVE
    ).order_by(Employee.name).all()
    form.employee_id.choices = [(0, '-- Nenhum --')] + [
        (e.id, e.name) for e in employees
    ]
    
    if request.method == 'GET':
        form.groups.data = [m.group_id for m in user.groups if not m.deleted_at]
        if hasattr(user, 'employee') and user.employee:
            form.employee_id.data = user.employee.id
    
    if form.validate_on_submit():
        try:
            user.username = form.username.data.lower().strip()
            user.email = form.email.data.lower().strip()
            user.first_name = form.first_name.data
            user.last_name = form.last_name.data
            user.phone = form.phone.data
            user.login_type_allowed = form.login_type_allowed.data
            user.is_active = form.is_active.data
            user.is_admin = form.is_admin.data
            user.bio = form.bio.data
            
            # Atualiza senha se informada
            if form.password.data:
                user.set_password(form.password.data)
            
            # Atualiza grupos
            current_groups = {m.group_id for m in user.groups if not m.deleted_at}
            new_groups = set(form.groups.data)
            
            # Remove grupos desmarcados
            for group_id in current_groups - new_groups:
                group = UserGroup.query.get(group_id)
                if group:
                    user.remove_from_group(group, current_user.id)
            
            # Adiciona novos grupos
            for group_id in new_groups - current_groups:
                group = UserGroup.query.get(group_id)
                if group:
                    user.add_to_group(group, current_user.id)
            
            # Atualiza vínculo com funcionário
            from apps.hr.models import Employee
            
            # Remove vínculo antigo
            if hasattr(user, 'employee') and user.employee:
                if user.employee.id != form.employee_id.data:
                    user.employee.user_id = None
            
            # Adiciona novo vínculo
            if form.employee_id.data:
                employee = Employee.query.get(form.employee_id.data)
                if employee:
                    employee.user_id = user.id
            
            db.session.commit()
            
            AuditLog.log(
                action='user.updated',
                table_name='user',
                record_id=user.id,
                description=f'Usuário {user.username} atualizado',
                user_id=current_user.id
            )
            
            flash('Usuário atualizado com sucesso!', 'success')
            return redirect(url_for('admin_blueprint.users_view', user_id=user.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar usuário: {str(e)}', 'danger')
    
    return render_template('admin/users/form.html', form=form, user=user, is_new=False)


@blueprint.route('/usuarios/<int:user_id>/excluir', methods=['POST'])
@login_required
@permission_required('users.delete')
def users_delete(user_id):
    """Excluir usuário (soft delete)"""
    
    user = Users.find_by_id(user_id)
    if not user:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Usuário não encontrado.'}), 404
        flash('Usuário não encontrado.', 'warning')
        return redirect(url_for('admin_blueprint.users_list'))
    
    # Não pode excluir a si mesmo
    if user.id == current_user.id:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Você não pode excluir sua própria conta.'}), 400
        flash('Você não pode excluir sua própria conta.', 'warning')
        return redirect(url_for('admin_blueprint.users_list'))
    
    try:
        user.soft_delete(current_user.id)
        
        AuditLog.log(
            action='user.deleted',
            table_name='user',
            record_id=user.id,
            description=f'Usuário {user.username} excluído',
            user_id=current_user.id
        )
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': 'Usuário excluído com sucesso!'})
        
        flash('Usuário excluído com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': str(e)}), 500
        flash(f'Erro ao excluir usuário: {str(e)}', 'danger')
    
    return redirect(url_for('admin_blueprint.users_list'))


@blueprint.route('/usuarios/<int:user_id>/desbloquear', methods=['POST'])
@login_required
@permission_required('users.unlock')
def users_unlock(user_id):
    """Desbloquear usuário"""
    
    user = Users.find_by_id(user_id)
    if not user:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Usuário não encontrado.'}), 404
        flash('Usuário não encontrado.', 'warning')
        return redirect(url_for('admin_blueprint.users_list'))
    
    try:
        user.unlock()
        
        AuditLog.log(
            action='user.unlocked',
            table_name='user',
            record_id=user.id,
            description=f'Usuário {user.username} desbloqueado',
            user_id=current_user.id
        )
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': 'Usuário desbloqueado com sucesso!'})
        
        flash('Usuário desbloqueado com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': str(e)}), 500
        flash(f'Erro ao desbloquear usuário: {str(e)}', 'danger')
    
    return redirect(url_for('admin_blueprint.users_view', user_id=user.id))


@blueprint.route('/usuarios/<int:user_id>/resetar-senha', methods=['POST'])
@login_required
@permission_required('users.reset_password')
def users_reset_password(user_id):
    """Resetar senha do usuário"""
    
    user = Users.find_by_id(user_id)
    if not user:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Usuário não encontrado.'}), 404
        flash('Usuário não encontrado.', 'warning')
        return redirect(url_for('admin_blueprint.users_list'))
    
    form = ResetPasswordAdminForm()
    
    if form.validate_on_submit():
        try:
            user.set_password(form.new_password.data)
            db.session.commit()
            
            AuditLog.log(
                action='user.password_reset',
                table_name='user',
                record_id=user.id,
                description=f'Senha do usuário {user.username} resetada por admin',
                user_id=current_user.id
            )
            
            # TODO: Enviar e-mail se form.send_email.data
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': True, 'message': 'Senha alterada com sucesso!'})
            
            flash('Senha alterada com sucesso!', 'success')
            
        except Exception as e:
            db.session.rollback()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'error': str(e)}), 500
            flash(f'Erro ao alterar senha: {str(e)}', 'danger')
    else:
        errors = [e for field_errors in form.errors.values() for e in field_errors]
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': ', '.join(errors)}), 400
        for error in errors:
            flash(error, 'danger')
    
    return redirect(url_for('admin_blueprint.users_view', user_id=user.id))


@blueprint.route('/usuarios/<int:user_id>/ativar', methods=['POST'])
@login_required
@permission_required('users.edit')
def users_toggle_active(user_id):
    """Ativar/Desativar usuário"""
    
    user = Users.find_by_id(user_id)
    if not user:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Usuário não encontrado.'}), 404
        flash('Usuário não encontrado.', 'warning')
        return redirect(url_for('admin_blueprint.users_list'))
    
    # Não pode desativar a si mesmo
    if user.id == current_user.id:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Você não pode desativar sua própria conta.'}), 400
        flash('Você não pode desativar sua própria conta.', 'warning')
        return redirect(url_for('admin_blueprint.users_view', user_id=user.id))
    
    try:
        user.is_active = not user.is_active
        db.session.commit()
        
        action = 'activated' if user.is_active else 'deactivated'
        msg = 'ativado' if user.is_active else 'desativado'
        
        AuditLog.log(
            action=f'user.{action}',
            table_name='user',
            record_id=user.id,
            description=f'Usuário {user.username} {msg}',
            user_id=current_user.id
        )
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True, 
                'message': f'Usuário {msg} com sucesso!',
                'is_active': user.is_active
            })
        
        flash(f'Usuário {msg} com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': str(e)}), 500
        flash(f'Erro ao alterar status: {str(e)}', 'danger')
    
    return redirect(url_for('admin_blueprint.users_view', user_id=user.id))


@blueprint.route('/usuarios/<int:user_id>/toggle-active', methods=['POST'])
@login_required
@permission_required('users.edit')
def users_toggle_active_json(user_id):
    """Ativar/Desativar usuário via JSON (para toggle inline)"""
    
    user = Users.find_by_id(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'Usuário não encontrado.'}), 404
    
    if user.id == current_user.id:
        return jsonify({'success': False, 'message': 'Você não pode desativar sua própria conta.'}), 400
    
    try:
        data = request.get_json() or {}
        user.is_active = data.get('active', not user.is_active)
        db.session.commit()
        
        msg = 'ativado' if user.is_active else 'desativado'
        
        AuditLog.log(
            action=f'user.{"activated" if user.is_active else "deactivated"}',
            table_name='user',
            record_id=user.id,
            description=f'Usuário {user.username} {msg}',
            user_id=current_user.id
        )
        
        return jsonify({
            'success': True, 
            'message': f'Usuário {msg} com sucesso!',
            'is_active': user.is_active
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@blueprint.route('/usuarios/<int:user_id>/send-invite', methods=['POST'])
@login_required
@permission_required('users.invite')
def users_send_invite(user_id):
    """Enviar convite por e-mail para usuário que nunca logou"""
    
    user = Users.find_by_id(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'Usuário não encontrado.'}), 404
    
    if user.last_login:
        return jsonify({'success': False, 'message': 'Usuário já acessou o sistema.'}), 400
    
    try:
        # Cria token de reset de senha para o primeiro acesso
        token = user.generate_password_reset_token()
        db.session.commit()
        
        # TODO: Implementar envio de e-mail real
        # Por enquanto, simula o envio
        # from apps.messaging.services import send_email
        # send_email(
        #     to=user.email,
        #     subject='Convite para acessar o sistema',
        #     template='emails/invite.html',
        #     user=user,
        #     token=token
        # )
        
        AuditLog.log(
            action='user.invite_sent',
            table_name='user',
            record_id=user.id,
            description=f'Convite enviado para {user.email}',
            user_id=current_user.id
        )
        
        return jsonify({
            'success': True, 
            'message': f'Convite enviado para {user.email}'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@blueprint.route('/termos-de-uso', methods=['GET', 'POST'])
@login_required
@admin_required
def terms_settings():
    """Configurações de termos de uso e consentimento"""
    from apps.settings.models import SystemSettings
    
    if request.method == 'POST':
        try:
            SystemSettings.set('terms_of_use', request.form.get('terms_of_use', ''))
            SystemSettings.set('privacy_policy', request.form.get('privacy_policy', ''))
            SystemSettings.set('terms_version', request.form.get('terms_version', '1.0'))
            SystemSettings.set('require_terms_acceptance', 
                              'true' if request.form.get('require_terms_acceptance') else 'false')
            
            AuditLog.log(
                action='settings.terms_updated',
                table_name='system_settings',
                description='Termos de uso atualizados',
                user_id=current_user.id
            )
            
            flash('Termos de uso atualizados com sucesso!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao salvar: {str(e)}', 'danger')
    
    # Carrega configurações atuais
    settings = {
        'terms_of_use': SystemSettings.get('terms_of_use', ''),
        'privacy_policy': SystemSettings.get('privacy_policy', ''),
        'terms_version': SystemSettings.get('terms_version', '1.0'),
        'require_terms_acceptance': SystemSettings.get('require_terms_acceptance', 'false') == 'true'
    }
    
    return render_template('admin/terms/settings.html', settings=settings)


# =============================================================================
# CONVITES
# =============================================================================

@blueprint.route('/convites')
@login_required
@permission_required('users.invite')
def invitations_list():
    """Lista de convites"""
    
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    
    query = UserInvitation.query_active()
    
    if status == 'pending':
        query = query.filter(
            UserInvitation.used_at.is_(None),
            UserInvitation.expires_at > datetime.utcnow()
        )
    elif status == 'used':
        query = query.filter(UserInvitation.used_at.isnot(None))
    elif status == 'expired':
        query = query.filter(
            UserInvitation.used_at.is_(None),
            UserInvitation.expires_at <= datetime.utcnow()
        )
    
    pagination = query.order_by(
        UserInvitation.created_at.desc()
    ).paginate(page=page, per_page=20, error_out=False)
    
    return render_template(
        'admin/invitations/list.html',
        invitations=pagination.items,
        pagination=pagination,
        current_status=status
    )


@blueprint.route('/convites/novo', methods=['GET', 'POST'])
@login_required
@permission_required('users.invite')
def invitations_create():
    """Criar novo convite"""
    
    form = InvitationForm()
    
    # Carrega funcionários sem usuário vinculado
    from apps.hr.models import Employee, EmployeeStatus
    employees = Employee.query_active().filter_by(
        status=EmployeeStatus.ACTIVE,
        user_id=None
    ).order_by(Employee.name).all()
    form.employee_id.choices = [(0, '-- Nenhum --')] + [
        (e.id, e.name) for e in employees
    ]
    
    if form.validate_on_submit():
        try:
            invitation = UserInvitation.create(
                email=form.email.data,
                invited_by_id=current_user.id,
                group_id=form.group_id.data if form.group_id.data else None,
                employee_id=form.employee_id.data if form.employee_id.data else None,
                name=form.name.data,
                message=form.message.data,
                expires_hours=form.expires_hours.data
            )
            
            AuditLog.log(
                action='invitation.created',
                table_name='invitation',
                record_id=invitation.id,
                description=f'Convite enviado para {form.email.data}',
                user_id=current_user.id
            )
            
            # TODO: Enviar e-mail com o convite
            # invite_url = url_for('authentication_blueprint.register_invite', 
            #                      token=invitation.token, _external=True)
            
            flash('Convite criado com sucesso!', 'success')
            return redirect(url_for('admin_blueprint.invitations_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar convite: {str(e)}', 'danger')
    
    return render_template('admin/invitations/form.html', form=form)


@blueprint.route('/convites/<int:invitation_id>/cancelar', methods=['POST'])
@login_required
@permission_required('users.invite')
def invitations_cancel(invitation_id):
    """Cancelar convite"""
    
    invitation = UserInvitation.query_active().filter_by(id=invitation_id).first()
    if not invitation:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Convite não encontrado.'}), 404
        flash('Convite não encontrado.', 'warning')
        return redirect(url_for('admin_blueprint.invitations_list'))
    
    if invitation.is_used:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Este convite já foi utilizado.'}), 400
        flash('Este convite já foi utilizado.', 'warning')
        return redirect(url_for('admin_blueprint.invitations_list'))
    
    try:
        invitation.soft_delete(current_user.id)
        
        AuditLog.log(
            action='invitation.cancelled',
            table_name='invitation',
            record_id=invitation.id,
            description=f'Convite para {invitation.email} cancelado',
            user_id=current_user.id
        )
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': 'Convite cancelado com sucesso!'})
        
        flash('Convite cancelado com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': str(e)}), 500
        flash(f'Erro ao cancelar convite: {str(e)}', 'danger')
    
    return redirect(url_for('admin_blueprint.invitations_list'))


@blueprint.route('/convites/<int:invitation_id>/reenviar', methods=['POST'])
@login_required
@permission_required('users.invite')
def invitations_resend(invitation_id):
    """Reenviar convite"""
    
    invitation = UserInvitation.query_active().filter_by(id=invitation_id).first()
    if not invitation:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Convite não encontrado.'}), 404
        flash('Convite não encontrado.', 'warning')
        return redirect(url_for('admin_blueprint.invitations_list'))
    
    if invitation.is_used:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Este convite já foi utilizado.'}), 400
        flash('Este convite já foi utilizado.', 'warning')
        return redirect(url_for('admin_blueprint.invitations_list'))
    
    try:
        # Cria novo convite com mesmos dados
        new_invitation = UserInvitation.create(
            email=invitation.email,
            invited_by_id=current_user.id,
            group_id=invitation.group_id,
            employee_id=invitation.employee_id,
            name=invitation.name,
            message=invitation.message,
            expires_hours=72
        )
        
        # Cancela o antigo
        invitation.soft_delete(current_user.id)
        
        AuditLog.log(
            action='invitation.resent',
            table_name='invitation',
            record_id=new_invitation.id,
            description=f'Convite reenviado para {invitation.email}',
            user_id=current_user.id
        )
        
        # TODO: Reenviar e-mail
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': 'Convite reenviado com sucesso!'})
        
        flash('Convite reenviado com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': str(e)}), 500
        flash(f'Erro ao reenviar convite: {str(e)}', 'danger')
    
    return redirect(url_for('admin_blueprint.invitations_list'))


# =============================================================================
# GRUPOS
# =============================================================================

@blueprint.route('/grupos')
@login_required
@permission_required('groups.view')
def groups_list():
    """Lista de grupos"""
    
    groups = UserGroup.query_active().order_by(UserGroup.name).all()
    
    return render_template('admin/groups/list.html', groups=groups)


@blueprint.route('/grupos/novo', methods=['GET', 'POST'])
@login_required
@permission_required('groups.create')
def groups_create():
    """Criar novo grupo"""
    
    form = UserGroupForm()
    
    # Carrega permissões agrupadas
    permissions = Permission.get_all_grouped()
    form.permissions.choices = [
        (p.id, p.name) for p_list in permissions.values() for p in p_list
    ]
    
    if form.validate_on_submit():
        try:
            group = UserGroup(
                name=form.name.data,
                description=form.description.data,
                is_active=form.is_active.data
            )
            
            db.session.add(group)
            db.session.flush()
            
            # Adiciona permissões
            for perm_id in form.permissions.data:
                perm = Permission.query.get(perm_id)
                if perm:
                    group.permissions.append(perm)
            
            db.session.commit()
            
            AuditLog.log(
                action='group.created',
                table_name='group',
                record_id=group.id,
                description=f'Grupo {group.name} criado',
                user_id=current_user.id
            )
            
            flash('Grupo criado com sucesso!', 'success')
            return redirect(url_for('admin_blueprint.groups_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar grupo: {str(e)}', 'danger')
    
    return render_template(
        'admin/groups/form.html', 
        form=form, 
        is_new=True,
        permissions_grouped=permissions
    )


@blueprint.route('/grupos/<int:group_id>')
@login_required
@permission_required('groups.view')
def groups_view(group_id):
    """Visualizar detalhes do grupo"""
    
    group = UserGroup.query_active().filter_by(id=group_id).first()
    if not group:
        flash('Grupo não encontrado.', 'warning')
        return redirect(url_for('admin_blueprint.groups_list'))
    
    # Membros do grupo - especificando explicitamente a condição de join
    members = Users.query_active().join(
        UserGroupMembership, 
        Users.id == UserGroupMembership.user_id
    ).filter(
        UserGroupMembership.group_id == group.id,
        UserGroupMembership.deleted_at.is_(None)
    ).order_by(Users.username).all()
    
    return render_template(
        'admin/groups/view.html',
        group=group,
        members=members
    )


@blueprint.route('/grupos/<int:group_id>/editar', methods=['GET', 'POST'])
@login_required
@permission_required('groups.edit')
def groups_edit(group_id):
    """Editar grupo"""
    
    group = UserGroup.query_active().filter_by(id=group_id).first()
    if not group:
        flash('Grupo não encontrado.', 'warning')
        return redirect(url_for('admin_blueprint.groups_list'))
    
    if group.is_system:
        flash('Grupos do sistema não podem ser editados.', 'warning')
        return redirect(url_for('admin_blueprint.groups_view', group_id=group.id))
    
    form = UserGroupForm(obj=group)
    
    # Carrega permissões agrupadas
    permissions = Permission.get_all_grouped()
    form.permissions.choices = [
        (p.id, p.name) for p_list in permissions.values() for p in p_list
    ]
    
    if request.method == 'GET':
        form.permissions.data = [p.id for p in group.permissions]
    
    if form.validate_on_submit():
        try:
            group.name = form.name.data
            group.description = form.description.data
            group.is_active = form.is_active.data
            
            # Atualiza permissões
            group.permissions = []
            for perm_id in form.permissions.data:
                perm = Permission.query.get(perm_id)
                if perm:
                    group.permissions.append(perm)
            
            db.session.commit()
            
            AuditLog.log(
                action='group.updated',
                table_name='group',
                record_id=group.id,
                description=f'Grupo {group.name} atualizado',
                user_id=current_user.id
            )
            
            flash('Grupo atualizado com sucesso!', 'success')
            return redirect(url_for('admin_blueprint.groups_view', group_id=group.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar grupo: {str(e)}', 'danger')
    
    return render_template(
        'admin/groups/form.html', 
        form=form, 
        group=group,
        is_new=False,
        permissions_grouped=permissions
    )


@blueprint.route('/grupos/<int:group_id>/excluir', methods=['POST'])
@login_required
@permission_required('groups.delete')
def groups_delete(group_id):
    """Excluir grupo (soft delete)"""
    
    group = UserGroup.query_active().filter_by(id=group_id).first()
    if not group:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Grupo não encontrado.'}), 404
        flash('Grupo não encontrado.', 'warning')
        return redirect(url_for('admin_blueprint.groups_list'))
    
    if group.is_system:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Grupos do sistema não podem ser excluídos.'}), 400
        flash('Grupos do sistema não podem ser excluídos.', 'warning')
        return redirect(url_for('admin_blueprint.groups_list'))
    
    try:
        group.soft_delete(current_user.id)
        
        AuditLog.log(
            action='group.deleted',
            table_name='group',
            record_id=group.id,
            description=f'Grupo {group.name} excluído',
            user_id=current_user.id
        )
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': 'Grupo excluído com sucesso!'})
        
        flash('Grupo excluído com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': str(e)}), 500
        flash(f'Erro ao excluir grupo: {str(e)}', 'danger')
    
    return redirect(url_for('admin_blueprint.groups_list'))


# =============================================================================
# PERMISSÕES
# =============================================================================

@blueprint.route('/permissoes')
@login_required
@admin_required
def permissions_list():
    """Lista de permissões (somente visualização)"""
    
    permissions = Permission.get_all_grouped()
    
    return render_template('admin/permissions/list.html', permissions_grouped=permissions)


# =============================================================================
# AUDITORIA
# =============================================================================

@blueprint.route('/auditoria')
@login_required
@permission_required('audit.view')
def audit_list():
    """Lista de logs de auditoria"""
    
    page = request.args.get('page', 1, type=int)
    user_id = request.args.get('user_id', type=int)
    action = request.args.get('action', '')
    entity_type = request.args.get('entity_type', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    query = AuditLog.query
    
    if user_id:
        query = query.filter_by(user_id=user_id)
    
    if action:
        query = query.filter(AuditLog.action.ilike(f'%{action}%'))
    
    if entity_type:
        query = query.filter_by(table_name=entity_type)
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(AuditLog.created_at >= date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            date_to_obj = date_to_obj.replace(hour=23, minute=59, second=59)
            query = query.filter(AuditLog.created_at <= date_to_obj)
        except ValueError:
            pass
    
    pagination = query.order_by(
        AuditLog.created_at.desc()
    ).paginate(page=page, per_page=50, error_out=False)
    
    # Tipos de entidade únicos para filtro
    entity_types = db.session.query(AuditLog.table_name).distinct().all()
    entity_types = [e[0] for e in entity_types if e[0]]
    
    # Usuários para filtro
    users = Users.query_active().order_by(Users.username).all()
    
    return render_template(
        'admin/audit/list.html',
        logs=pagination.items,
        pagination=pagination,
        entity_types=entity_types,
        users=users,
        filters={
            'user_id': user_id,
            'action': action,
            'entity_type': entity_type,
            'date_from': date_from,
            'date_to': date_to
        }
    )


@blueprint.route('/auditoria/<int:log_id>')
@login_required
@permission_required('audit.view')
def audit_view(log_id):
    """Visualizar detalhes de um log de auditoria"""
    
    log = AuditLog.query.get_or_404(log_id)
    
    return render_template('admin/audit/view.html', log=log)


# =============================================================================
# HISTÓRICO DE LOGIN
# =============================================================================

@blueprint.route('/logins')
@login_required
@permission_required('audit.view')
def login_history():
    """Histórico de logins"""
    
    page = request.args.get('page', 1, type=int)
    user_id = request.args.get('user_id', type=int)
    success = request.args.get('success', '')
    
    query = LoginHistory.query
    
    if user_id:
        query = query.filter_by(user_id=user_id)
    
    if success == '1':
        query = query.filter_by(success=True)
    elif success == '0':
        query = query.filter_by(success=False)
    
    pagination = query.order_by(
        LoginHistory.created_at.desc()
    ).paginate(page=page, per_page=50, error_out=False)
    
    users = Users.query_active().order_by(Users.username).all()
    
    return render_template(
        'admin/login_history/list.html',
        logs=pagination.items,
        pagination=pagination,
        users=users,
        filters={
            'user_id': user_id,
            'success': success
        }
    )


# =============================================================================
# INICIALIZAÇÃO DE PERMISSÕES E GRUPOS
# =============================================================================

@blueprint.route('/inicializar-permissoes', methods=['POST'])
@login_required
@admin_required
def init_permissions():
    """Inicializa permissões e grupos padrão do sistema"""
    
    try:
        created_perms = 0
        created_groups = 0
        
        # Cria permissões
        for perm_data in DEFAULT_PERMISSIONS:
            existing = Permission.get_by_code(perm_data['code'])
            if not existing:
                perm = Permission(**perm_data)
                db.session.add(perm)
                created_perms += 1
        
        db.session.flush()
        
        # Cria grupos
        for group_data in DEFAULT_GROUPS:
            existing = UserGroup.query.filter_by(name=group_data['name']).first()
            if not existing:
                group = UserGroup(
                    name=group_data['name'],
                    description=group_data['description'],
                    is_system=group_data.get('is_system', False)
                )
                db.session.add(group)
                db.session.flush()
                
                # Adiciona permissões
                perm_codes = group_data.get('permissions', [])
                if '*' in perm_codes:
                    # Todas as permissões
                    group.permissions = Permission.query.all()
                else:
                    for code in perm_codes:
                        perm = Permission.get_by_code(code)
                        if perm:
                            group.permissions.append(perm)
                
                created_groups += 1
        
        db.session.commit()
        
        AuditLog.log(
            action='system.permissions_initialized',
            table_name='system',
            record_id=0,
            description=f'Permissões inicializadas: {created_perms} permissões, {created_groups} grupos',
            user_id=current_user.id
        )
        
        flash(f'Inicialização concluída! {created_perms} permissões e {created_groups} grupos criados.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro na inicialização: {str(e)}', 'danger')
    
    return redirect(url_for('admin_blueprint.index'))
