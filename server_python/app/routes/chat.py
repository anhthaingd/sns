from fastapi import APIRouter, Depends, Query

from app.controllers.chat import get_chat, get_newest_message, read_message
from app.middleware.auth import get_current_user
from app.schemas.responses import ERROR_RESPONSES, ApiEnvelope, ChatResponse, NewestMessageResponse

router = APIRouter(tags=["chat"], responses=ERROR_RESPONSES)


@router.get("/api/messages/{sender_id}/{receiver_id}", response_model=ChatResponse)
async def route_get_chat(
    sender_id: str,
    receiver_id: str,
    page: int | None = Query(1, ge=1),
    decoded=Depends(get_current_user),
):
    return await get_chat(sender_id, receiver_id, page or 1)


@router.get("/api/newest_messages", response_model=NewestMessageResponse)
async def route_get_newest_message(decoded=Depends(get_current_user)):
    return await get_newest_message(decoded)


@router.put("/api/newest_messages/{message_id}", response_model=ApiEnvelope)
async def route_read_message(message_id: str, decoded=Depends(get_current_user)):
    return await read_message(decoded, message_id)
