# -*- encoding: utf-8 -*-
"""
Módulo de Database
Gerenciamento de banco de dados, migrações e seeds
"""

from apps.database.seeder import init_database, run_all_seeds, check_database_exists
from apps.database.models import (
    TimestampMixin,
    SoftDeleteMixin,
    AuditMixin,
    BaseModel,
    AuditLog,
    audited,
    enable_audit_for_model
)

__all__ = [
    # Seeder
    'init_database', 
    'run_all_seeds', 
    'check_database_exists',
    # Mixins
    'TimestampMixin',
    'SoftDeleteMixin',
    'AuditMixin',
    'BaseModel',
    # Auditoria
    'AuditLog',
    'audited',
    'enable_audit_for_model'
]
