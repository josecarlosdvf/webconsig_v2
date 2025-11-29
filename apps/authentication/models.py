# -*- encoding: utf-8 -*-
"""
Models de Autenticação
Usuários, Grupos, Permissões, Histórico de Login, Convites
"""

import secrets
from datetime import datetime, timedelta
from flask import request, has_request_context
from flask_login import UserMixin
from sqlalchemy.exc import SQLAlchemyError

from apps import db, login_manager
from apps.authentication.util import hash_password, verify_password
from apps.database.models import BaseModel, TimestampMixin, SoftDeleteMixin, audited


# =============================================================================
# ENUMS E CONSTANTES
# =============================================================================

class LoginTypeAllowed:
    """Tipos de login permitidos"""
    USERNAME = 'username'
    EMAIL = 'email'
    BOTH = 'both'
    
    CHOICES = [
        (USERNAME, 'Apenas usuário'),
        (EMAIL, 'Apenas e-mail'),
        (BOTH, 'Usuário ou e-mail')
    ]


# =============================================================================
# PERMISSÕES
# =============================================================================

@audited
class Permission(db.Model, TimestampMixin):
    """
    Permissão do sistema.
    Define ações específicas que podem ser atribuídas a grupos.
    """
    
    __tablename__ = 'permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Identificação
    code = db.Column(
        db.String(100), 
        unique=True, 
        nullable=False,
        index=True,
        comment='Código único (ex: users.create, employees.delete)'
    )
    name = db.Column(
        db.String(100), 
        nullable=False,
        comment='Nome de exibição'
    )
    description = db.Column(
        db.String(255), 
        nullable=True,
        comment='Descrição da permissão'
    )
    
    # Agrupamento
    module = db.Column(
        db.String(50), 
        nullable=False,
        index=True,
        comment='Módulo do sistema (users, employees, settings, etc)'
    )
    
    def __repr__(self):
        return f'<Permission {self.code}>'
    
    @classmethod
    def get_by_code(cls, code):
        """Busca permissão por código"""
        return cls.query.filter_by(code=code).first()
    
    @classmethod
    def get_by_module(cls, module):
        """Retorna permissões de um módulo"""
        return cls.query.filter_by(module=module).order_by(cls.name).all()
    
    @classmethod
    def get_all_grouped(cls):
        """Retorna todas as permissões agrupadas por módulo"""
        permissions = cls.query.order_by(cls.module, cls.name).all()
        grouped = {}
        for p in permissions:
            if p.module not in grouped:
                grouped[p.module] = []
            grouped[p.module].append(p)
        return grouped


# =============================================================================
# GRUPOS DE USUÁRIOS
# =============================================================================

