from fastapi import APIRouter, Depends, Form

from app.controllers.web import get_web, update_web
from app.middleware.auth import get_current_user
from app.middleware.upload import save_uploaded_files
from app.schemas.responses import ERROR_RESPONSES, MessageResponse, WebsiteResponse

router = APIRouter(tags=["website"], responses=ERROR_RESPONSES)


@router.get("/api/website", response_model=WebsiteResponse)
async def route_get_web():
    return await get_web()


@router.put("/api/website/{web_id}", response_model=MessageResponse)
async def route_update_web(
    web_id: str,
    website_name: str | None = Form(None),
    color_title: str | None = Form(None),
    website_quotes_register: str | None = Form(None),
    website_quotes_login: str | None = Form(None),
    oldLogo: str | None = Form(None),
    decoded=Depends(get_current_user),
    files: dict = Depends(save_uploaded_files),
):
    return await update_web(
        decoded, web_id, website_name, color_title, website_quotes_register, website_quotes_login, oldLogo, files
    )
