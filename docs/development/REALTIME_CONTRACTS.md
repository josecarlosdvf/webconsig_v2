# Contratos de Tempo Real (Webconsig)

## WebSocket

Endpoint:

- `GET/WS /api/v1/realtime/ws`

Formato de mensagem:

```json
{
  "event_type": "audit.event",
  "timestamp": "2026-03-09T20:10:30.000000",
  "payload": {
    "area": "financeiro",
    "action": "transaction.created",
    "actor": "admin"
  }
}
```

Eventos reservados:

- `system.startup`
- `system.connection`
- `system.heartbeat`
- `audit.event`
- `debug.event`

## Consulta REST (fallback)

- `GET /api/v1/realtime/events?limit=100&event_type=audit.event`

Resposta:

```json
{
  "items": [
    {
      "event_type": "audit.event",
      "timestamp": "2026-03-09T20:10:30.000000",
      "payload": {}
    }
  ],
  "total": 1
}
```

## HTMX

Endpoint de fragmento HTML:

- `GET /api/v1/realtime/htmx/audit-feed?limit=10`

Observações:

- Retorna HTML parcial para atualização incremental de painel.
- Header `HX-Trigger: realtime-feed-updated` para notificação de atualização no cliente HTMX.
