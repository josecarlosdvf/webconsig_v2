from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_actor, get_plugin_service, get_request_id, require_permission
from app.application.services.plugin_service import PluginService
from app.domain.schemas.chat_plugin import (
    ChatMessageCreateRequest,
    ChatMessageListRequest,
    ChatMessageListResponse,
)

router = APIRouter(prefix="/plugins/chat", tags=["chat-plugin"])


@router.post("/messages", summary="Enviar mensagem no chat (plugin)")
def send_message(
    payload: ChatMessageCreateRequest,
    service: PluginService = Depends(get_plugin_service),
    actor: str = Depends(get_actor),
    request_id: str = Depends(get_request_id),
    _: None = Depends(require_permission("api:/api/v1/plugins/chat/messages", "create")),
) -> dict:
    response = service.run_task_by_slug(
        slug="chat-hub",
        task="send_message",
        payload=payload.model_dump(),
        actor=actor,
        request_id=request_id,
    )
    return response.result


@router.post("/messages/list", response_model=ChatMessageListResponse, summary="Listar mensagens do chat (plugin)")
def list_messages(
    payload: ChatMessageListRequest,
    service: PluginService = Depends(get_plugin_service),
    actor: str = Depends(get_actor),
    request_id: str = Depends(get_request_id),
    _: None = Depends(require_permission("api:/api/v1/plugins/chat/messages/list", "view")),
) -> ChatMessageListResponse:
    response = service.run_task_by_slug(
        slug="chat-hub",
        task="list_messages",
        payload=payload.model_dump(),
        actor=actor,
        request_id=request_id,
    )
    return ChatMessageListResponse(**response.result)


@router.get("/rooms", summary="Listar salas do chat (plugin)")
def list_rooms(
    service: PluginService = Depends(get_plugin_service),
    actor: str = Depends(get_actor),
    request_id: str = Depends(get_request_id),
    _: None = Depends(require_permission("api:/api/v1/plugins/chat/rooms", "view")),
) -> dict:
    response = service.run_task_by_slug(
        slug="chat-hub",
        task="list_rooms",
        payload={},
        actor=actor,
        request_id=request_id,
    )
    return response.result
