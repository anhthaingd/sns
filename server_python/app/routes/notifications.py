from fastapi import APIRouter, Depends, Query

from app.controllers.notifications import get_notifications, read_notification
from app.middleware.auth import get_current_user
from app.schemas.responses import ERROR_RESPONSES, ApiEnvelope, NotificationListResponse

router = APIRouter(tags=["notifications"], responses=ERROR_RESPONSES)


@router.get("/api/notifications", response_model=NotificationListResponse)
async def route_get_notifications(page: int | None = Query(1, ge=1), decoded=Depends(get_current_user)):
    return await get_notifications(decoded, page or 1)


@router.post("/api/notifications/{notification_id}", response_model=ApiEnvelope)
async def route_read_notification(notification_id: str, decoded=Depends(get_current_user)):
    return await read_notification(decoded, notification_id)
