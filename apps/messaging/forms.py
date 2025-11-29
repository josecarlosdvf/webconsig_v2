# -*- encoding: utf-8 -*-
"""
Formulários do Módulo de Mensageria
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField, TextAreaField, SelectField, BooleanField,
    IntegerField, HiddenField, PasswordField
)
from wtforms.validators import (
    DataRequired, Length, Optional, URL, NumberRange, Regexp
)


class WhatsAppConnectionForm(FlaskForm):
    """Formulário de conexão WhatsApp"""
    
    name = StringField(
        'Nome da Conexão',
        validators=[
            DataRequired(message='Nome é obrigatório'),
            Length(min=2, max=100, message='Nome deve ter entre 2 e 100 caracteres')
        ],
        render_kw={'placeholder': 'Ex: Atendimento Principal'}
    )
    
    instance_id = StringField(
        'ID da Instância',
        validators=[
            DataRequired(message='ID da instância é obrigatório'),
            Length(min=2, max=100, message='ID deve ter entre 2 e 100 caracteres')
        ],
        render_kw={'placeholder': 'Ex: whatsapp-suporte-001'}
    )
    
    auth_token = PasswordField(
        'Token de Autenticação',
        validators=[
            Optional(),
            Length(max=500, message='Token muito longo')
        ],
        render_kw={'placeholder': 'Token de autenticação (opcional)'}
    )
    
    api_token = PasswordField(
        'Token da API',
        validators=[
            DataRequired(message='Token é obrigatório'),
            Length(min=10, max=500, message='Token inválido')
        ],
        render_kw={'placeholder': 'Cole o token aqui'}
    )
    
    api_base_url = StringField(
        'URL Base da API',
        validators=[
            Optional(),
            URL(message='URL inválida')
        ],
        default='https://wappbe2.rochapromotora.com.br',
        render_kw={'placeholder': 'https://wappbe2.rochapromotora.com.br'}
    )
    
    webhook_url = StringField(
        'URL do Webhook',
        validators=[
            Optional(),
            URL(message='URL inválida')
        ],
        render_kw={'placeholder': 'https://seu-sistema.com/webhook/whatsapp'}
    )
    
    description = TextAreaField(
        'Descrição',
        validators=[
            Optional(),
            Length(max=500, message='Descrição muito longa')
        ],
        render_kw={'placeholder': 'Descrição opcional sobre esta conexão', 'rows': 3}
    )
    
    is_default = BooleanField('Conexão Padrão')
    is_active = BooleanField('Ativa', default=True)
    
    # Rate Limiting
    rate_limit_enabled = BooleanField('Ativar Rate Limiting', default=True)
    
    max_messages_per_minute = IntegerField(
        'Máx. Mensagens/Minuto',
        validators=[
            Optional(),
            NumberRange(min=1, max=60, message='Valor entre 1 e 60')
        ],
        default=5
    )
    
    max_messages_per_hour = IntegerField(
        'Máx. Mensagens/Hora',
        validators=[
            Optional(),
            NumberRange(min=1, max=1000, message='Valor entre 1 e 1000')
        ],
        default=100
    )
    
    min_delay_ms = IntegerField(
        'Delay Mínimo (ms)',
        validators=[
            Optional(),
            NumberRange(min=1000, max=60000, message='Valor entre 1000 e 60000')
        ],
        default=15000
    )
    
    max_delay_ms = IntegerField(
        'Delay Máximo (ms)',
        validators=[
            Optional(),
            NumberRange(min=1000, max=120000, message='Valor entre 1000 e 120000')
        ],
        default=20000
    )


class SendMessageForm(FlaskForm):
    """Formulário de envio de mensagem"""
    
    connection_id = SelectField(
        'Conexão',
        coerce=int,
        validators=[Optional()]
    )
    
    phone_number = StringField(
        'Número de Telefone',
        validators=[
            DataRequired(message='Número é obrigatório'),
            Regexp(
                r'^[\d\s\(\)\-\+]+$',
                message='Número inválido'
            )
        ],
        render_kw={'placeholder': '(21) 99999-8888'}
    )
    
    message_body = TextAreaField(
        'Mensagem',
        validators=[
            DataRequired(message='Mensagem é obrigatória'),
            Length(max=4096, message='Mensagem muito longa')
        ],
        render_kw={
            'placeholder': 'Digite sua mensagem...',
            'rows': 4
        }
    )
    
    media = FileField(
        'Anexar Arquivo',
        validators=[
            Optional(),
            FileAllowed(
                ['jpg', 'jpeg', 'png', 'gif', 'pdf', 'doc', 'docx', 
                 'xls', 'xlsx', 'mp3', 'mp4', 'ogg', 'wav'],
                'Tipo de arquivo não permitido'
            )
        ]
    )


class MessageTemplateForm(FlaskForm):
    """Formulário de template de mensagem"""
    
    name = StringField(
        'Nome do Template',
        validators=[
            DataRequired(message='Nome é obrigatório'),
            Length(min=2, max=100)
        ],
        render_kw={'placeholder': 'Ex: Boas-vindas'}
    )
    
    code = StringField(
        'Código',
        validators=[
            Optional(),
            Length(max=50),
            Regexp(r'^[a-z0-9_]+$', message='Use apenas letras minúsculas, números e _')
        ],
        render_kw={'placeholder': 'Ex: boas_vindas'}
    )
    
    category = SelectField(
        'Categoria',
        choices=[
            ('', 'Selecione...'),
            ('atendimento', 'Atendimento'),
            ('vendas', 'Vendas'),
            ('cobranca', 'Cobrança'),
            ('notificacao', 'Notificação'),
            ('marketing', 'Marketing'),
            ('outros', 'Outros')
        ],
        validators=[Optional()]
    )
    
    body = TextAreaField(
        'Corpo da Mensagem',
        validators=[
            DataRequired(message='Mensagem é obrigatória'),
            Length(max=4096)
        ],
        render_kw={
            'placeholder': 'Olá {{nome}}, sua solicitação foi recebida...',
            'rows': 6
        }
    )
    
    is_active = BooleanField('Ativo', default=True)


class ContactForm(FlaskForm):
    """Formulário de contato"""
    
    name = StringField(
        'Nome',
        validators=[
            Optional(),
            Length(max=200)
        ],
        render_kw={'placeholder': 'Nome do contato'}
    )
    
    phone_number = StringField(
        'Telefone',
        validators=[
            DataRequired(message='Telefone é obrigatório'),
            Regexp(
                r'^[\d\s\(\)\-\+]+$',
                message='Telefone inválido'
            )
        ],
        render_kw={'placeholder': '(21) 99999-8888'}
    )
    
    email = StringField(
        'Email',
        validators=[
            Optional(),
            Length(max=200)
        ],
        render_kw={'placeholder': 'email@exemplo.com'}
    )
    
    entity_type = HiddenField()
    entity_id = HiddenField()


class MessageFilterForm(FlaskForm):
    """Formulário de filtro de mensagens"""
    
    search = StringField(
        'Buscar',
        validators=[Optional()],
        render_kw={'placeholder': 'Número ou mensagem...'}
    )
    
    direction = SelectField(
        'Direção',
        choices=[
            ('', 'Todas'),
            ('incoming', 'Recebidas'),
            ('outgoing', 'Enviadas')
        ],
        validators=[Optional()]
    )
    
    status = SelectField(
        'Status',
        choices=[
            ('', 'Todos'),
            ('sent', 'Enviadas'),
            ('delivered', 'Entregues'),
            ('read', 'Lidas'),
            ('failed', 'Falhas')
        ],
        validators=[Optional()]
    )
    
    date_from = StringField(
        'Data Início',
        validators=[Optional()],
        render_kw={'type': 'date'}
    )
    
    date_to = StringField(
        'Data Fim',
        validators=[Optional()],
        render_kw={'type': 'date'}
    )
