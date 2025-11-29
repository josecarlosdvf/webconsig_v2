# -*- encoding: utf-8 -*-
"""
Modelos Base do Banco de Dados
Mixins reutilizáveis e modelo de auditoria
"""

from datetime import datetime
from flask import request, has_request_context
from flask_login import current_user
from sqlalchemy import event, inspect
from sqlalchemy.orm import declared_attr

from apps import db


# =============================================================================
# MIXINS REUTILIZÁVEIS
# =============================================================================

class TimestampMixin:
    """
    Mixin para campos de timestamp automáticos.
    Adiciona created_at e updated_at em qualquer modelo.
    """
    
    created_at = db.Column(
        db.DateTime, 
        default=datetime.utcnow, 
        nullable=False,
        comment='Data de criação do registro'
    )
    updated_at = db.Column(
        db.DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow,
        nullable=False,
        comment='Data da última atualização'
    )


class SoftDeleteMixin:
    """
    Mixin para soft delete.
    Registros não são excluídos, apenas marcados como deletados.
    """
    
    deleted_at = db.Column(
        db.DateTime, 
        nullable=True, 
        index=True,
        comment='Data de exclusão (soft delete)'
    )
    
    @declared_attr
    def deleted_by_id(cls):
        return db.Column(
            db.Integer, 
            db.ForeignKey('users.id', ondelete='SET NULL'),
            nullable=True,
            comment='ID do usuário que excluiu o registro'
        )
    
    @property
    def is_deleted(self):
        """Verifica se o registro foi excluído"""
        return self.deleted_at is not None
    
    def soft_delete(self, user_id=None):
        """
        Marca o registro como excluído.
        
        Args:
            user_id: ID do usuário que está excluindo (opcional, usa current_user se disponível)
        """
        self.deleted_at = datetime.utcnow()
        
        if user_id:
            self.deleted_by_id = user_id
        elif has_request_context() and current_user and current_user.is_authenticated:
            self.deleted_by_id = current_user.id
        
        db.session.commit()
    
    def restore(self):
        """Restaura um registro excluído"""
        self.deleted_at = None
        self.deleted_by_id = None
        db.session.commit()
    
    @classmethod
    def query_active(cls):
        """Retorna query filtrada apenas com registros ativos (não excluídos)"""
        return cls.query.filter(cls.deleted_at.is_(None))
    
    @classmethod
    def query_deleted(cls):
        """Retorna query filtrada apenas com registros excluídos"""
        return cls.query.filter(cls.deleted_at.isnot(None))


class AuditMixin:
    """
    Mixin para rastreamento de criação/atualização.
    Registra quem criou e quem atualizou o registro.
    """
    
    @declared_attr
    def created_by_id(cls):
        return db.Column(
            db.Integer, 
            db.ForeignKey('users.id', ondelete='SET NULL'),
            nullable=True,
            comment='ID do usuário que criou o registro'
        )
    
    @declared_attr
    def updated_by_id(cls):
        return db.Column(
            db.Integer, 
            db.ForeignKey('users.id', ondelete='SET NULL'),
            nullable=True,
            comment='ID do usuário que atualizou o registro'
        )


class BaseModel(TimestampMixin, SoftDeleteMixin, AuditMixin):
    """
    Modelo base completo.
    Combina todos os mixins para uso padrão.
    Herdar esta classe em todos os modelos do sistema.
    """
    pass


# =============================================================================
# MODELO DE AUDITORIA
# =============================================================================

