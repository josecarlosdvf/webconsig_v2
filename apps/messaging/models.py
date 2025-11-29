# -*- encoding: utf-8 -*-
"""
Modelos do Módulo de Mensageria
"""

from datetime import datetime
from apps import db
from apps.database.models import SoftDeleteMixin, AuditMixin


class WhatsAppConnection(SoftDeleteMixin, db.Model):
    """
    Conexão com a API do WhatsApp.
    Cada conexão representa uma conta/número WhatsApp conectado.
    """
    
    __tablename__ = 'whatsapp_connections'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Identificação
    name = db.Column(
        db.String(100), 
        nullable=False,
        comment='Nome da conexão (ex: Atendimento Principal)'
    )
    
    # Credenciais da API
    api_token = db.Column(
        db.String(500), 
        nullable=False,
        comment='Token de autenticação da API'
    )
    api_base_url = db.Column(
        db.String(255), 
        nullable=False,
        default='https://wappbe2.rochapromotora.com.br',
        comment='URL base da API'
    )
    
    # Status da conexão
    status = db.Column(
        db.String(20), 
        nullable=False,
        default='disconnected',
        comment='Status: connected, disconnected, qrcode, opening'
    )
    phone_number = db.Column(
        db.String(20), 
        nullable=True,
        comment='Número conectado'
    )
    
    # Configurações de Rate Limiting
    rate_limit_enabled = db.Column(
        db.Boolean, 
        default=True,
        comment='Se rate limiting está ativo'
    )
    max_messages_per_minute = db.Column(
        db.Integer, 
        default=5,
        comment='Máximo de mensagens por minuto'
    )
    max_messages_per_hour = db.Column(
        db.Integer, 
        default=100,
        comment='Máximo de mensagens por hora'
    )
    min_delay_ms = db.Column(
        db.Integer, 
        default=15000,
        comment='Delay mínimo entre mensagens (ms)'
    )
    max_delay_ms = db.Column(
        db.Integer, 
        default=20000,
        comment='Delay máximo entre mensagens (ms)'
    )
    
    # Webhook
    webhook_url = db.Column(
        db.String(500), 
        nullable=True,
        comment='URL para receber callbacks'
    )
    
    # Flags
    is_default = db.Column(
        db.Boolean, 
        default=False,
        comment='Se é a conexão padrão'
    )
    is_active = db.Column(
        db.Boolean, 
        default=True,
        comment='Se está ativa'
    )
    
    # Datas
    last_connected_at = db.Column(
        db.DateTime, 
        nullable=True,
        comment='Última vez que conectou'
    )
    created_at = db.Column(
        db.DateTime, 
        default=datetime.utcnow
    )
    updated_at = db.Column(
        db.DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Relacionamentos
    messages = db.relationship(
        'WhatsAppMessage', 
        backref='connection', 
        lazy='dynamic'
    )
    contacts = db.relationship(
        'WhatsAppContact', 
        backref='connection', 
        lazy='dynamic'
    )
    
    def __repr__(self):
        return f'<WhatsAppConnection {self.name}>'
    
    @classmethod
    def get_default(cls):
        """Retorna a conexão padrão"""
        return cls.query.filter_by(is_default=True, is_active=True, deleted_at=None).first()


class WhatsAppContact(SoftDeleteMixin, db.Model):
    """
    Contato do WhatsApp.
    Armazena informações de contatos para envio de mensagens.
    """
    
    __tablename__ = 'whatsapp_contacts'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Dados do contato
    name = db.Column(
        db.String(200), 
        nullable=True,
        comment='Nome do contato'
    )
    phone_number = db.Column(
        db.String(20), 
        nullable=False,
        index=True,
        comment='Número de telefone (55DDDNUMERO)'
    )
    email = db.Column(
        db.String(200), 
        nullable=True,
        comment='Email do contato'
    )
    profile_pic_url = db.Column(
        db.String(500), 
        nullable=True,
        comment='URL da foto de perfil'
    )
    
    # JID do WhatsApp
    whatsapp_jid = db.Column(
        db.String(50), 
        nullable=True,
        comment='JID do WhatsApp (numero@s.whatsapp.net)'
    )
    
    # Verificação
    is_whatsapp_valid = db.Column(
        db.Boolean, 
        default=None,
        nullable=True,
        comment='Se o número tem WhatsApp válido'
    )
    last_verified_at = db.Column(
        db.DateTime, 
        nullable=True,
        comment='Última verificação do número'
    )
    
    # Vinculação com entidades do sistema
    entity_type = db.Column(
        db.String(50), 
        nullable=True,
        index=True,
        comment='Tipo de entidade vinculada (employee, user, etc)'
    )
    entity_id = db.Column(
        db.Integer, 
        nullable=True,
        index=True,
        comment='ID da entidade vinculada'
    )
    
    # Conexão
    connection_id = db.Column(
        db.Integer, 
        db.ForeignKey('whatsapp_connections.id'),
        nullable=True,
        comment='Conexão WhatsApp associada'
    )
    
    # Datas
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    messages = db.relationship(
        'WhatsAppMessage', 
        backref='contact', 
        lazy='dynamic'
    )
    
    def __repr__(self):
        return f'<WhatsAppContact {self.phone_number}>'
    
    @property
    def formatted_phone(self):
        """Retorna telefone formatado"""
        phone = self.phone_number
        if phone and len(phone) >= 11:
            return f'({phone[2:4]}) {phone[4:9]}-{phone[9:]}'
        return phone


class WhatsAppMessage(db.Model):
    """
    Mensagem do WhatsApp.
    Registra todas as mensagens enviadas e recebidas.
    """
    
    __tablename__ = 'whatsapp_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # IDs externos
    external_message_id = db.Column(
        db.String(100), 
        nullable=True,
        index=True,
        comment='ID da mensagem na API'
    )
    ticket_id = db.Column(
        db.Integer, 
        nullable=True,
        index=True,
        comment='ID do ticket/conversa na API'
    )
    
    # Contato e Conexão
    contact_id = db.Column(
        db.Integer, 
        db.ForeignKey('whatsapp_contacts.id'),
        nullable=True
    )
    connection_id = db.Column(
        db.Integer, 
        db.ForeignKey('whatsapp_connections.id'),
        nullable=True
    )
    
    # Dados da mensagem
    phone_number = db.Column(
        db.String(20), 
        nullable=False,
        index=True,
        comment='Número do destinatário/remetente'
    )
    body = db.Column(
        db.Text, 
        nullable=True,
        comment='Corpo da mensagem'
    )
    media_type = db.Column(
        db.String(20), 
        default='chat',
        comment='Tipo: chat, image, document, audio, video'
    )
    media_url = db.Column(
        db.String(500), 
        nullable=True,
        comment='URL da mídia'
    )
    media_mimetype = db.Column(
        db.String(100), 
        nullable=True,
        comment='MIME type da mídia'
    )
    
    # Direção e Status
    direction = db.Column(
        db.String(10), 
        nullable=False,
        default='outgoing',
        comment='incoming ou outgoing'
    )
    status = db.Column(
        db.String(20), 
        default='pending',
        comment='pending, queued, sent, delivered, read, failed'
    )
    error_message = db.Column(
        db.String(500), 
        nullable=True,
        comment='Mensagem de erro se falhou'
    )
    
    # Flags
    from_me = db.Column(
        db.Boolean, 
        default=True,
        comment='Se foi enviada por nós'
    )
    is_read = db.Column(
        db.Boolean, 
        default=False,
        comment='Se foi lida'
    )
    
    # Usuário que enviou (se outgoing)
    sent_by_id = db.Column(
        db.Integer, 
        db.ForeignKey('users.id'),
        nullable=True,
        comment='Usuário que enviou a mensagem'
    )
    
    # Datas
    sent_at = db.Column(
        db.DateTime, 
        nullable=True,
        comment='Quando foi enviada'
    )
    delivered_at = db.Column(
        db.DateTime, 
        nullable=True,
        comment='Quando foi entregue'
    )
    read_at = db.Column(
        db.DateTime, 
        nullable=True,
        comment='Quando foi lida'
    )
    created_at = db.Column(
        db.DateTime, 
        default=datetime.utcnow
    )
    
    # Relacionamentos
    sent_by = db.relationship(
        'Users', 
        backref='whatsapp_messages_sent'
    )
    
    def __repr__(self):
        return f'<WhatsAppMessage {self.id} - {self.direction}>'


class MessageTemplate(SoftDeleteMixin, AuditMixin, db.Model):
    """
    Template de mensagem.
    Mensagens pré-definidas para envio rápido.
    """
    
    __tablename__ = 'message_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Identificação
    name = db.Column(
        db.String(100), 
        nullable=False,
        comment='Nome do template'
    )
    code = db.Column(
        db.String(50), 
        nullable=True,
        unique=True,
        comment='Código único para identificação'
    )
    category = db.Column(
        db.String(50), 
        nullable=True,
        comment='Categoria do template'
    )
    
    # Conteúdo
    body = db.Column(
        db.Text, 
        nullable=False,
        comment='Corpo da mensagem. Pode usar variáveis como {{nome}}'
    )
    
    # Variáveis disponíveis
    variables = db.Column(
        db.JSON, 
        nullable=True,
        comment='Lista de variáveis aceitas pelo template'
    )
    
    # Flags
    is_active = db.Column(
        db.Boolean, 
        default=True
    )
    
    # Datas
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<MessageTemplate {self.name}>'
    
    def render(self, context: dict) -> str:
        """
        Renderiza o template substituindo variáveis.
        
        Args:
            context: Dicionário com valores das variáveis
            
        Returns:
            Mensagem renderizada
        """
        result = self.body
        for key, value in context.items():
            result = result.replace(f'{{{{{key}}}}}', str(value or ''))
        return result


class MessageQueue(db.Model):
    """
    Fila de mensagens para envio.
    Gerencia o envio com rate limiting.
    """
    
    __tablename__ = 'message_queue'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Mensagem
    message_id = db.Column(
        db.Integer, 
        db.ForeignKey('whatsapp_messages.id'),
        nullable=False
    )
    connection_id = db.Column(
        db.Integer, 
        db.ForeignKey('whatsapp_connections.id'),
        nullable=False
    )
    
    # Status da fila
    priority = db.Column(
        db.Integer, 
        default=0,
        comment='Prioridade (maior = mais importante)'
    )
    attempts = db.Column(
        db.Integer, 
        default=0,
        comment='Tentativas de envio'
    )
    max_attempts = db.Column(
        db.Integer, 
        default=3,
        comment='Máximo de tentativas'
    )
    status = db.Column(
        db.String(20), 
        default='pending',
        comment='pending, processing, completed, failed'
    )
    
    # Agendamento
    scheduled_for = db.Column(
        db.DateTime, 
        nullable=True,
        comment='Agendado para'
    )
    processed_at = db.Column(
        db.DateTime, 
        nullable=True,
        comment='Quando foi processado'
    )
    
    # Datas
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    message = db.relationship('WhatsAppMessage')
    connection = db.relationship('WhatsAppConnection')
    
    def __repr__(self):
        return f'<MessageQueue {self.id} - {self.status}>'
