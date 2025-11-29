# -*- encoding: utf-8 -*-
"""
Decoradores de Autenticação e Autorização
"""

from functools import wraps
from flask import abort, flash, redirect, url_for, request, jsonify
from flask_login import current_user, login_required


def permission_required(*permission_codes, require_all=False):
    """
    Decorador que verifica se o usuário tem as permissões necessárias.
    
    Args:
        *permission_codes: Códigos das permissões necessárias
        require_all: Se True, requer todas as permissões. Se False, requer pelo menos uma.
    
    Exemplo:
        @permission_required('users.create')
        def create_user():
            ...
        
        @permission_required('users.edit', 'users.delete', require_all=True)
        def manage_user():
            ...
    """
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            # Administradores sempre têm acesso
            if current_user.is_admin:
                return f(*args, **kwargs)
            
            # Verifica permissões
            if require_all:
                has_access = current_user.has_all_permissions(permission_codes)
            else:
                has_access = current_user.has_any_permission(permission_codes)
            
            if not has_access:
                # Se for requisição AJAX, retorna JSON
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        'success': False,
                        'error': 'Você não tem permissão para realizar esta ação.'
                    }), 403
                
                flash('Você não tem permissão para acessar esta página.', 'danger')
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """
    Decorador que verifica se o usuário é administrador.
    
    Exemplo:
        @admin_required
        def admin_panel():
            ...
    """
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': False,
                    'error': 'Acesso restrito a administradores.'
                }), 403
            
            flash('Acesso restrito a administradores.', 'danger')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function


def group_required(*group_names):
    """
    Decorador que verifica se o usuário pertence a um dos grupos especificados.
    
    Args:
        *group_names: Nomes dos grupos permitidos
    
    Exemplo:
        @group_required('Administradores', 'Gerentes')
        def managers_only():
            ...
    """
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            # Administradores sempre têm acesso
            if current_user.is_admin:
                return f(*args, **kwargs)
            
            # Verifica grupos
            user_group_names = [g.name for g in current_user.user_groups]
            has_access = any(name in user_group_names for name in group_names)
            
            if not has_access:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        'success': False,
                        'error': 'Você não tem permissão para realizar esta ação.'
                    }), 403
                
                flash('Você não tem permissão para acessar esta página.', 'danger')
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def active_required(f):
    """
    Decorador que verifica se a conta do usuário está ativa.
    
    Exemplo:
        @active_required
        def some_action():
            ...
    """
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_active:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': False,
                    'error': 'Sua conta está desativada.'
                }), 403
            
            flash('Sua conta está desativada. Entre em contato com o administrador.', 'warning')
            return redirect(url_for('authentication_blueprint.logout'))
        
        return f(*args, **kwargs)
    return decorated_function


def unlocked_required(f):
    """
    Decorador que verifica se a conta do usuário não está bloqueada.
    
    Exemplo:
        @unlocked_required
        def some_action():
            ...
    """
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.is_locked:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': False,
                    'error': f'Sua conta está bloqueada. Tente novamente em {current_user.lock_remaining_minutes} minutos.'
                }), 403
            
            flash(f'Sua conta está bloqueada. Tente novamente em {current_user.lock_remaining_minutes} minutos.', 'warning')
            return redirect(url_for('authentication_blueprint.logout'))
        
        return f(*args, **kwargs)
    return decorated_function


def api_permission_required(*permission_codes, require_all=False):
    """
    Decorador para APIs que verifica permissões e retorna JSON.
    
    Args:
        *permission_codes: Códigos das permissões necessárias
        require_all: Se True, requer todas as permissões
    
    Exemplo:
        @api_permission_required('users.create')
        def api_create_user():
            ...
    """
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({
                    'success': False,
                    'error': 'Autenticação necessária.'
                }), 401
            
            if current_user.is_admin:
                return f(*args, **kwargs)
            
            if require_all:
                has_access = current_user.has_all_permissions(permission_codes)
            else:
                has_access = current_user.has_any_permission(permission_codes)
            
            if not has_access:
                return jsonify({
                    'success': False,
                    'error': 'Permissão negada.'
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def owner_or_permission(owner_field='user_id', permission_code=None):
    """
    Decorador que permite acesso se o usuário é o dono do recurso
    ou tem a permissão especificada.
    
    Args:
        owner_field: Nome do campo que contém o ID do dono
        permission_code: Código da permissão alternativa
    
    Exemplo:
        @owner_or_permission(owner_field='created_by_id', permission_code='posts.edit_any')
        def edit_post(post_id):
            post = Post.query.get(post_id)
            ...
    """
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if current_user.is_admin:
                return f(*args, **kwargs)
            
            # Tenta obter o objeto do primeiro argumento nomeado
            # ou do retorno de um método get_object
            obj = kwargs.get('obj')
            
            if obj and hasattr(obj, owner_field):
                owner_id = getattr(obj, owner_field)
                if owner_id == current_user.id:
                    return f(*args, **kwargs)
            
            # Verifica permissão alternativa
            if permission_code and current_user.has_permission(permission_code):
                return f(*args, **kwargs)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': False,
                    'error': 'Você não tem permissão para realizar esta ação.'
                }), 403
            
            flash('Você não tem permissão para acessar este recurso.', 'danger')
            abort(403)
        
        return decorated_function
    return decorator


class PermissionContext:
    """
    Contexto para verificar permissões em templates.
    
    Uso no template:
        {% if perm.can('users.create') %}
            <button>Criar Usuário</button>
        {% endif %}
    """
    
    def __init__(self, user):
        self.user = user
    
    def can(self, permission_code):
        """Verifica se pode realizar a ação"""
        if not self.user or not self.user.is_authenticated:
            return False
        return self.user.has_permission(permission_code)
    
    def can_any(self, *permission_codes):
        """Verifica se pode realizar pelo menos uma das ações"""
        if not self.user or not self.user.is_authenticated:
            return False
        return self.user.has_any_permission(permission_codes)
    
    def can_all(self, *permission_codes):
        """Verifica se pode realizar todas as ações"""
        if not self.user or not self.user.is_authenticated:
            return False
        return self.user.has_all_permissions(permission_codes)
    
    @property
    def is_admin(self):
        """Verifica se é administrador"""
        if not self.user or not self.user.is_authenticated:
            return False
        return self.user.is_admin
    
    def in_group(self, group_name):
        """Verifica se está em um grupo"""
        if not self.user or not self.user.is_authenticated:
            return False
        return group_name in [g.name for g in self.user.user_groups]


def inject_permission_context():
    """
    Context processor para injetar contexto de permissões em templates.
    
    Uso:
        app.context_processor(inject_permission_context)
    """
    from flask_login import current_user
    return dict(perm=PermissionContext(current_user))
