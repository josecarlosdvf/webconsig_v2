# API de Integração WhatsApp - Rocha Promotora

## Visão Geral

Esta API permite integrar seu CRM ou sistema externo com o WhatsApp através da plataforma Rocha Promotora. Com ela você pode enviar mensagens, gerenciar conexões, configurar webhooks para receber notificações de mensagens e controlar limites de envio.

**Base URL:** `https://wappbe2.rochapromotora.com.br`

---

## Autenticação

Todas as requisições devem incluir o header de autenticação com o token da conexão WhatsApp.

```
Authorization: Bearer SEU_TOKEN_AQUI
```

O token é configurado na edição de cada conexão WhatsApp através do painel administrativo (Menu Conexões > Editar).

---

## Endpoints

### 1. Mensagens

#### 1.1 Enviar Mensagem de Texto

Envia uma mensagem de texto para um número de WhatsApp.

**Endpoint:** `POST /api/v1/messages/text`

**Headers:**
```
Authorization: Bearer SEU_TOKEN
Content-Type: application/json
```

**Body:**
```json
{
  "number": "5521999998888",
  "body": "Olá! Esta é uma mensagem de teste."
}
```

**Resposta de Sucesso (200):**
```json
{
  "success": true,
  "message": "Mensagem enfileirada para envio",
  "data": {
    "messageId": "3EB0A1B2C3D4E5F6",
    "queuePosition": 1,
    "estimatedDelivery": "2025-11-29T12:00:30.000Z"
  }
}
```

**Observações:**
- O número deve incluir código do país (55 para Brasil) + DDD + número
- Não usar máscaras, parênteses ou traços
- Mensagens são enfileiradas e enviadas respeitando os limites de rate limiting

---

#### 1.2 Enviar Mídia (Imagem, Documento, Áudio, Vídeo)

Envia arquivos de mídia para um número de WhatsApp.

**Endpoint:** `POST /api/v1/messages/media`

**Headers:**
```
Authorization: Bearer SEU_TOKEN
Content-Type: multipart/form-data
```

**Form Data:**
| Campo | Tipo | Descrição |
|-------|------|-----------|
| number | string | Número do destinatário (5521999998888) |
| body | string | Legenda da mídia (opcional) |
| medias | file | Arquivo a ser enviado |

**Exemplo com cURL:**
```bash
curl -X POST "https://wappbe2.rochapromotora.com.br/api/v1/messages/media" \
  -H "Authorization: Bearer SEU_TOKEN" \
  -F "number=5521999998888" \
  -F "body=Segue o documento solicitado" \
  -F "medias=@/caminho/para/arquivo.pdf"
```

**Resposta de Sucesso (200):**
```json
{
  "success": true,
  "message": "Mídia enfileirada para envio",
  "data": {
    "messageId": "3EB0A1B2C3D4E5F7",
    "mediaType": "document",
    "queuePosition": 2
  }
}
```

**Tipos de mídia suportados:**
- Imagens: jpg, jpeg, png, gif, webp
- Documentos: pdf, doc, docx, xls, xlsx, txt
- Áudio: mp3, ogg, wav, m4a
- Vídeo: mp4, 3gp, mov

---

#### 1.3 Buscar Mensagens por Contato

Retorna o histórico de mensagens de um contato.

**Endpoint:** `GET /api/v1/messages/by-contact`

**Query Parameters:**
| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| number | string | Sim | Número do contato |
| limit | number | Não | Quantidade de mensagens (padrão: 50) |
| offset | number | Não | Paginação |

**Exemplo:**
```
GET /api/v1/messages/by-contact?number=5521999998888&limit=20
```

**Resposta:**
```json
{
  "success": true,
  "messages": [
    {
      "id": 12345,
      "body": "Olá, bom dia!",
      "fromMe": false,
      "mediaType": "chat",
      "createdAt": "2025-11-29T10:30:00.000Z",
      "read": true
    },
    {
      "id": 12346,
      "body": "Bom dia! Como posso ajudar?",
      "fromMe": true,
      "mediaType": "chat",
      "createdAt": "2025-11-29T10:31:00.000Z",
      "read": true
    }
  ],
  "total": 150,
  "hasMore": true
}
```