class AuditLog(db.Model):
    """
    Log de auditoria do sistema.
    Registra todas as ações dos usuários para fins de auditoria.
    """
    
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Quem fez a ação
    user_id = db.Column(
        db.Integer, 
        db.ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
        comment='ID do usuário que executou a ação'
    )
    username = db.Column(
        db.String(64), 
        nullable=True,
        comment='Username do usuário (para manter histórico mesmo se usuário for excluído)'
    )
    
    # O que foi feito
    action = db.Column(
        db.String(50), 
        nullable=False,
        index=True,
        comment='Tipo de ação: create, update, delete, login, logout, etc'
    )
    
    # Onde foi feito
    table_name = db.Column(
        db.String(100), 
        nullable=True,
        index=True,
        comment='Nome da tabela afetada'
    )
    record_id = db.Column(
        db.Integer, 
        nullable=True,
        comment='ID do registro afetado'
    )
    
    # Detalhes da mudança (JSON)
    old_values = db.Column(
        db.JSON, 
        nullable=True,
        comment='Valores anteriores (para update/delete)'
    )
    new_values = db.Column(
        db.JSON, 
        nullable=True,
        comment='Novos valores (para create/update)'
    )
    
    # Descrição legível
    description = db.Column(
        db.String(500), 
        nullable=True,
        comment='Descrição legível da ação'
    )
    
    # Contexto da requisição
    ip_address = db.Column(
        db.String(45), 
        nullable=True,
        comment='Endereço IP do usuário'
    )
    user_agent = db.Column(
        db.String(500), 
        nullable=True,
        comment='User-Agent do navegador'
    )
    endpoint = db.Column(
        db.String(200), 
        nullable=True,
        comment='Endpoint/rota acessada'
    )
    method = db.Column(
        db.String(10), 
        nullable=True,
        comment='Método HTTP (GET, POST, etc)'
    )
    
    # Timestamp
    created_at = db.Column(
        db.DateTime, 
        default=datetime.utcnow, 
        nullable=False,
        index=True
    )
    
    # Relacionamentos
    user = db.relationship(
        'Users', 
        backref=db.backref('audit_logs', lazy='dynamic'),
        foreign_keys=[user_id]
    )
    
    def __repr__(self):
        return f'<AuditLog {self.id}: {self.action} by {self.username}>'
    
    @classmethod
    def log(cls, action, table_name=None, record_id=None, old_values=None, 
            new_values=None, description=None, user_id=None, username=None):
        """
        Registra uma ação no log de auditoria.
        
        Args:
            action: Tipo de ação (create, update, delete, login, etc)
            table_name: Nome da tabela afetada
            record_id: ID do registro afetado
            old_values: Dict com valores anteriores
            new_values: Dict com novos valores
            description: Descrição legível da ação
            user_id: ID do usuário (opcional, usa current_user)
            username: Username (opcional, usa current_user)
        
        Returns:
            AuditLog: Instância criada
        """
        # Obtém informações do usuário
        if user_id is None and has_request_context():
            if current_user and current_user.is_authenticated:
                user_id = current_user.id
                username = current_user.username
        
        # Obtém informações da requisição
        ip_address = None
        user_agent = None
        endpoint = None
        method = None
        
        if has_request_context():
            ip_address = request.remote_addr
            user_agent = request.user_agent.string[:500] if request.user_agent else None
            endpoint = request.endpoint
            method = request.method
        
        # Cria o log
        log_entry = cls(
            user_id=user_id,
            username=username,
            action=action,
            table_name=table_name,
            record_id=record_id,
            old_values=old_values,
            new_values=new_values,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            endpoint=endpoint,
            method=method
        )
        
        db.session.add(log_entry)
        # Não faz commit aqui para permitir transações
        
        return log_entry
    
    @classmethod
    def log_login(cls, user, success=True, failure_reason=None):
        """Registra tentativa de login"""
        action = 'login_success' if success else 'login_failed'
        description = f"Login {'bem-sucedido' if success else 'falhou'}"
        if failure_reason:
            description += f": {failure_reason}"
        
        return cls.log(
            action=action,
            table_name='users',
            record_id=user.id if user else None,
            description=description,
            user_id=user.id if user else None,
            username=user.username if user else None
        )
    
    @classmethod
    def log_logout(cls, user):
        """Registra logout"""
        return cls.log(
            action='logout',
            table_name='users',
            record_id=user.id,
            description='Logout realizado',
            user_id=user.id,
            username=user.username
        )


# =============================================================================
# FUNÇÕES AUXILIARES PARA AUDITORIA AUTOMÁTICA
# =============================================================================

def get_model_changes(instance):
    """
    Obtém as mudanças em um modelo antes do commit.
    
    Returns:
        tuple: (old_values, new_values) dicts
    """
    old_values = {}
    new_values = {}
    
    mapper = inspect(instance.__class__)
    
    for column in mapper.columns:
        key = column.key
        
        # Ignora campos de senha e tokens
        if key in ('password', 'session_token', 'password_reset_token'):
            continue
        
        history = inspect(instance).attrs[key].history
        
        if history.has_changes():
            old_val = history.deleted[0] if history.deleted else None
            new_val = history.added[0] if history.added else None
            
            # Converte datetime para string
            if isinstance(old_val, datetime):
                old_val = old_val.isoformat()
            if isinstance(new_val, datetime):
                new_val = new_val.isoformat()
            
            old_values[key] = old_val
            new_values[key] = new_val
    
    return old_values, new_values


