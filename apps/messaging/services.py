# -*- encoding: utf-8 -*-
"""
Serviço de integração com API WhatsApp - Rocha Promotora
Base URL: https://wappbe2.rochapromotora.com.br
"""

import requests
import time
import os
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime
from flask import current_app

from apps import db
from apps.messaging.models import (
    WhatsAppConnection, WhatsAppContact, WhatsAppMessage, MessageQueue
)


class WhatsAppAPIError(Exception):
    """Exceção para erros da API WhatsApp"""
    
    def __init__(self, message: str, code: str = None, status_code: int = None):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(self.message)


class WhatsAppService:
    """
    Serviço de integração com API do WhatsApp.
    
    Implementa todos os endpoints documentados:
    - Mensagens (texto e mídia)
    - Contatos
    - Conexões
    - Rate Limiting
    - Tickets
    - Webhooks
    """
    
    def __init__(self, connection: WhatsAppConnection = None):
        """
        Inicializa o serviço.
        
        Args:
            connection: Conexão WhatsApp a usar. Se None, usa a padrão.
        """
        self.connection = connection or WhatsAppConnection.get_default()
        
        if self.connection:
            self.base_url = self.connection.api_base_url.rstrip('/')
            self.token = self.connection.api_token
        else:
            self.base_url = 'https://wappbe2.rochapromotora.com.br'
            self.token = None
    
    def _get_headers(self) -> Dict[str, str]:
        """Retorna headers com autenticação"""
        headers = {
            'Content-Type': 'application/json',
        }
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        return headers
    
    def _get_multipart_headers(self) -> Dict[str, str]:
        """Retorna headers para multipart/form-data"""
        headers = {}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        return headers
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Dict = None, 
        files: Dict = None,
        params: Dict = None
    ) -> Dict:
        """
        Faz requisição à API.
        
        Args:
            method: GET, POST, PUT, DELETE
            endpoint: Endpoint da API
            data: Dados para enviar (JSON)
            files: Arquivos para upload
            params: Query parameters
            
        Returns:
            Resposta da API como dicionário
            
        Raises:
            WhatsAppAPIError: Em caso de erro
        """
        url = f'{self.base_url}{endpoint}'
        
        try:
            if files:
                # Upload de arquivo
                response = requests.request(
                    method,
                    url,
                    headers=self._get_multipart_headers(),
                    data=data,
                    files=files,
                    params=params,
                    timeout=30
                )
            else:
                # Requisição JSON
                response = requests.request(
                    method,
                    url,
                    headers=self._get_headers(),
                    json=data,
                    params=params,
                    timeout=30
                )
            
            # Verifica erros HTTP
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    raise WhatsAppAPIError(
                        message=error_data.get('error', 'Erro desconhecido'),
                        code=error_data.get('code'),
                        status_code=response.status_code
                    )
                except ValueError:
                    raise WhatsAppAPIError(
                        message=response.text or 'Erro desconhecido',
                        status_code=response.status_code
                    )
            
            # Retorna resposta
            try:
                return response.json()
            except ValueError:
                return {'success': True, 'raw': response.text}
                
        except requests.exceptions.Timeout:
            raise WhatsAppAPIError('Timeout na requisição', code='TIMEOUT')
        except requests.exceptions.ConnectionError:
            raise WhatsAppAPIError('Erro de conexão com a API', code='CONNECTION_ERROR')
        except requests.exceptions.RequestException as e:
            raise WhatsAppAPIError(str(e), code='REQUEST_ERROR')
    
    # =========================================================================
    # MENSAGENS
    # =========================================================================
    
    def send_text_message(
        self, 
        number: str, 
        body: str,
        save_to_db: bool = True,
        user_id: int = None
    ) -> Tuple[Dict, Optional[WhatsAppMessage]]:
        """
        Envia mensagem de texto.
        
        POST /api/v1/messages/text
        
        Args:
            number: Número do destinatário (55DDDNUMERO)
            body: Corpo da mensagem
            save_to_db: Se deve salvar no banco
            user_id: ID do usuário que está enviando
            
        Returns:
            Tupla com (resposta_api, mensagem_db)
        """
        # Normaliza número
        number = self._normalize_phone(number)
        
        response = self._make_request(
            'POST',
            '/api/v1/messages/text',
            data={'number': number, 'body': body}
        )
        
        message = None
        if save_to_db:
            message = WhatsAppMessage(
                external_message_id=response.get('data', {}).get('messageId'),
                connection_id=self.connection.id if self.connection else None,
                phone_number=number,
                body=body,
                media_type='chat',
                direction='outgoing',
                status='queued' if response.get('success') else 'failed',
                from_me=True,
                sent_by_id=user_id,
                sent_at=datetime.utcnow()
            )
            db.session.add(message)
            db.session.commit()
        
        return response, message
    
    def send_media_message(
        self,
        number: str,
        file_path: str = None,
        file_data: bytes = None,
        filename: str = None,
        caption: str = None,
        save_to_db: bool = True,
        user_id: int = None
    ) -> Tuple[Dict, Optional[WhatsAppMessage]]:
        """
        Envia mídia (imagem, documento, áudio, vídeo).
        
        POST /api/v1/messages/media
        
        Args:
            number: Número do destinatário
            file_path: Caminho do arquivo (opcional se file_data fornecido)
            file_data: Bytes do arquivo (opcional se file_path fornecido)
            filename: Nome do arquivo
            caption: Legenda da mídia
            save_to_db: Se deve salvar no banco
            user_id: ID do usuário que está enviando
            
        Returns:
            Tupla com (resposta_api, mensagem_db)
        """
        number = self._normalize_phone(number)
        
        # Prepara arquivo
        if file_path:
            with open(file_path, 'rb') as f:
                file_data = f.read()
            if not filename:
                filename = os.path.basename(file_path)
        
        if not file_data or not filename:
            raise WhatsAppAPIError('Arquivo não fornecido', code='MISSING_FILE')
        
        # Faz upload
        files = {'medias': (filename, file_data)}
        data = {'number': number}
        if caption:
            data['body'] = caption
        
        response = self._make_request(
            'POST',
            '/api/v1/messages/media',
            data=data,
            files=files
        )
        
        message = None
        if save_to_db:
            media_type = response.get('data', {}).get('mediaType', 'document')
            message = WhatsAppMessage(
                external_message_id=response.get('data', {}).get('messageId'),
                connection_id=self.connection.id if self.connection else None,
                phone_number=number,
                body=caption,
                media_type=media_type,
                direction='outgoing',
                status='queued' if response.get('success') else 'failed',
                from_me=True,
                sent_by_id=user_id,
                sent_at=datetime.utcnow()
            )
            db.session.add(message)
            db.session.commit()
        
        return response, message
    
    def get_messages_by_contact(
        self, 
        number: str, 
        limit: int = 50, 
        offset: int = 0
    ) -> Dict:
        """
        Busca mensagens de um contato.
        
        GET /api/v1/messages/by-contact
        
        Args:
            number: Número do contato
            limit: Quantidade de mensagens
            offset: Paginação
            
        Returns:
            Resposta com lista de mensagens
        """
        return self._make_request(
            'GET',
            '/api/v1/messages/by-contact',
            params={
                'number': self._normalize_phone(number),
                'limit': limit,
                'offset': offset
            }
        )
    
    # =========================================================================
    # CONTATOS
    # =========================================================================
    
    def check_number(self, number: str) -> Dict:
        """
        Verifica se número tem WhatsApp.
        
        POST /api/v1/contacts/check
        
        Args:
            number: Número a verificar
            
        Returns:
            Resposta com exists, jid e name
        """
        return self._make_request(
            'POST',
            '/api/v1/contacts/check',
            data={'number': self._normalize_phone(number)}
        )
    
    def list_contacts(
        self, 
        search: str = None, 
        limit: int = 50, 
        offset: int = 0
    ) -> Dict:
        """
        Lista contatos.
        
        GET /api/v1/contacts
        
        Args:
            search: Buscar por nome ou número
            limit: Quantidade
            offset: Paginação
            
        Returns:
            Lista de contatos
        """
        params = {'limit': limit, 'offset': offset}
        if search:
            params['search'] = search
            
        return self._make_request('GET', '/api/v1/contacts', params=params)
    
    def create_or_update_contact(
        self, 
        number: str, 
        name: str = None, 
        email: str = None
    ) -> Dict:
        """
        Cria ou atualiza contato.
        
        POST /api/v1/contacts
        
        Args:
            number: Número do contato
            name: Nome
            email: Email
            
        Returns:
            Dados do contato
        """
        data = {'number': self._normalize_phone(number)}
        if name:
            data['name'] = name
        if email:
            data['email'] = email
            
        return self._make_request('POST', '/api/v1/contacts', data=data)
    
    # =========================================================================
    # CONEXÕES
    # =========================================================================
    
    def list_connections(self) -> Dict:
        """
        Lista conexões WhatsApp.
        
        GET /api/v1/connections
        """
        return self._make_request('GET', '/api/v1/connections')
    
    def get_connection_status(self) -> Dict:
        """
        Status da conexão atual.
        
        GET /api/v1/connections/status
        """
        return self._make_request('GET', '/api/v1/connections/status')
    
    def create_connection(self, name: str, is_default: bool = False) -> Dict:
        """
        Cria nova conexão.
        
        POST /api/v1/connections
        
        Args:
            name: Nome da conexão
            is_default: Se é a padrão
        """
        return self._make_request(
            'POST',
            '/api/v1/connections',
            data={'name': name, 'isDefault': is_default}
        )
    
    def get_qrcode(self, connection_id: int) -> Dict:
        """
        Obtém QR Code para conectar.
        
        GET /api/v1/connections/:id/qrcode
        
        Args:
            connection_id: ID da conexão
        """
        return self._make_request('GET', f'/api/v1/connections/{connection_id}/qrcode')
    
    def restart_connection(self, connection_id: int) -> Dict:
        """
        Reinicia conexão.
        
        POST /api/v1/connections/:id/restart
        """
        return self._make_request('POST', f'/api/v1/connections/{connection_id}/restart')
    
    def disconnect(self, connection_id: int) -> Dict:
        """
        Desconecta sessão.
        
        POST /api/v1/connections/:id/disconnect
        """
        return self._make_request('POST', f'/api/v1/connections/{connection_id}/disconnect')
    
    def delete_connection(self, connection_id: int) -> Dict:
        """
        Remove conexão.
        
        DELETE /api/v1/connections/:id
        """
        return self._make_request('DELETE', f'/api/v1/connections/{connection_id}')
    
    # =========================================================================
    # RATE LIMITING
    # =========================================================================
    
    def get_rate_limit(self, connection_id: int) -> Dict:
        """
        Obtém configurações de rate limit.
        
        GET /api/v1/connections/:id/rate-limit
        """
        return self._make_request('GET', f'/api/v1/connections/{connection_id}/rate-limit')
    
    def update_rate_limit(
        self,
        connection_id: int,
        enabled: bool = True,
        max_per_minute: int = 5,
        max_per_hour: int = 100,
        min_delay: int = 15000,
        max_delay: int = 20000
    ) -> Dict:
        """
        Atualiza configurações de rate limit.
        
        PUT /api/v1/connections/:id/rate-limit
        
        Args:
            connection_id: ID da conexão
            enabled: Se rate limiting está ativo
            max_per_minute: Máximo mensagens por minuto
            max_per_hour: Máximo mensagens por hora
            min_delay: Delay mínimo (ms)
            max_delay: Delay máximo (ms)
        """
        return self._make_request(
            'PUT',
            f'/api/v1/connections/{connection_id}/rate-limit',
            data={
                'rateLimitEnabled': enabled,
                'maxMessagesPerMinute': max_per_minute,
                'maxMessagesPerHour': max_per_hour,
                'minDelay': min_delay,
                'maxDelay': max_delay
            }
        )
    
    def clear_queue(self, connection_id: int) -> Dict:
        """
        Limpa fila de mensagens.
        
        DELETE /api/v1/connections/:id/queue
        """
        return self._make_request('DELETE', f'/api/v1/connections/{connection_id}/queue')
    
    def reset_rate_limit_counters(self, connection_id: int) -> Dict:
        """
        Reseta contadores de rate limit.
        
        POST /api/v1/connections/:id/rate-limit/reset
        """
        return self._make_request('POST', f'/api/v1/connections/{connection_id}/rate-limit/reset')
    
    # =========================================================================
    # TICKETS
    # =========================================================================
    
    def list_tickets(
        self, 
        status: str = None, 
        limit: int = 50, 
        offset: int = 0
    ) -> Dict:
        """
        Lista tickets/conversas.
        
        GET /api/v1/tickets
        
        Args:
            status: open, pending, closed
            limit: Quantidade
            offset: Paginação
        """
        params = {'limit': limit, 'offset': offset}
        if status:
            params['status'] = status
            
        return self._make_request('GET', '/api/v1/tickets', params=params)
    
    def get_ticket_messages(
        self, 
        ticket_id: int, 
        limit: int = 50, 
        offset: int = 0
    ) -> Dict:
        """
        Mensagens de um ticket.
        
        GET /api/v1/tickets/:ticketId/messages
        """
        return self._make_request(
            'GET',
            f'/api/v1/tickets/{ticket_id}/messages',
            params={'limit': limit, 'offset': offset}
        )
    
    def update_ticket(
        self, 
        ticket_id: int, 
        status: str = None, 
        user_id: int = None
    ) -> Dict:
        """
        Atualiza ticket.
        
        PUT /api/v1/tickets/:ticketId
        
        Args:
            ticket_id: ID do ticket
            status: open, pending, closed
            user_id: ID do usuário atribuído
        """
        data = {}
        if status:
            data['status'] = status
        if user_id:
            data['userId'] = user_id
            
        return self._make_request('PUT', f'/api/v1/tickets/{ticket_id}', data=data)
    
    # =========================================================================
    # WEBHOOK
    # =========================================================================
    
    def configure_webhook(self, url: str) -> Dict:
        """
        Configura webhook.
        
        PUT /api/v1/webhook
        
        Args:
            url: URL para receber eventos
        """
        return self._make_request('PUT', '/api/v1/webhook', data={'webhookUrl': url})
    
    def get_webhook(self) -> Dict:
        """
        Consulta webhook configurado.
        
        GET /api/v1/webhook
        """
        return self._make_request('GET', '/api/v1/webhook')
    
    # =========================================================================
    # UTILITÁRIOS
    # =========================================================================
    
    def _normalize_phone(self, phone: str) -> str:
        """
        Normaliza número de telefone.
        Remove caracteres especiais e adiciona código do país se necessário.
        
        Args:
            phone: Número original
            
        Returns:
            Número normalizado (apenas dígitos, com código do país)
        """
        # Remove tudo que não é dígito
        digits = ''.join(filter(str.isdigit, phone))
        
        # Adiciona código do país se não tiver
        if len(digits) <= 11:  # Número nacional (DDD + número)
            digits = '55' + digits
        
        return digits
    
    def sync_contact_from_api(self, api_contact: Dict) -> WhatsAppContact:
        """
        Sincroniza contato da API com banco local.
        
        Args:
            api_contact: Dados do contato da API
            
        Returns:
            Contato salvo no banco
        """
        phone = self._normalize_phone(api_contact.get('number', ''))
        
        contact = WhatsAppContact.query.filter_by(
            phone_number=phone,
            connection_id=self.connection.id if self.connection else None
        ).first()
        
        if not contact:
            contact = WhatsAppContact(
                phone_number=phone,
                connection_id=self.connection.id if self.connection else None
            )
            db.session.add(contact)
        
        # Atualiza dados
        contact.name = api_contact.get('name') or contact.name
        contact.email = api_contact.get('email') or contact.email
        contact.profile_pic_url = api_contact.get('profilePicUrl') or contact.profile_pic_url
        contact.whatsapp_jid = api_contact.get('jid') or contact.whatsapp_jid
        
        db.session.commit()
        return contact
    
    def sync_message_from_webhook(self, event_data: Dict) -> WhatsAppMessage:
        """
        Processa evento de webhook e salva mensagem.
        
        Args:
            event_data: Dados do evento de webhook
            
        Returns:
            Mensagem salva
        """
        data = event_data.get('data', {})
        
        # Determina direção
        from_me = data.get('fromMe', False)
        direction = 'outgoing' if from_me else 'incoming'
        
        # Busca ou cria contato
        phone = data.get('from') or data.get('to')
        if phone:
            phone = self._normalize_phone(phone)
            contact = WhatsAppContact.query.filter_by(
                phone_number=phone,
                connection_id=self.connection.id if self.connection else None
            ).first()
            
            if not contact:
                contact = WhatsAppContact(
                    phone_number=phone,
                    name=data.get('fromName'),
                    connection_id=self.connection.id if self.connection else None
                )
                db.session.add(contact)
                db.session.flush()
        
        # Cria mensagem
        message = WhatsAppMessage(
            external_message_id=data.get('messageId'),
            ticket_id=data.get('ticket', {}).get('id'),
            contact_id=contact.id if contact else None,
            connection_id=self.connection.id if self.connection else None,
            phone_number=phone,
            body=data.get('body'),
            media_type=data.get('mediaType', 'chat'),
            media_url=data.get('mediaUrl'),
            media_mimetype=data.get('mimetype'),
            direction=direction,
            status='received' if not from_me else 'sent',
            from_me=from_me,
            is_read=data.get('read', False),
            created_at=datetime.utcnow()
        )
        
        db.session.add(message)
        db.session.commit()
        
        return message