---

### 2. Contatos

#### 2.1 Verificar Número no WhatsApp

Verifica se um número possui conta no WhatsApp.

**Endpoint:** `POST /api/v1/contacts/check`

**Body:**
```json
{
  "number": "5521999998888"
}
```

**Resposta:**
```json
{
  "success": true,
  "exists": true,
  "jid": "5521999998888@s.whatsapp.net",
  "name": "João Silva"
}
```

---

#### 2.2 Listar Contatos

Retorna lista de contatos cadastrados.

**Endpoint:** `GET /api/v1/contacts`

**Query Parameters:**
| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| search | string | Buscar por nome ou número |
| limit | number | Quantidade (padrão: 50) |
| offset | number | Paginação |

**Resposta:**
```json
{
  "success": true,
  "contacts": [
    {
      "id": 1,
      "name": "João Silva",
      "number": "5521999998888",
      "email": "joao@email.com",
      "profilePicUrl": "https://...",
      "isGroup": false,
      "createdAt": "2025-01-15T10:00:00.000Z"
    }
  ],
  "total": 1500,
  "hasMore": true
}
```

---

#### 2.3 Criar/Atualizar Contato

Cria um novo contato ou atualiza existente.

**Endpoint:** `POST /api/v1/contacts`

**Body:**
```json
{
  "name": "Maria Santos",
  "number": "5521988887777",
  "email": "maria@email.com"
}
```

**Resposta:**
```json
{
  "success": true,
  "contact": {
    "id": 123,
    "name": "Maria Santos",
    "number": "5521988887777",
    "email": "maria@email.com",
    "createdAt": "2025-11-29T12:00:00.000Z"
  },
  "created": true
}
```

---

### 3. Conexões (WhatsApp)

#### 3.1 Listar Conexões

Lista todas as conexões WhatsApp disponíveis.

**Endpoint:** `GET /api/v1/connections`

**Resposta:**
```json
{
  "success": true,
  "connections": [
    {
      "id": 1,
      "name": "Atendimento Principal",
      "status": "CONNECTED",
      "number": "5521999998888",
      "battery": "85",
      "plugged": true,
      "isConnected": true,
      "createdAt": "2025-01-10T08:00:00.000Z"
    },
    {
      "id": 2,
      "name": "Vendas",
      "status": "qrcode",
      "number": "",
      "isConnected": false
    }
  ]
}
```

**Status possíveis:**
- `CONNECTED` / `open` - Conectado e funcionando
- `qrcode` - Aguardando leitura do QR Code
- `DISCONNECTED` - Desconectado
- `OPENING` - Iniciando conexão

---

#### 3.2 Status da Conexão Atual

Retorna status detalhado da conexão vinculada ao token.

**Endpoint:** `GET /api/v1/connections/status`

**Resposta:**
```json
{
  "success": true,
  "connection": {
    "id": 1,
    "name": "Atendimento Principal",
    "status": "CONNECTED",
    "number": "5521999998888",
    "isDefault": true
  }
}
```

---

#### 3.3 Criar Nova Conexão

Cria uma nova conexão WhatsApp.

**Endpoint:** `POST /api/v1/connections`

**Body:**
```json
{
  "name": "Nova Conexão",
  "isDefault": false
}
```

**Resposta:**
```json
{
  "success": true,
  "connection": {
    "id": 5,
    "name": "Nova Conexão",
    "status": "OPENING",
    "token": "TOKEN_GERADO_AUTOMATICAMENTE"
  },
  "message": "Conexão criada. Escaneie o QR Code para conectar."
}
```

---

#### 3.4 Obter QR Code

Obtém o QR Code para conectar uma sessão.

**Endpoint:** `GET /api/v1/connections/:id/qrcode`

**Resposta:**
```json
{
  "success": true,
  "qrcode": "data:image/png;base64,iVBORw0KGgo...",
  "status": "qrcode",
  "expiresIn": 60
}
```

**Observação:** O QR Code expira em aproximadamente 60 segundos. Caso expire, chame o endpoint de restart.