def get_model_dict(instance, exclude=None):
    """
    Converte um modelo para dicionário.
    
    Args:
        instance: Instância do modelo
        exclude: Lista de campos a excluir
    
    Returns:
        dict: Dicionário com os valores do modelo
    """
    exclude = exclude or ['password', 'session_token', 'password_reset_token']
    result = {}
    
    mapper = inspect(instance.__class__)
    
    for column in mapper.columns:
        key = column.key
        
        if key in exclude:
            continue
        
        value = getattr(instance, key, None)
        
        # Converte datetime para string
        if isinstance(value, datetime):
            value = value.isoformat()
        
        result[key] = value
    
    return result


# Lista de tabelas que devem ter auditoria automática
AUDITED_TABLES = set()

# Lista de logs pendentes para serem gravados
_pending_audit_logs = []

# Flag para evitar recursão no flush de logs
_flushing_audit_logs = False


def _flush_pending_audit_logs():
    """Grava os logs de auditoria pendentes usando uma nova sessão"""
    global _pending_audit_logs, _flushing_audit_logs
    
    # Evita recursão
    if _flushing_audit_logs:
        return
    
    if not _pending_audit_logs:
        return
        
    _flushing_audit_logs = True
    logs_to_write = _pending_audit_logs.copy()
    _pending_audit_logs = []
    
    try:
        for log_data in logs_to_write:
            AuditLog.log(**log_data)
        # Faz commit dos logs de auditoria
        db.session.commit()
    except Exception as e:
        # Log silencioso para não interferir na operação principal
        import logging
        logging.getLogger('app').warning(f'Erro ao gravar audit log: {e}')
        try:
            db.session.rollback()
        except:
            pass
    finally:
        _flushing_audit_logs = False


def enable_audit_for_model(model_class):
    """
    Habilita auditoria automática para um modelo.
    
    Args:
        model_class: Classe do modelo SQLAlchemy
    """
    AUDITED_TABLES.add(model_class.__tablename__)
    
    @event.listens_for(model_class, 'after_insert')
    def audit_insert(mapper, connection, target):
        """Registra criação de registro"""
        # Agenda o log para ser gravado após o commit
        _pending_audit_logs.append({
            'action': 'create',
            'table_name': target.__tablename__,
            'record_id': target.id,
            'new_values': get_model_dict(target),
            'description': f'Registro criado em {target.__tablename__}'
        })
    
    @event.listens_for(model_class, 'before_update')
    def audit_update(mapper, connection, target):
        """Registra atualização de registro"""
        # Campos a ignorar na auditoria (atualizações frequentes/automáticas)
        AUDIT_IGNORE_FIELDS = {
            'session_token', 'last_login', 'failed_login_attempts', 
            'locked_until', 'updated_at'
        }
        
        old_values, new_values = get_model_changes(target)
        
        # Remove campos ignorados
        for field in AUDIT_IGNORE_FIELDS:
            old_values.pop(field, None)
            new_values.pop(field, None)
        
        if old_values:  # Só loga se houve mudanças reais (excluindo ignorados)
            _pending_audit_logs.append({
                'action': 'update',
                'table_name': target.__tablename__,
                'record_id': target.id,
                'old_values': old_values,
                'new_values': new_values,
                'description': f'Registro atualizado em {target.__tablename__}'
            })
    
    @event.listens_for(model_class, 'before_delete')
    def audit_delete(mapper, connection, target):
        """Registra exclusão de registro"""
        old_values = get_model_dict(target)
        
        _pending_audit_logs.append({
            'action': 'delete',
            'table_name': target.__tablename__,
            'record_id': target.id,
            'old_values': old_values,
            'description': f'Registro excluído de {target.__tablename__}'
        })


# Registra o evento de flush dos logs após cada commit
@event.listens_for(db.session, 'after_commit')
def _after_commit_flush_logs(session):
    """Grava os logs pendentes após cada commit bem-sucedido"""
    _flush_pending_audit_logs()


# Decorator para habilitar auditoria
def audited(cls):
    """
    Decorator para habilitar auditoria automática em um modelo.
    
    Uso:
        @audited
        class MyModel(db.Model, BaseModel):
            ...
    """
    enable_audit_for_model(cls)
    return cls
