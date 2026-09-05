from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from app.middleware.auth import get_current_user
from app.controllers.chat import get_chat, get_newest_message, read_message

router = APIRouter()


@router.get("/api/messages/{sender_id}/{receiver_id}")
async def route_get_chat(
    sender_id: str,
    receiver_id: str,
    page: Optional[int] = Query(1),
    decoded=Depends(get_current_user),
):
    result = await get_chat(sender_id, receiver_id, page or 1)
    return JSONResponse(status_code=result["status"], content=result["body"])


@router.get("/api/newest_messages")
async def route_get_newest_message(decoded=Depends(get_current_user)):
    result = await get_newest_message(decoded)
    return JSONResponse(status_code=result["status"], content=result["body"])


@router.put("/api/newest_messages/{message_id}")
async def route_read_message(message_id: str, decoded=Depends(get_current_user)):
    result = await read_message(decoded, message_id)
    return JSONResponse(status_code=result["status"], content=result["body"])