---

#### 3.5 Reiniciar Conexão

Reinicia a conexão e gera novo QR Code.

**Endpoint:** `POST /api/v1/connections/:id/restart`

**Resposta:**
```json
{
  "success": true,
  "message": "Conexão reiniciada. Aguarde o novo QR Code."
}
```

---

#### 3.6 Desconectar (Logout)

Desconecta a sessão do WhatsApp.

**Endpoint:** `POST /api/v1/connections/:id/disconnect`

**Resposta:**
```json
{
  "success": true,
  "message": "Sessão desconectada com sucesso"
}
```

---

#### 3.7 Remover Conexão

Remove permanentemente uma conexão.

**Endpoint:** `DELETE /api/v1/connections/:id`

**Resposta:**
```json
{
  "success": true,
  "message": "Conexão removida com sucesso"
}
```

---

### 4. Rate Limiting (Controle de Envio)

O sistema possui controle de rate limiting para evitar bloqueios pelo WhatsApp/Meta.

#### 4.1 Obter Configurações de Rate Limit

**Endpoint:** `GET /api/v1/connections/:id/rate-limit`

**Resposta:**
```json
{
  "success": true,
  "connection": {
    "id": 1,
    "name": "Atendimento Principal",
    "status": "CONNECTED"
  },
  "rateLimiting": {
    "enabled": true,
    "config": {
      "maxMessagesPerMinute": 5,
      "maxMessagesPerHour": 100,
      "minDelay": 15000,
      "maxDelay": 20000
    },
    "current": {
      "messagesThisMinute": 3,
      "messagesThisHour": 45,
      "queuedMessages": 10,
      "isProcessing": true,
      "lastMessageSentAt": "2025-11-29T12:30:15.000Z"
    },
    "limits": {
      "minuteUsage": "3/5",
      "hourUsage": "45/100",
      "minutePercentage": 60,
      "hourPercentage": 45
    }
  }
}
```

**Campos de configuração:**
| Campo | Tipo | Descrição |
|-------|------|-----------|
| maxMessagesPerMinute | number | Máximo de mensagens por minuto |
| maxMessagesPerHour | number | Máximo de mensagens por hora |
| minDelay | number | Intervalo mínimo entre mensagens (ms) |
| maxDelay | number | Intervalo máximo entre mensagens (ms) |

---

#### 4.2 Atualizar Configurações de Rate Limit

**Endpoint:** `PUT /api/v1/connections/:id/rate-limit`

**Body:**
```json
{
  "rateLimitEnabled": true,
  "maxMessagesPerMinute": 5,
  "maxMessagesPerHour": 100,
  "minDelay": 15000,
  "maxDelay": 20000
}
```

**Valores Recomendados:**
- `maxMessagesPerMinute`: 5-10
- `maxMessagesPerHour`: 100-200
- `minDelay`: 15000-20000 (15-20 segundos)
- `maxDelay`: 20000-30000 (20-30 segundos)

**Resposta:**
```json
{
  "success": true,
  "message": "Configurações de rate limiting atualizadas",
  "rateLimiting": {
    "enabled": true,
    "maxMessagesPerMinute": 5,
    "maxMessagesPerHour": 100,
    "minDelay": 15000,
    "maxDelay": 20000
  }
}
```

---

#### 4.3 Limpar Fila de Mensagens

Remove todas as mensagens pendentes na fila.

**Endpoint:** `DELETE /api/v1/connections/:id/queue`

**Resposta:**
```json
{
  "success": true,
  "message": "Fila limpa com sucesso",
  "clearedMessages": 15
}
```

---

#### 4.4 Resetar Contadores

Zera os contadores de mensagens por minuto/hora.

**Endpoint:** `POST /api/v1/connections/:id/rate-limit/reset`

**Resposta:**
```json
{
  "success": true,
  "message": "Contadores resetados com sucesso"
}
```

---

### 5. Tickets (Conversas)

#### 5.1 Listar Tickets

Lista as conversas/tickets.

**Endpoint:** `GET /api/v1/tickets`

