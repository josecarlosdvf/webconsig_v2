# -*- encoding: utf-8 -*-
"""
Rotas do Módulo de Mensageria - WhatsApp Integration
"""

from flask import (
    render_template, redirect, url_for, flash, request, 
    jsonify, current_app, abort
)
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy import or_, desc

from apps import db
from apps.messaging import blueprint
from apps.messaging.models import (
    WhatsAppConnection, WhatsAppContact, WhatsAppMessage, MessageTemplate
)
from apps.messaging.forms import (
    WhatsAppConnectionForm, SendMessageForm, MessageTemplateForm,
    ContactForm, MessageFilterForm
)
from apps.messaging.services import WhatsAppService, WhatsAppAPIError
from apps.database.models import AuditLog
from apps.authentication.decorators import permission_required


# =============================================================================
# DASHBOARD DE MENSAGENS
# =============================================================================

@blueprint.route('/')
@login_required
@permission_required('messaging.view')
def index():
    """Dashboard de mensageria"""
    
    # Estatísticas
    stats = {
        'total_messages': WhatsAppMessage.query.count(),
        'messages_today': WhatsAppMessage.query.filter(
            WhatsAppMessage.created_at >= datetime.utcnow().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        ).count(),
        'total_contacts': WhatsAppContact.query.filter_by(deleted_at=None).count(),
        'active_connections': WhatsAppConnection.query.filter_by(
            is_active=True, deleted_at=None
        ).count()
    }
    
    # Últimas mensagens
    recent_messages = WhatsAppMessage.query.order_by(
        desc(WhatsAppMessage.created_at)
    ).limit(10).all()
    
    # Conexões ativas
    connections = WhatsAppConnection.query.filter_by(
        is_active=True, deleted_at=None
    ).all()
    
    return render_template(
        'messaging/index.html',
        stats=stats,
        recent_messages=recent_messages,
        connections=connections
    )


# =============================================================================
# CONEXÕES WHATSAPP
# =============================================================================

@blueprint.route('/conexoes')
@login_required
@permission_required('messaging.manage')
def connections_list():
    """Lista de conexões WhatsApp"""
    connections = WhatsAppConnection.query.filter_by(deleted_at=None).order_by(
        desc(WhatsAppConnection.is_default),
        WhatsAppConnection.name
    ).all()
    
    return render_template(
        'messaging/connections/list.html',
        connections=connections
    )


@blueprint.route('/conexoes/nova', methods=['GET', 'POST'])
@login_required
@permission_required('messaging.manage')
def connection_create():
    """Criar nova conexão WhatsApp"""
    form = WhatsAppConnectionForm()
    
    if form.validate_on_submit():
        # Se for padrão, remove a flag das outras
        if form.is_default.data:
            WhatsAppConnection.query.filter_by(is_default=True).update(
                {'is_default': False}
            )
        
        connection = WhatsAppConnection(
            name=form.name.data,
            api_token=form.api_token.data,
            api_base_url=form.api_base_url.data or 'https://wappbe2.rochapromotora.com.br',
            is_default=form.is_default.data,
            is_active=form.is_active.data,
            rate_limit_enabled=form.rate_limit_enabled.data,
            max_messages_per_minute=form.max_messages_per_minute.data,
            max_messages_per_hour=form.max_messages_per_hour.data,
            min_delay_ms=form.min_delay_ms.data,
            max_delay_ms=form.max_delay_ms.data,
            webhook_url=form.webhook_url.data
        )
        
        db.session.add(connection)
        db.session.commit()
        
        AuditLog.log(
            action='create',
            table_name='whatsapp_connections',
            record_id=connection.id,
            new_values={'name': connection.name},
            description=f'Conexão WhatsApp criada: {connection.name}'
        )
        
        flash('Conexão criada com sucesso!', 'success')
        return redirect(url_for('messaging_blueprint.connections_list'))
    
    return render_template(
        'messaging/connections/form.html',
        form=form,
        title='Nova Conexão WhatsApp'
    )


