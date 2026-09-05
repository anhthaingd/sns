from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.controllers.shortcuts import get_shortcuts, update_shortcut
from app.middleware.auth import get_current_user

router = APIRouter()


@router.get("/api/shortcuts")
async def route_get_shortcuts(decoded=Depends(get_current_user)):
    result = await get_shortcuts(decoded)
    return JSONResponse(status_code=result["status"], content=result["body"])


@router.put("/api/shortcuts/{channel_id}")
async def route_update_shortcut(channel_id: str, decoded=Depends(get_current_user)):
    result = await update_shortcut(decoded, channel_id)
    return JSONResponse(status_code=result["status"], content=result["body"])