**Query Parameters:**
| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| status | string | open, pending, closed |
| limit | number | Quantidade (padrão: 50) |
| offset | number | Paginação |

**Resposta:**
```json
{
  "success": true,
  "tickets": [
    {
      "id": 123,
      "status": "open",
      "lastMessage": "Obrigado pelo atendimento!",
      "unreadMessages": 2,
      "contact": {
        "id": 45,
        "name": "João Silva",
        "number": "5521999998888",
        "profilePicUrl": "https://..."
      },
      "user": {
        "id": 1,
        "name": "Atendente Maria"
      },
      "whatsapp": {
        "id": 1,
        "name": "Atendimento Principal"
      },
      "createdAt": "2025-11-29T10:00:00.000Z",
      "updatedAt": "2025-11-29T12:30:00.000Z"
    }
  ],
  "total": 250,
  "hasMore": true
}
```

---

#### 5.2 Mensagens de um Ticket

Retorna mensagens de um ticket específico.

**Endpoint:** `GET /api/v1/tickets/:ticketId/messages`

**Query Parameters:**
| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| limit | number | Quantidade (padrão: 50) |
| offset | number | Paginação |

**Resposta:**
```json
{
  "success": true,
  "messages": [
    {
      "id": 1001,
      "body": "Olá, preciso de ajuda",
      "fromMe": false,
      "mediaType": "chat",
      "read": true,
      "createdAt": "2025-11-29T10:00:00.000Z"
    },
    {
      "id": 1002,
      "body": "Claro! Em que posso ajudar?",
      "fromMe": true,
      "mediaType": "chat",
      "read": true,
      "createdAt": "2025-11-29T10:01:00.000Z"
    }
  ],
  "total": 25
}
```

---

#### 5.3 Atualizar Ticket

Atualiza status ou atribuição de um ticket.

**Endpoint:** `PUT /api/v1/tickets/:ticketId`

**Body:**
```json
{
  "status": "closed",
  "userId": 2
}
```

**Status válidos:**
- `open` - Aberto/Em atendimento
- `pending` - Aguardando
- `closed` - Fechado

---

### 6. Webhook

Configure webhooks para receber notificações em tempo real de eventos.

#### 6.1 Configurar Webhook

**Endpoint:** `PUT /api/v1/webhook`

**Body:**
```json
{
  "webhookUrl": "https://seu-crm.com.br/webhook/whatsapp"
}
```

**Resposta:**
```json
{
  "success": true,
  "message": "Webhook configurado com sucesso",
  "webhookUrl": "https://seu-crm.com.br/webhook/whatsapp"
}
```

---

#### 6.2 Consultar Webhook

**Endpoint:** `GET /api/v1/webhook`

**Resposta:**
```json
{
  "success": true,
  "webhookUrl": "https://seu-crm.com.br/webhook/whatsapp",
  "configured": true
}
```

---

## Eventos de Webhook

Quando uma mensagem é recebida ou um evento ocorre, uma requisição POST é enviada para sua URL de webhook.

### Estrutura do Payload

```json
{
  "event": "message.received",
  "timestamp": "2025-11-29T12:30:00.000Z",
  "connection": {
    "id": 1,
    "name": "Atendimento Principal",
    "number": "5521999998888"
  },
  "data": {
    // Dados específicos do evento
  }
}
```

### Tipos de Eventos

#### message.received
Disparado quando uma nova mensagem é recebida.

```json
{
  "event": "message.received",
  "timestamp": "2025-11-29T12:30:00.000Z",
  "connection": {
    "id": 1,
    "name": "Atendimento Principal",
    "number": "5521999998888"
  },
  "data": {
    "messageId": "3EB0A1B2C3D4E5F6",
    "from": "5521988887777",
    "fromName": "João Silva",
    "body": "Olá, bom dia!",
    "mediaType": "chat",
    "timestamp": "2025-11-29T12:30:00.000Z",
    "isGroup": false,
    "ticket": {
      "id": 123,
      "status": "open"
    },
    "contact": {
      "id": 45,
      "name": "João Silva",
      "number": "5521988887777"
    }
  }
}
```

