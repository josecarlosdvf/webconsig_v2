# -*- encoding: utf-8 -*-
"""
Models de Configurações do Sistema
"""

from datetime import datetime
from apps import db


class SystemSettings(db.Model):
    """Configurações do sistema persistidas no banco de dados"""
    
    __tablename__ = 'system_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text, nullable=True)
    value_type = db.Column(db.String(20), default='string')  # string, int, bool, json, text
    category = db.Column(db.String(50), default='geral', index=True)
    label = db.Column(db.String(100), nullable=True)  # Label amigável para exibição
    description = db.Column(db.String(255), nullable=True)
    is_public = db.Column(db.Boolean, default=False)  # Pode ser mostrado em páginas públicas
    is_editable = db.Column(db.Boolean, default=True)  # Pode ser editado pela interface
    order = db.Column(db.Integer, default=0)  # Ordem de exibição
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SystemSettings {self.key}>'
    
    def get_typed_value(self):
        """Retorna o valor convertido para o tipo correto"""
        if self.value is None:
            return None
        
        if self.value_type == 'int':
            try:
                return int(self.value)
            except (ValueError, TypeError):
                return 0
        
        elif self.value_type == 'bool':
            return self.value.lower() in ('true', '1', 'sim', 'yes')
        
        elif self.value_type == 'json':
            import json
            try:
                return json.loads(self.value)
            except (json.JSONDecodeError, TypeError):
                return {}
        
        elif self.value_type == 'float':
            try:
                return float(self.value)
            except (ValueError, TypeError):
                return 0.0
        
        return self.value  # string ou text
    
    @classmethod
    def get(cls, key: str, default=None):
        """Obtém valor de uma configuração"""
        setting = cls.query.filter_by(key=key).first()
        if setting:
            return setting.get_typed_value()
        return default
    
    @classmethod
    def set(cls, key: str, value, category: str = 'geral', 
            value_type: str = 'string', label: str = None,
            description: str = None, is_public: bool = False,
            is_editable: bool = True, order: int = 0):
        """Define valor de uma configuração"""
        setting = cls.query.filter_by(key=key).first()
        
        if setting:
            setting.value = str(value) if value is not None else None
            setting.updated_at = datetime.utcnow()
            if label:
                setting.label = label
            if description:
                setting.description = description
        else:
            setting = cls(
                key=key,
                value=str(value) if value is not None else None,
                value_type=value_type,
                category=category,
                label=label or key,
                description=description,
                is_public=is_public,
                is_editable=is_editable,
                order=order
            )
            db.session.add(setting)
        
        db.session.commit()
        return setting
    
    @classmethod
    def get_by_category(cls, category: str):
        """Retorna todas as configurações de uma categoria"""
        return cls.query.filter_by(category=category).order_by(cls.order).all()
    
    @classmethod
    def get_all_grouped(cls):
        """Retorna todas as configurações agrupadas por categoria"""
        settings = cls.query.order_by(cls.category, cls.order).all()
        grouped = {}
        for setting in settings:
            if setting.category not in grouped:
                grouped[setting.category] = []
            grouped[setting.category].append(setting)
        return grouped
    
    @classmethod
    def get_public(cls):
        """Retorna configurações públicas"""
        return cls.query.filter_by(is_public=True).all()


