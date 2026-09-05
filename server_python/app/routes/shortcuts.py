from fastapi import APIRouter, Depends

from app.controllers.shortcuts import get_shortcuts, update_shortcut
from app.middleware.auth import get_current_user
from app.schemas.responses import ERROR_RESPONSES, ApiEnvelope, ShortcutListResponse

router = APIRouter(tags=["shortcuts"], responses=ERROR_RESPONSES)


@router.get("/api/shortcuts", response_model=ShortcutListResponse)
async def route_get_shortcuts(decoded=Depends(get_current_user)):
    return await get_shortcuts(decoded)


@router.put("/api/shortcuts/{channel_id}", response_model=ApiEnvelope)
async def route_update_shortcut(channel_id: str, decoded=Depends(get_current_user)):
    return await update_shortcut(decoded, channel_id)
