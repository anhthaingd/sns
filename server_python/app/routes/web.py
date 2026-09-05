from typing import Optional
from fastapi import APIRouter, Depends, Form
from fastapi.responses import JSONResponse

from app.middleware.auth import get_current_user
from app.middleware.upload import save_uploaded_files
from app.controllers.web import get_web, update_web

router = APIRouter()


@router.get("/api/website")
async def route_get_web():
    result = await get_web()
    return JSONResponse(status_code=result["status"], content=result["body"])


@router.put("/api/website/{web_id}")
async def route_update_web(
    web_id: str,
    website_name: Optional[str] = Form(None),
    color_title: Optional[str] = Form(None),
    website_quotes_register: Optional[str] = Form(None),
    website_quotes_login: Optional[str] = Form(None),
    oldLogo: Optional[str] = Form(None),
    decoded=Depends(get_current_user),
    files: dict = Depends(save_uploaded_files),
):
    result = await update_web(decoded, web_id, website_name, color_title, website_quotes_register, website_quotes_login, oldLogo, files)
    return JSONResponse(status_code=result["status"], content=result["body"])