@blueprint.route('/conexoes/<int:connection_id>/editar', methods=['GET', 'POST'])
@login_required
@permission_required('messaging.manage')
def connection_edit(connection_id):
    """Editar conexão WhatsApp"""
    connection = WhatsAppConnection.query.get_or_404(connection_id)
    form = WhatsAppConnectionForm(obj=connection)
    
    if form.validate_on_submit():
        # Se for padrão, remove a flag das outras
        if form.is_default.data and not connection.is_default:
            WhatsAppConnection.query.filter(
                WhatsAppConnection.id != connection_id,
                WhatsAppConnection.is_default == True
            ).update({'is_default': False})
        
        old_values = {'name': connection.name}
        
        connection.name = form.name.data
        if form.api_token.data:  # Só atualiza se fornecido
            connection.api_token = form.api_token.data
        connection.api_base_url = form.api_base_url.data
        connection.is_default = form.is_default.data
        connection.is_active = form.is_active.data
        connection.rate_limit_enabled = form.rate_limit_enabled.data
        connection.max_messages_per_minute = form.max_messages_per_minute.data
        connection.max_messages_per_hour = form.max_messages_per_hour.data
        connection.min_delay_ms = form.min_delay_ms.data
        connection.max_delay_ms = form.max_delay_ms.data
        connection.webhook_url = form.webhook_url.data
        
        db.session.commit()
        
        AuditLog.log(
            action='update',
            table_name='whatsapp_connections',
            record_id=connection.id,
            old_values=old_values,
            new_values={'name': connection.name},
            description=f'Conexão WhatsApp atualizada: {connection.name}'
        )
        
        flash('Conexão atualizada com sucesso!', 'success')
        return redirect(url_for('messaging_blueprint.connections_list'))
    
    # Não mostrar token existente
    form.api_token.data = ''
    
    return render_template(
        'messaging/connections/form.html',
        form=form,
        connection=connection,
        title='Editar Conexão WhatsApp'
    )


@blueprint.route('/conexoes/<int:connection_id>/status')
@login_required
@permission_required('messaging.view')
def connection_status(connection_id):
    """Verifica status da conexão"""
    connection = WhatsAppConnection.query.get_or_404(connection_id)
    
    try:
        service = WhatsAppService(connection)
        status = service.get_connection_status()
        
        # Atualiza status local
        conn_data = status.get('connection', {})
        connection.status = conn_data.get('status', 'unknown')
        connection.phone_number = conn_data.get('number', '')
        db.session.commit()
        
        return jsonify({
            'success': True,
            'connection': {
                'id': connection.id,
                'name': connection.name,
                'status': connection.status,
                'phone_number': connection.phone_number
            }
        })
        
    except WhatsAppAPIError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@blueprint.route('/conexoes/<int:connection_id>/qrcode')
@login_required
@permission_required('messaging.manage')
def connection_qrcode(connection_id):
    """Obtém QR Code para conexão"""
    connection = WhatsAppConnection.query.get_or_404(connection_id)
    
    try:
        service = WhatsAppService(connection)
        result = service.get_qrcode(connection_id)
        
        return jsonify({
            'success': True,
            'qrcode': result.get('qrcode'),
            'status': result.get('status'),
            'expires_in': result.get('expiresIn', 60)
        })
        
    except WhatsAppAPIError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@blueprint.route('/conexoes/<int:connection_id>/reiniciar', methods=['POST'])
@login_required
@permission_required('messaging.manage')
def connection_restart(connection_id):
    """Reinicia conexão"""
    connection = WhatsAppConnection.query.get_or_404(connection_id)
    
    try:
        service = WhatsAppService(connection)
        result = service.restart_connection(connection_id)
        
        connection.status = 'qrcode'
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': result.get('message', 'Conexão reiniciada')
        })
        
    except WhatsAppAPIError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@blueprint.route('/conexoes/<int:connection_id>/desconectar', methods=['POST'])
@login_required
@permission_required('messaging.manage')
def connection_disconnect(connection_id):
    """Desconecta sessão"""
    connection = WhatsAppConnection.query.get_or_404(connection_id)
    
    try:
        service = WhatsAppService(connection)
        result = service.disconnect(connection_id)
        
        connection.status = 'disconnected'
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': result.get('message', 'Desconectado')
        })
        
    except WhatsAppAPIError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@blueprint.route('/conexoes/<int:connection_id>/excluir', methods=['POST'])