#### message.sent
Disparado quando uma mensagem é enviada com sucesso.

```json
{
  "event": "message.sent",
  "timestamp": "2025-11-29T12:31:00.000Z",
  "connection": {
    "id": 1,
    "name": "Atendimento Principal"
  },
  "data": {
    "messageId": "3EB0A1B2C3D4E5F7",
    "to": "5521988887777",
    "body": "Bom dia! Como posso ajudar?",
    "mediaType": "chat",
    "status": "sent"
  }
}
```

#### message.media
Disparado quando uma mídia é recebida.

```json
{
  "event": "message.media",
  "timestamp": "2025-11-29T12:32:00.000Z",
  "connection": {
    "id": 1,
    "name": "Atendimento Principal"
  },
  "data": {
    "messageId": "3EB0A1B2C3D4E5F8",
    "from": "5521988887777",
    "mediaType": "image",
    "mimetype": "image/jpeg",
    "caption": "Foto do documento",
    "mediaUrl": "https://wappbe2.rochapromotora.com.br/public/media/123456.jpg",
    "ticket": {
      "id": 123,
      "status": "open"
    }
  }
}
```

#### ticket.created
Disparado quando um novo ticket/conversa é criado.

```json
{
  "event": "ticket.created",
  "timestamp": "2025-11-29T12:30:00.000Z",
  "connection": {
    "id": 1,
    "name": "Atendimento Principal"
  },
  "data": {
    "ticketId": 124,
    "status": "pending",
    "contact": {
      "id": 46,
      "name": "Maria Santos",
      "number": "5521977776666"
    }
  }
}
```

#### ticket.updated
Disparado quando um ticket é atualizado (status, atribuição, etc).

```json
{
  "event": "ticket.updated",
  "timestamp": "2025-11-29T12:45:00.000Z",
  "connection": {
    "id": 1,
    "name": "Atendimento Principal"
  },
  "data": {
    "ticketId": 123,
    "oldStatus": "open",
    "newStatus": "closed",
    "user": {
      "id": 1,
      "name": "Atendente Maria"
    }
  }
}
```

#### connection.status
Disparado quando o status da conexão muda.

```json
{
  "event": "connection.status",
  "timestamp": "2025-11-29T13:00:00.000Z",
  "connection": {
    "id": 1,
    "name": "Atendimento Principal"
  },
  "data": {
    "oldStatus": "CONNECTED",
    "newStatus": "DISCONNECTED",
    "reason": "Sessão encerrada pelo dispositivo"
  }
}
```

---

## Implementando o Webhook no seu CRM

### Exemplo em PHP

```php
<?php
// webhook.php

$payload = file_get_contents('php://input');
$data = json_decode($payload, true);

// Log do evento
file_put_contents('webhook.log', date('Y-m-d H:i:s') . " - " . $payload . "\n", FILE_APPEND);

// Processar eventos
switch ($data['event']) {
    case 'message.received':
        $from = $data['data']['from'];
        $body = $data['data']['body'];
        $ticketId = $data['data']['ticket']['id'];
        
        // Salvar no banco de dados
        $pdo->prepare("INSERT INTO mensagens (from_number, body, ticket_id, created_at) VALUES (?, ?, ?, NOW())")
            ->execute([$from, $body, $ticketId]);
        
        // Notificar atendentes
        // ...
        break;
        
    case 'ticket.created':
        $contactName = $data['data']['contact']['name'];
        $contactNumber = $data['data']['contact']['number'];
        
        // Criar registro no CRM
        // ...
        break;
        
    case 'connection.status':
        if ($data['data']['newStatus'] === 'DISCONNECTED') {
            // Alertar administrador
            mail('admin@empresa.com', 'WhatsApp Desconectado', 'A conexão foi perdida.');
        }
        break;
}

// Responder com 200 OK
http_response_code(200);
echo json_encode(['received' => true]);
```

### Exemplo em Node.js

