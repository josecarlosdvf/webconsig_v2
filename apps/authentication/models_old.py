# -*- encoding: utf-8 -*-
"""
Models de Autenticação
"""

import secrets
from datetime import datetime
from flask_login import UserMixin
from sqlalchemy.exc import SQLAlchemyError

from apps import db, login_manager
from apps.authentication.util import hash_password, verify_password


class Users(db.Model, UserMixin):
    """Model de Usuário"""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password = db.Column(db.LargeBinary, nullable=False)
    
    # Informações pessoais
    first_name = db.Column(db.String(64), nullable=True)
    last_name = db.Column(db.String(64), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    avatar_url = db.Column(db.String(255), nullable=True)
    
    # Status e Role
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    role_id = db.Column(db.Integer, default=3)  # 1=Admin, 2=Manager, 3=User
    
    # OAuth
    oauth_github = db.Column(db.String(100), nullable=True)
    oauth_google = db.Column(db.String(100), nullable=True)
    
    # Controle de Sessão Única
    session_token = db.Column(db.String(64), nullable=True, index=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Campos que não podem ser editados pelo usuário
    readonly_fields = ['id', 'username', 'email', 'oauth_github', 'oauth_google', 'created_at']
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(value, '__iter__') and not isinstance(value, str):
                value = value[0]
            
            if key == 'password':
                value = hash_password(value)
            
            setattr(self, key, value)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
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
    
    def check_password(self, password: str) -> bool:
        """Verifica se a senha está correta"""
        return verify_password(password, self.password)
    
    def set_password(self, password: str):
        """Define nova senha"""
        self.password = hash_password(password)
    
    def update_last_login(self):
        """Atualiza data do último login"""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def generate_session_token(self):
        """Gera um novo token de sessão único"""
        self.session_token = secrets.token_hex(32)
        self.last_login = datetime.utcnow()
        db.session.commit()
        return self.session_token
    
    def invalidate_session(self):
        """Invalida o token de sessão atual"""
        self.session_token = None
        db.session.commit()
    
    def verify_session_token(self, token):
        """Verifica se o token de sessão é válido"""
        return self.session_token is not None and self.session_token == token
    
    @classmethod
    def find_by_email(cls, email: str):
        """Busca usuário por e-mail"""
        return cls.query.filter_by(email=email).first()
    
    @classmethod
    def find_by_username(cls, username: str):
        """Busca usuário por username"""
        return cls.query.filter_by(username=username).first()
    
    @classmethod
    def find_by_id(cls, user_id: int):
        """Busca usuário por ID"""
        return cls.query.filter_by(id=user_id).first()
    
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
    
    def delete(self):
        """Remove usuário do banco"""
        try:
            db.session.delete(self)
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f'Erro ao deletar usuário: {e}')
            return False


@login_manager.user_loader
def user_loader(user_id):
    """Carrega usuário para o Flask-Login"""
    return Users.query.filter_by(id=user_id).first()


@login_manager.request_loader
def request_loader(request):
    """Carrega usuário da requisição"""
    username = request.form.get('username')
    if username:
        return Users.query.filter_by(username=username).first()
    return None