@login_required
@permission_required('messaging.manage')
def connection_delete(connection_id):
    """Exclui conexão (soft delete)"""
    connection = WhatsAppConnection.query.get_or_404(connection_id)
    
    connection.soft_delete(current_user.id)
    
    AuditLog.log(
        action='delete',
        table_name='whatsapp_connections',
        record_id=connection.id,
        old_values={'name': connection.name},
        description=f'Conexão WhatsApp excluída: {connection.name}'
    )
    
    flash('Conexão excluída com sucesso!', 'success')
    return redirect(url_for('messaging_blueprint.connections_list'))


# =============================================================================
# ENVIO DE MENSAGENS
# =============================================================================

@blueprint.route('/enviar', methods=['GET', 'POST'])
@login_required
@permission_required('messaging.send')
def send_message():
    """Enviar nova mensagem"""
    form = SendMessageForm()
    
    # Popula conexões
    connections = WhatsAppConnection.query.filter_by(
        is_active=True, deleted_at=None
    ).all()
    form.connection_id.choices = [
        (0, 'Conexão Padrão')
    ] + [(c.id, c.name) for c in connections]
    
    if form.validate_on_submit():
        # Obtém conexão
        connection = None
        if form.connection_id.data:
            connection = WhatsAppConnection.query.get(form.connection_id.data)
        
        try:
            service = WhatsAppService(connection)
            
            # Verifica se tem arquivo
            if form.media.data:
                # Envio com mídia
                file = form.media.data
                result, message = service.send_media_message(
                    number=form.phone_number.data,
                    file_data=file.read(),
                    filename=file.filename,
                    caption=form.message_body.data,
                    user_id=current_user.id
                )
            else:
                # Envio de texto
                result, message = service.send_text_message(
                    number=form.phone_number.data,
                    body=form.message_body.data,
                    user_id=current_user.id
                )
            
            if result.get('success'):
                flash('Mensagem enviada com sucesso!', 'success')
                return redirect(url_for('messaging_blueprint.messages_list'))
            else:
                flash(f'Erro ao enviar: {result.get("error", "Erro desconhecido")}', 'error')
                
        except WhatsAppAPIError as e:
            flash(f'Erro: {e.message}', 'error')
    
    # Templates disponíveis
    templates = MessageTemplate.query.filter_by(
        is_active=True, deleted_at=None
    ).order_by(MessageTemplate.name).all()
    
    return render_template(
        'messaging/send.html',
        form=form,
        templates=templates
    )


@blueprint.route('/api/enviar', methods=['POST'])
@login_required
@permission_required('messaging.send')
def api_send_message():
    """API para envio de mensagem"""
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'Dados não fornecidos'}), 400
    
    number = data.get('number')
    body = data.get('body')
    connection_id = data.get('connection_id')
    
    if not number or not body:
        return jsonify({'success': False, 'error': 'Número e mensagem são obrigatórios'}), 400
    
    try:
        connection = None
        if connection_id:
            connection = WhatsAppConnection.query.get(connection_id)
        
        service = WhatsAppService(connection)
        result, message = service.send_text_message(
            number=number,
            body=body,
            user_id=current_user.id
        )
        
        return jsonify({
            'success': result.get('success', False),
            'message_id': message.id if message else None,
            'external_id': result.get('data', {}).get('messageId')
        })
        
    except WhatsAppAPIError as e:
        return jsonify({
            'success': False,
            'error': e.message,
            'code': e.code
        }), 400


# =============================================================================
# HISTÓRICO DE MENSAGENS
# =============================================================================