```javascript
const express = require('express');
const app = express();

app.use(express.json());

app.post('/webhook/whatsapp', (req, res) => {
  const { event, data, connection, timestamp } = req.body;
  
  console.log(`[${timestamp}] Evento: ${event}`);
  
  switch (event) {
    case 'message.received':
      console.log(`Mensagem de ${data.from}: ${data.body}`);
      // Processar mensagem recebida
      // Integrar com seu CRM
      break;
      
    case 'message.sent':
      console.log(`Mensagem enviada para ${data.to}`);
      break;
      
    case 'ticket.created':
      console.log(`Novo ticket: ${data.ticketId}`);
      // Criar lead no CRM
      break;
      
    case 'connection.status':
      console.log(`Status: ${data.oldStatus} -> ${data.newStatus}`);
      if (data.newStatus === 'DISCONNECTED') {
        // Alertar equipe
      }
      break;
  }
  
  res.json({ received: true });
});

app.listen(3000, () => {
  console.log('Webhook server running on port 3000');
});
```

### Exemplo em Python

```python
from flask import Flask, request, jsonify
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route('/webhook/whatsapp', methods=['POST'])
def webhook():
    data = request.json
    event = data.get('event')
    
    logging.info(f"Evento recebido: {event}")
    
    if event == 'message.received':
        message_data = data['data']
        from_number = message_data['from']
        body = message_data['body']
        
        logging.info(f"Mensagem de {from_number}: {body}")
        
        # Processar mensagem
        # Salvar no banco
        # Notificar equipe
        
    elif event == 'ticket.created':
        ticket_data = data['data']
        contact = ticket_data['contact']
        
        logging.info(f"Novo ticket de {contact['name']}")
        
        # Criar lead no CRM
        
    elif event == 'connection.status':
        status_data = data['data']
        new_status = status_data['newStatus']
        
        if new_status == 'DISCONNECTED':
            # Enviar alerta
            pass
    
    return jsonify({'received': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

---

## Códigos de Erro

| Código | Descrição |
|--------|-----------|
| 400 | Requisição inválida (parâmetros faltando ou inválidos) |
| 401 | Token inválido ou não fornecido |
| 403 | Acesso não permitido |
| 404 | Recurso não encontrado |
| 429 | Rate limit excedido |
| 500 | Erro interno do servidor |

### Exemplo de Erro

```json
{
  "error": "Número inválido",
  "code": "INVALID_NUMBER",
  "details": "O número deve conter apenas dígitos e incluir código do país"
}
```

---

## Limites e Boas Práticas

### Rate Limiting

Para evitar bloqueios pelo WhatsApp/Meta, siga estas recomendações:

1. **Intervalo entre mensagens:** Mínimo de 15-20 segundos
2. **Mensagens por minuto:** Máximo de 5-10
3. **Mensagens por hora:** Máximo de 100-200
4. **Variação randômica:** Configure minDelay e maxDelay para simular comportamento humano

### Dicas de Uso

1. **Sempre verifique o número** antes de enviar usando `/api/v1/contacts/check`
2. **Monitore o webhook** para detectar conexões perdidas
3. **Implemente retry** com backoff exponencial para falhas temporárias
4. **Armazene messageIds** para rastreamento de entregas
5. **Use a fila** - mensagens são automaticamente enfileiradas

---

## Exemplos de Integração

### Envio Simples com cURL

```bash
# Enviar mensagem de texto
curl -X POST "https://wappbe2.rochapromotora.com.br/api/v1/messages/text" \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"number": "5521999998888", "body": "Olá! Teste de integração."}'

# Verificar número
curl -X POST "https://wappbe2.rochapromotora.com.br/api/v1/contacts/check" \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"number": "5521999998888"}'

# Listar conexões
curl -X GET "https://wappbe2.rochapromotora.com.br/api/v1/connections" \
  -H "Authorization: Bearer SEU_TOKEN"

# Configurar webhook
curl -X PUT "https://wappbe2.rochapromotora.com.br/api/v1/webhook" \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"webhookUrl": "https://seu-crm.com.br/webhook"}'
```

---

## Suporte

Em caso de dúvidas ou problemas:

- **Email:** suporte@rochapromotora.com.br
- **WhatsApp:** (21) 99999-8888

---

*Documentação atualizada em: 29 de Novembro de 2025*
