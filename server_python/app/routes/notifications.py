from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from app.middleware.auth import get_current_user
from app.controllers.notifications import get_notifications, read_notification

router = APIRouter()


@router.get("/api/notifications")
async def route_get_notifications(
    page: Optional[int] = Query(1),
    decoded=Depends(get_current_user),
):
    result = await get_notifications(decoded, page or 1)
    return JSONResponse(status_code=result["status"], content=result["body"])


@router.post("/api/notifications/{notification_id}")
async def route_read_notification(notification_id: str, decoded=Depends(get_current_user)):
    result = await read_notification(decoded, notification_id)
    return JSONResponse(status_code=result["status"], content=result["body"])