@blueprint.route('/historico')
@login_required
@permission_required('messaging.view')
def messages_list():
    """Lista de mensagens"""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    # Filtros
    search = request.args.get('search', '')
    direction = request.args.get('direction', '')
    status = request.args.get('status', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    query = WhatsAppMessage.query
    
    if search:
        query = query.filter(
            or_(
                WhatsAppMessage.phone_number.ilike(f'%{search}%'),
                WhatsAppMessage.body.ilike(f'%{search}%')
            )
        )
    
    if direction:
        query = query.filter_by(direction=direction)
    
    if status:
        query = query.filter_by(status=status)
    
    if date_from:
        try:
            dt_from = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(WhatsAppMessage.created_at >= dt_from)
        except ValueError:
            pass
    
    if date_to:
        try:
            dt_to = datetime.strptime(date_to, '%Y-%m-%d').replace(
                hour=23, minute=59, second=59
            )
            query = query.filter(WhatsAppMessage.created_at <= dt_to)
        except ValueError:
            pass
    
    pagination = query.order_by(
        desc(WhatsAppMessage.created_at)
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template(
        'messaging/messages/list.html',
        messages=pagination.items,
        pagination=pagination,
        filters={
            'search': search,
            'direction': direction,
            'status': status,
            'date_from': date_from,
            'date_to': date_to
        }
    )


@blueprint.route('/mensagem/<int:message_id>')
@login_required
@permission_required('messaging.view')
def message_view(message_id):
    """Visualizar mensagem"""
    message = WhatsAppMessage.query.get_or_404(message_id)
    
    # Busca outras mensagens do mesmo contato
    related_messages = WhatsAppMessage.query.filter_by(
        phone_number=message.phone_number
    ).order_by(desc(WhatsAppMessage.created_at)).limit(20).all()
    
    return render_template(
        'messaging/messages/view.html',
        message=message,
        related_messages=related_messages
    )


# =============================================================================
# CONTATOS
# =============================================================================

@blueprint.route('/contatos')
@login_required
@permission_required('messaging.view')
def contacts_list():
    """Lista de contatos"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    per_page = 50
    
    query = WhatsAppContact.query.filter_by(deleted_at=None)
    
    if search:
        query = query.filter(
            or_(
                WhatsAppContact.name.ilike(f'%{search}%'),
                WhatsAppContact.phone_number.ilike(f'%{search}%'),
                WhatsAppContact.email.ilike(f'%{search}%')
            )
        )
    
    pagination = query.order_by(
        WhatsAppContact.name, WhatsAppContact.phone_number
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template(
        'messaging/contacts/list.html',
        contacts=pagination.items,
        pagination=pagination,
        search=search
    )


@blueprint.route('/contatos/<int:contact_id>')
@login_required
@permission_required('messaging.view')
def contact_view(contact_id):
    """Visualizar contato"""
    contact = WhatsAppContact.query.get_or_404(contact_id)
    
    # Mensagens do contato
    messages = WhatsAppMessage.query.filter_by(
        phone_number=contact.phone_number
    ).order_by(desc(WhatsAppMessage.created_at)).limit(50).all()
    
    return render_template(
        'messaging/contacts/view.html',
        contact=contact,
        messages=messages
    )


@blueprint.route('/api/contatos/verificar', methods=['POST'])
@login_required
@permission_required('messaging.view')
def api_check_contact():
    """Verifica se número tem WhatsApp"""
    data = request.get_json()
    
    number = data.get('number')
    if not number:
        return jsonify({'success': False, 'error': 'Número não fornecido'}), 400
    
    try:
        service = WhatsAppService()
        result = service.check_number(number)
        
        return jsonify({
            'success': True,
            'exists': result.get('exists', False),
            'jid': result.get('jid'),
            'name': result.get('name')
        })
        
    except WhatsAppAPIError as e:
        return jsonify({
            'success': False,
            'error': e.message
        }), 400


# =============================================================================
# TEMPLATES
# =============================================================================

@blueprint.route('/templates')
@login_required
@permission_required('messaging.manage')
def templates_list():
    """Lista de templates"""
    templates = MessageTemplate.query.filter_by(deleted_at=None).order_by(
        MessageTemplate.category, MessageTemplate.name
    ).all()
    
    return render_template(
        'messaging/templates/list.html',
        templates=templates
    )


@blueprint.route('/templates/novo', methods=['GET', 'POST'])
@login_required
@permission_required('messaging.manage')
def template_create():
    """Criar template"""
    form = MessageTemplateForm()
    
    if form.validate_on_submit():
        template = MessageTemplate(
            name=form.name.data,
            code=form.code.data or None,
            category=form.category.data or None,
            body=form.body.data,
            is_active=form.is_active.data,
            created_by_id=current_user.id
        )
        
        db.session.add(template)
        db.session.commit()
        
        AuditLog.log(
            action='create',
            table_name='message_templates',
            record_id=template.id,
            new_values={'name': template.name},
            description=f'Template criado: {template.name}'
        )
        
        flash('Template criado com sucesso!', 'success')
        return redirect(url_for('messaging_blueprint.templates_list'))
    
    return render_template(
        'messaging/templates/form.html',
        form=form,
        title='Novo Template'
    )


@blueprint.route('/templates/<int:template_id>/editar', methods=['GET', 'POST'])
@login_required
@permission_required('messaging.manage')
def template_edit(template_id):
    """Editar template"""
    template = MessageTemplate.query.get_or_404(template_id)
    form = MessageTemplateForm(obj=template)
    
    if form.validate_on_submit():
        old_values = {'name': template.name, 'body': template.body}
        
        template.name = form.name.data
        template.code = form.code.data or None
        template.category = form.category.data or None
        template.body = form.body.data
        template.is_active = form.is_active.data
        template.updated_by_id = current_user.id
        
        db.session.commit()
        
        AuditLog.log(
            action='update',
            table_name='message_templates',
            record_id=template.id,
            old_values=old_values,
            new_values={'name': template.name},
            description=f'Template atualizado: {template.name}'
        )
        
        flash('Template atualizado!', 'success')
        return redirect(url_for('messaging_blueprint.templates_list'))
    
    return render_template(
        'messaging/templates/form.html',
        form=form,
        template=template,
        title='Editar Template'
    )


@blueprint.route('/templates/<int:template_id>/excluir', methods=['POST'])
@login_required
@permission_required('messaging.manage')
def template_delete(template_id):
    """Excluir template (soft delete)"""
    template = MessageTemplate.query.get_or_404(template_id)
    
    template.soft_delete(current_user.id)
    
    AuditLog.log(
        action='delete',
        table_name='message_templates',
        record_id=template.id,
        old_values={'name': template.name},
        description=f'Template excluído: {template.name}'
    )
    
    flash('Template excluído!', 'success')
    return redirect(url_for('messaging_blueprint.templates_list'))


# =============================================================================
# WEBHOOK
# =============================================================================

@blueprint.route('/webhook', methods=['POST'])
def webhook_receiver():
    """
    Recebe eventos de webhook da API WhatsApp.
    
    Eventos suportados:
    - message.received: Nova mensagem recebida
    - message.sent: Mensagem enviada
    - message.media: Mídia recebida
    - ticket.created: Novo ticket
    - ticket.updated: Ticket atualizado
    - connection.status: Status da conexão mudou
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'received': False, 'error': 'No data'}), 400
    
    event = data.get('event')
    timestamp = data.get('timestamp')
    connection_data = data.get('connection', {})
    event_data = data.get('data', {})
    
    current_app.logger.info(f'Webhook recebido: {event} - {timestamp}')
    
    try:
        # Busca conexão local pelo número
        connection = None
        if connection_data.get('number'):
            connection = WhatsAppConnection.query.filter_by(
                phone_number=connection_data.get('number'),
                deleted_at=None
            ).first()
        
        # Processa evento
        if event in ['message.received', 'message.media']:
            # Nova mensagem recebida
            service = WhatsAppService(connection)
            message = service.sync_message_from_webhook(data)
            
            current_app.logger.info(f'Mensagem recebida salva: {message.id}')
            
        elif event == 'message.sent':
            # Atualiza status da mensagem enviada
            external_id = event_data.get('messageId')
            if external_id:
                message = WhatsAppMessage.query.filter_by(
                    external_message_id=external_id
                ).first()
                if message:
                    message.status = 'sent'
                    message.sent_at = datetime.utcnow()
                    db.session.commit()
        
        elif event == 'connection.status':
            # Atualiza status da conexão
            if connection:
                connection.status = event_data.get('newStatus', 'unknown')
                if connection.status == 'CONNECTED':
                    connection.last_connected_at = datetime.utcnow()
                db.session.commit()
        
        return jsonify({'received': True})
        
    except Exception as e:
        current_app.logger.error(f'Erro ao processar webhook: {e}')
        return jsonify({'received': False, 'error': str(e)}), 500