# Configurações padrão do sistema
DEFAULT_SETTINGS = [
    # Informações do Sistema
    {
        'key': 'app_name',
        'value': 'WebConsig',
        'value_type': 'string',
        'category': 'sistema',
        'label': 'Nome do Sistema',
        'description': 'Nome exibido no título e cabeçalhos',
        'is_public': True,
        'order': 1
    },
    {
        'key': 'app_description',
        'value': 'Sistema de Gestão Integrada',
        'value_type': 'text',
        'category': 'sistema',
        'label': 'Descrição do Sistema',
        'description': 'Descrição breve do sistema',
        'is_public': True,
        'order': 2
    },
    {
        'key': 'app_version',
        'value': '1.0.0',
        'value_type': 'string',
        'category': 'sistema',
        'label': 'Versão',
        'description': 'Versão atual do sistema',
        'is_public': False,
        'order': 3
    },
    
    # Empresa Desenvolvedora
    {
        'key': 'developer_name',
        'value': 'Sua Empresa de Desenvolvimento',
        'value_type': 'string',
        'category': 'desenvolvedor',
        'label': 'Nome da Desenvolvedora',
        'description': 'Nome da empresa que desenvolveu o sistema',
        'is_public': True,
        'order': 1
    },
    {
        'key': 'developer_url',
        'value': 'https://suaempresa.com.br',
        'value_type': 'string',
        'category': 'desenvolvedor',
        'label': 'Site da Desenvolvedora',
        'description': 'URL do site da desenvolvedora',
        'is_public': True,
        'order': 2
    },
    {
        'key': 'developer_email',
        'value': 'contato@suaempresa.com.br',
        'value_type': 'string',
        'category': 'desenvolvedor',
        'label': 'E-mail da Desenvolvedora',
        'description': 'E-mail de contato para suporte técnico',
        'is_public': False,
        'order': 3
    },
    
    # Empresa Cliente
    {
        'key': 'company_name',
        'value': 'Empresa Cliente LTDA',
        'value_type': 'string',
        'category': 'empresa',
        'label': 'Nome da Empresa',
        'description': 'Nome da empresa que utiliza o sistema',
        'is_public': True,
        'order': 1
    },
    {
        'key': 'company_cnpj',
        'value': '',
        'value_type': 'string',
        'category': 'empresa',
        'label': 'CNPJ',
        'description': 'CNPJ da empresa',
        'is_public': False,
        'order': 2
    },
    {
        'key': 'company_address',
        'value': '',
        'value_type': 'text',
        'category': 'empresa',
        'label': 'Endereço',
        'description': 'Endereço completo da empresa',
        'is_public': False,
        'order': 3
    },
    {
        'key': 'company_phone',
        'value': '',
        'value_type': 'string',
        'category': 'empresa',
        'label': 'Telefone',
        'description': 'Telefone de contato',
        'is_public': False,
        'order': 4
    },
    {
        'key': 'company_email',
        'value': '',
        'value_type': 'string',
        'category': 'empresa',
        'label': 'E-mail',
        'description': 'E-mail de contato da empresa',
        'is_public': False,
        'order': 5
    },
    
    # Aparência
    {
        'key': 'logo_url',
        'value': '/static/assets/img/brand/logo.svg',
        'value_type': 'string',
        'category': 'aparencia',
        'label': 'Logo',
        'description': 'Caminho ou URL da logo principal',
        'is_public': True,
        'order': 1
    },
    {
        'key': 'logo_dark_url',
        'value': '/static/assets/img/brand/logo-light.svg',
        'value_type': 'string',
        'category': 'aparencia',
        'label': 'Logo (Tema Escuro)',
        'description': 'Logo para tema escuro',
        'is_public': True,
        'order': 2
    },
    {
        'key': 'favicon_url',
        'value': '/static/assets/img/favicon/favicon.svg',
        'value_type': 'string',
        'category': 'aparencia',
        'label': 'Favicon',
        'description': 'Ícone do navegador',
        'is_public': True,
        'order': 3
    },
    {
        'key': 'primary_color',
        'value': '#1F2937',
        'value_type': 'string',
        'category': 'aparencia',
        'label': 'Cor Primária',
        'description': 'Cor principal do tema',
        'is_public': True,
        'order': 4
    },
    {
        'key': 'secondary_color',
        'value': '#6B7280',
        'value_type': 'string',
        'category': 'aparencia',
        'label': 'Cor Secundária',
        'description': 'Cor secundária do tema',
        'is_public': True,
        'order': 5
    },
    
    # Localização
    {
        'key': 'language',
        'value': 'pt-BR',
        'value_type': 'string',
        'category': 'localizacao',
        'label': 'Idioma',
        'description': 'Idioma padrão do sistema',
        'is_public': True,
        'order': 1
    },
    {
        'key': 'timezone',
        'value': 'America/Sao_Paulo',
        'value_type': 'string',
        'category': 'localizacao',
        'label': 'Fuso Horário',
        'description': 'Fuso horário do sistema',
        'is_public': True,
        'order': 2
    },
    {
        'key': 'date_format',
        'value': 'DD/MM/YYYY',
        'value_type': 'string',
        'category': 'localizacao',
        'label': 'Formato de Data',
        'description': 'Formato de exibição de datas',
        'is_public': True,
        'order': 3
    },
    {
        'key': 'currency',
        'value': 'BRL',
        'value_type': 'string',
        'category': 'localizacao',
        'label': 'Moeda',
        'description': 'Moeda padrão (BRL, USD, EUR)',
        'is_public': True,
        'order': 4
    },
    
    # Segurança
    {
        'key': 'session_timeout',
        'value': '3600',
        'value_type': 'int',
        'category': 'seguranca',
        'label': 'Tempo de Sessão',
        'description': 'Tempo de expiração da sessão em segundos',
        'is_public': False,
        'order': 1
    },
    {
        'key': 'max_login_attempts',
        'value': '5',
        'value_type': 'int',
        'category': 'seguranca',
        'label': 'Tentativas de Login',
        'description': 'Número máximo de tentativas de login antes de bloquear',
        'is_public': False,
        'order': 2
    },
    {
        'key': 'password_min_length',
        'value': '8',
        'value_type': 'int',
        'category': 'seguranca',
        'label': 'Tamanho Mínimo da Senha',
        'description': 'Número mínimo de caracteres para senhas',
        'is_public': False,
        'order': 3
    },
    {
        'key': 'maintenance_mode',
        'value': 'false',
        'value_type': 'bool',
        'category': 'seguranca',
        'label': 'Modo Manutenção',
        'description': 'Ativar modo de manutenção (bloqueia acesso de usuários)',
        'is_public': False,
        'order': 4
    },
]


def seed_settings():
    """Insere configurações padrão no banco de dados"""
    from apps import db
    
    for setting_data in DEFAULT_SETTINGS:
        existing = SystemSettings.query.filter_by(key=setting_data['key']).first()
        if not existing:
            setting = SystemSettings(**setting_data)
            db.session.add(setting)
    
    db.session.commit()
    print(' > Configurações padrão inseridas com sucesso!')
