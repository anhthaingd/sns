from typing import Optional
from fastapi import APIRouter, Depends, Query, Form
from fastapi.responses import JSONResponse

from app.middleware.auth import get_current_user
from app.middleware.upload import save_uploaded_files
from app.controllers.channels import (
    get_all_channels,
    get_channels_by_user,
    get_channel_details,
    create_channel,
    join_channel,
    update_channel,
    delete_channel,
    remove_user_from_channel,
)

router = APIRouter()


@router.get("/api/channels")
async def route_get_all_channels(
    page: Optional[int] = Query(1),
    search: Optional[str] = Query(None),
):
    result = await get_all_channels(page or 1, search)
    return JSONResponse(status_code=result["status"], content=result["body"])


@router.post("/api/channels")
async def route_create_channel(
    name: str = Form(...),
    intro: Optional[str] = Form(None),
    decoded=Depends(get_current_user),
    files: dict = Depends(save_uploaded_files),
):
    result = await create_channel(decoded, name, intro, files)
    return JSONResponse(status_code=result["status"], content=result["body"])


@router.get("/api/channels/get_by_user")
async def route_get_channels_by_user(decoded=Depends(get_current_user)):
    result = await get_channels_by_user(decoded)
    return JSONResponse(status_code=result["status"], content=result["body"])


@router.get("/api/channels/{channel_id}")
async def route_get_channel_details(channel_id: str, decoded=Depends(get_current_user)):
    result = await get_channel_details(decoded, channel_id)
    return JSONResponse(status_code=result["status"], content=result["body"])


@router.post("/api/channels/{channel_id}")
async def route_join_channel(channel_id: str, decoded=Depends(get_current_user)):
    result = await join_channel(decoded, channel_id)
    return JSONResponse(status_code=result["status"], content=result["body"])


@router.put("/api/channels/{channel_id}")
async def route_update_channel(
    channel_id: str,
    name: Optional[str] = Form(None),
    intro: Optional[str] = Form(None),
    oldBackground: Optional[str] = Form(None),
    decoded=Depends(get_current_user),
    files: dict = Depends(save_uploaded_files),
):
    result = await update_channel(decoded, channel_id, name, intro, oldBackground, files)
    return JSONResponse(status_code=result["status"], content=result["body"])


@router.delete("/api/channels/{channel_id}")
async def route_delete_channel(channel_id: str, decoded=Depends(get_current_user)):
    result = await delete_channel(decoded, channel_id)
    return JSONResponse(status_code=result["status"], content=result["body"])


@router.delete("/api/channels/{channel_id}/delete_user")
async def route_remove_user_from_channel(channel_id: str, body: dict, decoded=Depends(get_current_user)):
    result = await remove_user_from_channel(decoded, channel_id, body.get("userId", ""))
    return JSONResponse(status_code=result["status"], content=result["body"])