# Tabela de associação Grupo <-> Permissão
group_permissions = db.Table(
    'group_permissions',
    db.Column('group_id', db.Integer, db.ForeignKey('user_groups.id'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permissions.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)


@audited
class UserGroup(db.Model, BaseModel):
    """
    Grupo de usuários para controle de acesso (RBAC).
    Grupos possuem permissões que são herdadas pelos usuários membros.
    """
    
    __tablename__ = 'user_groups'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Identificação
    name = db.Column(
        db.String(64), 
        unique=True, 
        nullable=False,
        comment='Nome do grupo'
    )
    description = db.Column(
        db.String(255), 
        nullable=True,
        comment='Descrição do grupo'
    )
    
    # Configurações
    is_active = db.Column(
        db.Boolean, 
        default=True,
        comment='Se o grupo está ativo'
    )
    is_system = db.Column(
        db.Boolean, 
        default=False,
        comment='Se é um grupo do sistema (não pode ser excluído)'
    )
    
    # Relacionamentos
    permissions = db.relationship(
        'Permission',
        secondary=group_permissions,
        backref=db.backref('groups', lazy='dynamic')
    )
    members = db.relationship(
        'UserGroupMembership', 
        backref='group', 
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    
    def __repr__(self):
        return f'<UserGroup {self.name}>'
    
    @property
    def member_count(self):
        """Número de membros ativos"""
        return self.members.join(
            Users, 
            UserGroupMembership.user_id == Users.id
        ).filter(
            Users.is_active == True,
            UserGroupMembership.deleted_at.is_(None)
        ).count()
    
    @property
    def permission_codes(self):
        """Lista de códigos de permissões"""
        return [p.code for p in self.permissions]
    
    def has_permission(self, permission_code):
        """Verifica se o grupo tem uma permissão"""
        return permission_code in self.permission_codes
    
    def add_permission(self, permission):
        """Adiciona uma permissão ao grupo"""
        if permission not in self.permissions:
            self.permissions.append(permission)
            db.session.commit()
    
    def remove_permission(self, permission):
        """Remove uma permissão do grupo"""
        if permission in self.permissions:
            self.permissions.remove(permission)
            db.session.commit()
    
    def set_permissions(self, permission_codes):
        """Define as permissões do grupo por lista de códigos"""
        permissions = Permission.query.filter(
            Permission.code.in_(permission_codes)
        ).all()
        self.permissions = permissions
        db.session.commit()
    
    @classmethod
    def get_active(cls):
        """Retorna grupos ativos"""
        return cls.query_active().filter_by(is_active=True).order_by(cls.name).all()


# =============================================================================
# ASSOCIAÇÃO USUÁRIO <-> GRUPO
# =============================================================================

class UserGroupMembership(db.Model, TimestampMixin, SoftDeleteMixin):
    """
    Associação entre usuário e grupo.
    Permite soft delete para manter histórico.
    """
    
    __tablename__ = 'user_group_memberships'
    
    id = db.Column(db.Integer, primary_key=True)
    
    user_id = db.Column(
        db.Integer, 
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    group_id = db.Column(
        db.Integer, 
        db.ForeignKey('user_groups.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Quem adicionou ao grupo
    added_by_id = db.Column(
        db.Integer, 
        db.ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True
    )
    
    # Constraint única
    __table_args__ = (
        db.UniqueConstraint('user_id', 'group_id', name='unique_user_group'),
    )
    
    def __repr__(self):
        return f'<UserGroupMembership user={self.user_id} group={self.group_id}>'


# =============================================================================
# HISTÓRICO DE LOGIN
# =============================================================================

class LoginHistory(db.Model, TimestampMixin):
    """
    Histórico de tentativas de login.
    Registra todas as tentativas (sucesso e falha) para auditoria.
    """
    
    __tablename__ = 'login_history'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Usuário (pode ser nulo se login falhou com usuário inexistente)
    user_id = db.Column(
        db.Integer, 
        db.ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    
    # O que foi digitado no campo de usuário
    username_attempted = db.Column(
        db.String(120), 
        nullable=False,
        comment='Username ou email tentado'
    )
    
    # Resultado
    success = db.Column(
        db.Boolean, 
        default=False,
        index=True,
        comment='Se o login foi bem-sucedido'
    )
    failure_reason = db.Column(
        db.String(50), 
        nullable=True,
        comment='Motivo da falha: invalid_password, account_locked, account_inactive, user_not_found'
    )
    
    # Contexto
    ip_address = db.Column(
        db.String(45), 
        nullable=True,
        comment='Endereço IP'
    )
    user_agent = db.Column(
        db.String(500), 
        nullable=True,
        comment='User-Agent do navegador'
    )
    location = db.Column(
        db.String(200), 
        nullable=True,
        comment='Localização aproximada (se disponível)'
    )
    
    # Relacionamento
    user = db.relationship('Users', backref=db.backref('login_history', lazy='dynamic'))
    
    def __repr__(self):
        status = 'success' if self.success else 'failed'
        return f'<LoginHistory {self.username_attempted} {status}>'
    
    @classmethod
    def log(cls, username, success, user=None, failure_reason=None):
        """
        Registra uma tentativa de login.
        
        Args:
            username: Username ou email tentado
            success: Se foi bem-sucedido
            user: Usuário (se encontrado)
            failure_reason: Motivo da falha
        
        Returns:
            LoginHistory: Registro criado
        """
        ip_address = None
        user_agent = None
        
        if has_request_context():
            ip_address = request.remote_addr
            user_agent = request.user_agent.string[:500] if request.user_agent else None
        
        entry = cls(
            user_id=user.id if user else None,
            username_attempted=username,
            success=success,
            failure_reason=failure_reason,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.session.add(entry)
        # Não faz commit para permitir transações
        
        return entry
    
    @classmethod
    def get_recent_failures(cls, user_id=None, ip_address=None, minutes=30):
        """
        Conta tentativas de login falhas recentes.
        
        Args:
            user_id: ID do usuário
            ip_address: Endereço IP
            minutes: Janela de tempo em minutos
        
        Returns:
            int: Número de tentativas falhas
        """
        since = datetime.utcnow() - timedelta(minutes=minutes)
        
        query = cls.query.filter(
            cls.success == False,
            cls.created_at >= since
        )
        
        if user_id:
            query = query.filter(cls.user_id == user_id)
        elif ip_address:
            query = query.filter(cls.ip_address == ip_address)
        else:
            return 0
        
        return query.count()
    
    @classmethod
    def get_user_history(cls, user_id, limit=50):
        """Retorna histórico de login de um usuário"""
        return cls.query.filter_by(user_id=user_id).order_by(
            cls.created_at.desc()
        ).limit(limit).all()


# =============================================================================
# CONVITES
# =============================================================================

@audited
class UserInvitation(db.Model, BaseModel):
    """
    Convite para registro de usuário.
    Permite convidar novos usuários por e-mail com pré-configuração de grupo.
    """
    
    __tablename__ = 'user_invitations'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Dados do convite
    email = db.Column(
        db.String(120), 
        nullable=False,
        index=True,
        comment='E-mail do convidado'
    )
    name = db.Column(
        db.String(100), 
        nullable=True,
        comment='Nome do convidado (opcional)'
    )
    token = db.Column(
        db.String(64), 
        unique=True, 
        nullable=False,
        index=True,
        comment='Token único para o link de convite'
    )
    
    # Quem convidou
    invited_by_id = db.Column(
        db.Integer, 
        db.ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True
    )
    
    # Pré-configuração
    group_id = db.Column(
        db.Integer, 
        db.ForeignKey('user_groups.id', ondelete='SET NULL'),
        nullable=True,
        comment='Grupo padrão para o novo usuário'
    )
    employee_id = db.Column(
        db.Integer, 
        db.ForeignKey('employees.id', ondelete='SET NULL'),
        nullable=True,
        comment='Funcionário a vincular (se aplicável)'
    )
    
    # Validade
    expires_at = db.Column(
        db.DateTime, 
        nullable=False,
        comment='Data de expiração do convite'
    )
    
    # Uso
    used_at = db.Column(
        db.DateTime, 
        nullable=True,
        comment='Data em que foi usado'
    )
    user_id = db.Column(
        db.Integer, 
        db.ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        comment='ID do usuário criado (se usado)'
    )
    
    # Mensagem personalizada
    message = db.Column(
        db.Text, 
        nullable=True,
        comment='Mensagem personalizada no convite'
    )
    
    # Relacionamentos
    invited_by = db.relationship(
        'Users', 
        foreign_keys=[invited_by_id],
        backref='invitations_sent'
    )
    group = db.relationship('UserGroup')
    user = db.relationship(
        'Users', 
        foreign_keys=[user_id],
        backref='invitation'
    )
    
    def __repr__(self):
        return f'<UserInvitation {self.email}>'
    
    @property
    def is_expired(self):
        """Verifica se o convite expirou"""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_used(self):
        """Verifica se o convite foi usado"""
        return self.used_at is not None
    
    @property
    def is_valid(self):
        """Verifica se o convite é válido (não expirado e não usado)"""
        return not self.is_expired and not self.is_used and not self.is_deleted
    
    def mark_used(self, user):
        """Marca o convite como usado"""
        self.used_at = datetime.utcnow()
        self.user_id = user.id
        db.session.commit()
    
    @classmethod
    def create(cls, email, invited_by_id, group_id=None, employee_id=None, 
               name=None, message=None, expires_hours=72):
        """
        Cria um novo convite.
        
        Args:
            email: E-mail do convidado
            invited_by_id: ID do usuário que convidou
            group_id: ID do grupo padrão
            employee_id: ID do funcionário a vincular
            name: Nome do convidado
            message: Mensagem personalizada
            expires_hours: Horas até expirar
        
        Returns:
            UserInvitation: Convite criado
        """
        invitation = cls(
            email=email.lower().strip(),
            name=name,
            token=secrets.token_urlsafe(32),
            invited_by_id=invited_by_id,
            group_id=group_id,
            employee_id=employee_id,
            message=message,
            expires_at=datetime.utcnow() + timedelta(hours=expires_hours)
        )
        
        db.session.add(invitation)
        db.session.commit()
        
        return invitation
    
    @classmethod
    def get_by_token(cls, token):
        """Busca convite por token"""
        return cls.query_active().filter_by(token=token).first()
    
    @classmethod
    def get_pending_for_email(cls, email):
        """Busca convites pendentes para um e-mail"""
        return cls.query_active().filter(
            cls.email == email.lower().strip(),
            cls.used_at.is_(None),
            cls.expires_at > datetime.utcnow()
        ).order_by(cls.created_at.desc()).first()


# =============================================================================
# USUÁRIO
# =============================================================================

@audited
class Users(db.Model, UserMixin, BaseModel):
    """
    Model de Usuário do sistema.
    Inclui autenticação, controle de sessão, bloqueio de conta e vinculação com funcionário.
    """
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # =============================
    # AUTENTICAÇÃO
    # =============================
    
    username = db.Column(
        db.String(64), 
        unique=True, 
        nullable=False, 
        index=True,
        comment='Nome de usuário único'
    )
    email = db.Column(
        db.String(120), 
        unique=True, 
        nullable=False, 
        index=True,
        comment='E-mail único'
    )
    password = db.Column(
        db.LargeBinary, 
        nullable=False,
        comment='Hash da senha'
    )
    
    # Tipo de login permitido
    login_type_allowed = db.Column(
        db.String(20), 
        nullable=False,
        default=LoginTypeAllowed.BOTH,
        comment='Tipo de login permitido: username, email, both'
    )
    
    # =============================
    # INFORMAÇÕES PESSOAIS
    # =============================
    
    first_name = db.Column(db.String(64), nullable=True)
    last_name = db.Column(db.String(64), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    avatar_url = db.Column(db.String(255), nullable=True)
    
    # =============================
    # STATUS E PERMISSÕES
    # =============================
    
    is_active = db.Column(
        db.Boolean, 
        default=True,
        comment='Se a conta está ativa'
    )
    is_admin = db.Column(
        db.Boolean, 
        default=False,
        comment='Se é administrador do sistema'
    )
    
    # =============================
    # CONTROLE DE SESSÃO
    # =============================
    
    session_token = db.Column(
        db.String(64), 
        nullable=True, 
        index=True,
        comment='Token de sessão única'
    )
    last_login = db.Column(
        db.DateTime, 
        nullable=True,
        comment='Data do último login'
    )
    
    # =============================
    # BLOQUEIO DE CONTA
    # =============================
    
    failed_login_attempts = db.Column(
        db.Integer, 
        default=0,
        comment='Tentativas de login falhas consecutivas'
    )
    locked_until = db.Column(
        db.DateTime, 
        nullable=True,
        comment='Conta bloqueada até esta data'
    )
    
    # =============================
    # RESET DE SENHA
    # =============================
    
    password_reset_token = db.Column(
        db.String(64), 
        nullable=True,
        comment='Token para reset de senha'
    )
    password_reset_expires = db.Column(
        db.DateTime, 
        nullable=True,
        comment='Expiração do token de reset'
    )
    
    # =============================
    # VINCULAÇÃO COM FUNCIONÁRIO
    # =============================
    
    # Nota: O campo employee_id está definido no modelo Employee
    # para evitar importação circular
    
    # =============================
    # TERMOS DE USO
    # =============================
    
    terms_accepted_at = db.Column(
        db.DateTime, 
        nullable=True,
        comment='Data de aceite dos termos de uso'
    )
    terms_version = db.Column(
        db.String(20), 
        nullable=True,
        comment='Versão dos termos aceitos'
    )
    
    # =============================
    # RELACIONAMENTOS
    # =============================
    
    groups = db.relationship(
        'UserGroupMembership',
        backref='user',
        lazy='dynamic',
        foreign_keys='UserGroupMembership.user_id'
    )
    
    # Campos que não podem ser editados pelo usuário
    readonly_fields = ['id', 'username', 'email', 'created_at', 'is_admin']
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(value, '__iter__') and not isinstance(value, str):
                value = value[0]
            
            if key == 'password':
                value = hash_password(value)
            
            setattr(self, key, value)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    # =============================
    # PROPRIEDADES
    # =============================
    
    @property
    def full_name(self):
        """Retorna nome completo"""
        if self.first_name and self.last_name:
            return f'{self.first_name} {self.last_name}'
        return self.first_name or self.last_name or self.username
    
    @property
    def display_name(self):
        """Nome para exibição"""
        return self.first_name or self.username
    
    @property
    def is_locked(self):
        """Verifica se a conta está bloqueada"""
        if self.locked_until:
            return datetime.utcnow() < self.locked_until
        return False
    
    @property
    def lock_remaining_minutes(self):
        """Minutos restantes de bloqueio"""
        if not self.is_locked:
            return 0
        delta = self.locked_until - datetime.utcnow()
        return max(0, int(delta.total_seconds() / 60))
    
    @property
    def user_groups(self):
        """Retorna grupos ativos do usuário"""
        return [m.group for m in self.groups.filter(
            UserGroupMembership.deleted_at.is_(None)
        ).all() if m.group.is_active]
    
    @property
    def all_permissions(self):
        """Retorna todas as permissões do usuário (de todos os grupos)"""
        if self.is_admin:
            return Permission.query.all()
        
        permissions = set()
        for group in self.user_groups:
            for perm in group.permissions:
                permissions.add(perm)
        return list(permissions)
    
    @property
    def permission_codes(self):
        """Retorna códigos de todas as permissões"""
        if self.is_admin:
            return [p.code for p in Permission.query.all()]
        return [p.code for p in self.all_permissions]
    
    # =============================
    # MÉTODOS DE SENHA
    # =============================
    
    def check_password(self, password: str) -> bool:
        """Verifica se a senha está correta"""
        return verify_password(password, self.password)
    
    def set_password(self, password: str):
        """Define nova senha"""
        self.password = hash_password(password)
        self.password_reset_token = None
        self.password_reset_expires = None
    
    # =============================
    # MÉTODOS DE SESSÃO
    # =============================
    
    def generate_session_token(self):
        """Gera um novo token de sessão único"""
        self.session_token = secrets.token_hex(32)
        self.last_login = datetime.utcnow()
        
        # Garante que o objeto está na sessão e persiste
        try:
            db.session.add(self)
            db.session.flush()
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e
            
        return self.session_token
    
    def invalidate_session(self):
        """Invalida o token de sessão atual"""
        self.session_token = None
        try:
            db.session.add(self)
            db.session.flush()
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e
    
    def verify_session_token(self, token):
        """Verifica se o token de sessão é válido"""
        return self.session_token is not None and self.session_token == token
    
    def update_last_login(self):
        """Atualiza data do último login"""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    # =============================
    # MÉTODOS DE BLOQUEIO
    # =============================
    
    def record_failed_login(self, max_attempts=5, lockout_minutes=30):
        """
        Registra tentativa de login falha.
        
        Args:
            max_attempts: Máximo de tentativas antes de bloquear
            lockout_minutes: Minutos de bloqueio
        
        Returns:
            bool: True se a conta foi bloqueada
        """
        self.failed_login_attempts += 1
        
        if self.failed_login_attempts >= max_attempts:
            self.locked_until = datetime.utcnow() + timedelta(minutes=lockout_minutes)
            db.session.commit()
            return True
        
        db.session.commit()
        return False
    
    def reset_failed_attempts(self):
        """Reseta contador de tentativas falhas após login bem-sucedido"""
        self.failed_login_attempts = 0
        self.locked_until = None
        db.session.commit()
    
    def unlock(self):
        """Desbloqueia a conta manualmente"""
        self.failed_login_attempts = 0
        self.locked_until = None
        db.session.commit()
    
    # =============================
    # MÉTODOS DE RESET DE SENHA
    # =============================
    
    def generate_password_reset_token(self, expires_hours=24):
        """Gera token para reset de senha"""
        self.password_reset_token = secrets.token_urlsafe(32)
        self.password_reset_expires = datetime.utcnow() + timedelta(hours=expires_hours)
        db.session.commit()
        return self.password_reset_token
    
    def verify_reset_token(self, token):
        """Verifica se o token de reset é válido"""
        if not self.password_reset_token or not self.password_reset_expires:
            return False
        if datetime.utcnow() > self.password_reset_expires:
            return False
        return self.password_reset_token == token
    
    # =============================
    # MÉTODOS DE PERMISSÕES
    # =============================
    
    def has_permission(self, permission_code):
        """
        Verifica se o usuário tem uma permissão específica.
        
        Args:
            permission_code: Código da permissão (ex: 'users.create')
        
        Returns:
            bool: True se tem a permissão
        """
        if self.is_admin:
            return True
        return permission_code in self.permission_codes
    
    def has_any_permission(self, permission_codes):
        """Verifica se tem pelo menos uma das permissões"""
        if self.is_admin:
            return True
        return any(code in self.permission_codes for code in permission_codes)
    
    def has_all_permissions(self, permission_codes):
        """Verifica se tem todas as permissões"""
        if self.is_admin:
            return True
        return all(code in self.permission_codes for code in permission_codes)
    
    # =============================
    # MÉTODOS DE GRUPOS
    # =============================
    
    def add_to_group(self, group, added_by_id=None):
        """Adiciona usuário a um grupo"""
        existing = UserGroupMembership.query.filter_by(
            user_id=self.id,
            group_id=group.id
        ).first()
        
        if existing:
            if existing.deleted_at:
                existing.deleted_at = None
                existing.deleted_by_id = None
                db.session.commit()
            return existing
        
        membership = UserGroupMembership(
            user_id=self.id,
            group_id=group.id,
            added_by_id=added_by_id
        )
        db.session.add(membership)
        db.session.commit()
        return membership
    
    def remove_from_group(self, group, removed_by_id=None):
        """Remove usuário de um grupo (soft delete)"""
        membership = UserGroupMembership.query.filter_by(
            user_id=self.id,
            group_id=group.id,
            deleted_at=None
        ).first()
        
        if membership:
            membership.soft_delete(removed_by_id)
    
    def is_in_group(self, group):
        """Verifica se está em um grupo"""
        return group in self.user_groups
    
    # =============================
    # MÉTODOS DE CLASSE
    # =============================
    
    @classmethod
    def find_by_email(cls, email: str):
        """Busca usuário por e-mail"""
        return cls.query_active().filter_by(email=email.lower().strip()).first()
    
    @classmethod
    def find_by_username(cls, username: str):
        """Busca usuário por username"""
        return cls.query_active().filter_by(username=username.lower().strip()).first()
    
    @classmethod
    def find_by_login(cls, login: str):
        """Busca usuário por username ou e-mail"""
        login = login.lower().strip()
        return cls.query_active().filter(
            (cls.username == login) | (cls.email == login)
        ).first()
    
    @classmethod
    def find_by_id(cls, user_id: int):
        """Busca usuário por ID"""
        return cls.query_active().filter_by(id=user_id).first()
    
    @classmethod
    def find_by_reset_token(cls, token: str):
        """Busca usuário por token de reset de senha"""
        return cls.query_active().filter_by(password_reset_token=token).first()
    
    def save(self):
        """Salva usuário no banco"""
        try:
            db.session.add(self)
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f'Erro ao salvar usuário: {e}')
            return False


# =============================================================================
# PERMISSÕES PADRÃO DO SISTEMA
# =============================================================================

DEFAULT_PERMISSIONS = [
    # Usuários
    {'code': 'users.view', 'name': 'Visualizar usuários', 'module': 'users'},
    {'code': 'users.create', 'name': 'Criar usuários', 'module': 'users'},
    {'code': 'users.edit', 'name': 'Editar usuários', 'module': 'users'},
    {'code': 'users.delete', 'name': 'Excluir usuários', 'module': 'users'},
    {'code': 'users.unlock', 'name': 'Desbloquear usuários', 'module': 'users'},
    {'code': 'users.reset_password', 'name': 'Resetar senhas', 'module': 'users'},
    {'code': 'users.invite', 'name': 'Enviar convites', 'module': 'users'},
    
    # Grupos
    {'code': 'groups.view', 'name': 'Visualizar grupos', 'module': 'groups'},
    {'code': 'groups.create', 'name': 'Criar grupos', 'module': 'groups'},
    {'code': 'groups.edit', 'name': 'Editar grupos', 'module': 'groups'},
    {'code': 'groups.delete', 'name': 'Excluir grupos', 'module': 'groups'},
    
    # Funcionários
    {'code': 'employees.view', 'name': 'Visualizar funcionários', 'module': 'employees'},
    {'code': 'employees.create', 'name': 'Criar funcionários', 'module': 'employees'},
    {'code': 'employees.edit', 'name': 'Editar funcionários', 'module': 'employees'},
    {'code': 'employees.delete', 'name': 'Excluir funcionários', 'module': 'employees'},
    {'code': 'employees.terminate', 'name': 'Desligar funcionários', 'module': 'employees'},
    
    # Equipes
    {'code': 'teams.view', 'name': 'Visualizar equipes', 'module': 'teams'},
    {'code': 'teams.create', 'name': 'Criar equipes', 'module': 'teams'},
    {'code': 'teams.edit', 'name': 'Editar equipes', 'module': 'teams'},
    {'code': 'teams.delete', 'name': 'Excluir equipes', 'module': 'teams'},
    
    # Arquivos
    {'code': 'files.view', 'name': 'Visualizar arquivos', 'module': 'files'},
    {'code': 'files.upload', 'name': 'Fazer upload', 'module': 'files'},
    {'code': 'files.download', 'name': 'Fazer download', 'module': 'files'},
    {'code': 'files.edit', 'name': 'Editar arquivos', 'module': 'files'},
    {'code': 'files.delete', 'name': 'Excluir arquivos', 'module': 'files'},
    {'code': 'files.validate', 'name': 'Validar documentos', 'module': 'files'},
    
    # Configurações
    {'code': 'settings.view', 'name': 'Visualizar configurações', 'module': 'settings'},
    {'code': 'settings.edit', 'name': 'Editar configurações', 'module': 'settings'},
    
    # Auditoria
    {'code': 'audit.view', 'name': 'Visualizar logs de auditoria', 'module': 'audit'},
    
    # Mensagens
    {'code': 'messages.view', 'name': 'Visualizar mensagens', 'module': 'messages'},
    {'code': 'messages.send', 'name': 'Enviar mensagens', 'module': 'messages'},
    {'code': 'messages.send_external', 'name': 'Enviar mensagens externas', 'module': 'messages'},
]


DEFAULT_GROUPS = [
    {
        'name': 'Administradores',
        'description': 'Acesso total ao sistema',
        'is_system': True,
        'permissions': ['*']  # Todas as permissões
    },
    {
        'name': 'Gerentes',
        'description': 'Gerenciamento de equipes e funcionários',
        'is_system': True,
        'permissions': [
            'employees.view', 'employees.create', 'employees.edit',
            'teams.view', 'teams.create', 'teams.edit',
            'files.view', 'files.upload', 'files.download', 'files.validate',
            'messages.view', 'messages.send'
        ]
    },
    {
        'name': 'Operadores',
        'description': 'Operações básicas do sistema',
        'is_system': True,
        'permissions': [
            'employees.view', 'employees.create', 'employees.edit',
            'files.view', 'files.upload', 'files.download',
            'messages.view', 'messages.send'
        ]
    },
    {
        'name': 'Visualizadores',
        'description': 'Apenas visualização',
        'is_system': True,
        'permissions': [
            'employees.view',
            'teams.view',
            'files.view', 'files.download'
        ]
    }
]


# =============================================================================
# FLASK-LOGIN CALLBACKS
# =============================================================================

@login_manager.user_loader
def user_loader(user_id):
    """Carrega usuário para o Flask-Login"""
    return Users.query.filter_by(id=user_id).first()


# REMOVIDO: request_loader estava causando problemas com o login
# O request_loader era chamado em cada POST e "autenticava" o usuário
# temporariamente baseado no form, sem criar sessão real.
# O user_loader é suficiente para carregar usuários da sessão.

