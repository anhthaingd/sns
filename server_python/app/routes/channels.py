from fastapi import APIRouter, Depends, Form, Query

from app.controllers.channels import (
    create_channel,
    delete_channel,
    get_all_channels,
    get_channel_details,
    get_channels_by_user,
    join_channel,
    remove_user_from_channel,
    update_channel,
)
from app.middleware.auth import get_current_user
from app.middleware.upload import save_uploaded_files
from app.schemas.requests import RemoveUserFromChannelRequest
from app.schemas.responses import (
    ERROR_RESPONSES,
    ChannelDetailsResponse,
    ChannelListResponse,
    MessageResponse,
    UserChannelsResponse,
)

router = APIRouter(tags=["channels"], responses=ERROR_RESPONSES)


@router.get("/api/channels", response_model=ChannelListResponse)
async def route_get_all_channels(page: int | None = Query(1, ge=1), search: str | None = Query(None)):
    return await get_all_channels(page or 1, search)


@router.post("/api/channels", status_code=201, response_model=MessageResponse)
async def route_create_channel(
    name: str = Form(...),
    intro: str | None = Form(None),
    decoded=Depends(get_current_user),
    files: dict = Depends(save_uploaded_files),
):
    return await create_channel(decoded, name, intro, files)


@router.get("/api/channels/get_by_user", response_model=UserChannelsResponse)
async def route_get_channels_by_user(decoded=Depends(get_current_user)):
    return await get_channels_by_user(decoded)


@router.get("/api/channels/{channel_id}", response_model=ChannelDetailsResponse)
async def route_get_channel_details(channel_id: str, decoded=Depends(get_current_user)):
    return await get_channel_details(decoded, channel_id)


@router.post("/api/channels/{channel_id}", response_model=MessageResponse)
async def route_join_channel(channel_id: str, decoded=Depends(get_current_user)):
    return await join_channel(decoded, channel_id)


@router.put("/api/channels/{channel_id}", response_model=MessageResponse)
async def route_update_channel(
    channel_id: str,
    name: str | None = Form(None),
    intro: str | None = Form(None),
    oldBackground: str | None = Form(None),
    decoded=Depends(get_current_user),
    files: dict = Depends(save_uploaded_files),
):
    return await update_channel(decoded, channel_id, name, intro, oldBackground, files)


@router.delete("/api/channels/{channel_id}", response_model=MessageResponse)
async def route_delete_channel(channel_id: str, decoded=Depends(get_current_user)):
    return await delete_channel(decoded, channel_id)


@router.delete("/api/channels/{channel_id}/delete_user", response_model=MessageResponse)
async def route_remove_user_from_channel(
    channel_id: str,
    body: RemoveUserFromChannelRequest,
    decoded=Depends(get_current_user),
):
    return await remove_user_from_channel(decoded, channel_id, body.userId)
