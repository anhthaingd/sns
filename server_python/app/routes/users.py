from typing import Optional
from fastapi import APIRouter, Depends, Query, Form, Header
from fastapi.responses import JSONResponse

from app.middleware.auth import get_current_user
from app.middleware.upload import save_uploaded_files
from app.controllers.users import (
    get_user_by_token,
    login_user,
    register_user,
    logout_user,
    get_user_details,
    update_user,
    following_user,
    search_users,
    get_users_by_admin,
    get_following,
    get_followers,
    remove_following,
    remove_followers,
    get_resume,
    post_resume,
)

router = APIRouter()


@router.get("/api/users/getByToken")
async def route_get_user_by_token(decoded=Depends(get_current_user)):
    result = await get_user_by_token(decoded)
    return JSONResponse(status_code=result["status"], content=result["body"])


@router.post("/api/users/login")
async def route_login(body: dict):
    result = await login_user(body.get("email", ""), body.get("password", ""))
    return JSONResponse(status_code=result["status"], content=result["body"])


@router.post("/api/users/register")
async def route_register(body: dict):
    result = await register_user(
        email=body.get("email"),
        password=body.get("password"),
        username=body.get("username"),
        address=body.get("address"),
        intro=body.get("intro"),
    )
    return JSONResponse(status_code=result["status"], content=result["body"])


@router.post("/api/users/logout")
async def route_logout(authorization: Optional[str] = Header(default=None)):
    result = await logout_user(authorization or "")
    return JSONResponse(status_code=result["status"], content=result["body"])


@router.get("/api/users/{user_id}")
async def route_get_user_details(user_id: str):
    result = await get_user_details(user_id)
    return JSONResponse(status_code=result["status"], content=result["body"])


@router.put("/api/users/{user_id}")
async def route_update_user(
    user_id: str,
    username: Optional[str] = Form(None),
    oldPassword: Optional[str] = Form(None),
    newPassword: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    intro: Optional[str] = Form(None),
    oldAvatar: Optional[str] = Form(None),
    oldCoverBg: Optional[str] = Form(None),
    update_images: Optional[str] = Form(None),
    decoded=Depends(get_current_user),
    files: dict = Depends(save_uploaded_files),
):
    result = await update_user(
        user_id=user_id,
        decoded_user=decoded,
        username=username,
        old_password=oldPassword,
        new_password=newPassword,
        address=address,
        intro=intro,
        old_avatar=oldAvatar,
        old_cover_bg=oldCoverBg,
        update_images=update_images,
        files=files,
    )
    return JSONResponse(status_code=result["status"], content=result["body"])


@router.post("/api/users/{user_id}/following")
async def route_following_user(user_id: str, decoded=Depends(get_current_user)):
    result = await following_user(decoded, user_id)
    return JSONResponse(status_code=result["status"], content=result["body"])


@router.get("/api/users")
async def route_search_users(
    search: Optional[str] = Query(None),
    page: Optional[int] = Query(None),
    decoded=Depends(get_current_user),
):
    result = await search_users(decoded, search, page or 1)
    return JSONResponse(status_code=result["status"], content=result["body"])


@router.get("/api/get_users_by_admin")
async def route_get_users_by_admin(
    page: Optional[int] = Query(1),
    search: Optional[str] = Query(None),
    decoded=Depends(get_current_user),
):
    result = await get_users_by_admin(decoded, page or 1, search)
    return JSONResponse(status_code=result["status"], content=result["body"])


@router.get("/api/get_following")
async def route_get_following(
    page: Optional[int] = Query(1),
    decoded=Depends(get_current_user),
):
    result = await get_following(decoded, page or 1)
    return JSONResponse(status_code=result["status"], content=result["body"])


@router.get("/api/get_followers")
async def route_get_followers(
    page: Optional[int] = Query(1),
    decoded=Depends(get_current_user),
):
    result = await get_followers(decoded, page or 1)
    return JSONResponse(status_code=result["status"], content=result["body"])


@router.delete("/api/remove_following/{target_id}")
async def route_remove_following(target_id: str, decoded=Depends(get_current_user)):
    result = await remove_following(decoded, target_id)
    return JSONResponse(status_code=result["status"], content=result["body"])


@router.delete("/api/remove_followers/{target_id}")
async def route_remove_followers(target_id: str, decoded=Depends(get_current_user)):
    result = await remove_followers(decoded, target_id)
    return JSONResponse(status_code=result["status"], content=result["body"])


@router.get("/api/resume")
async def route_get_resume(decoded=Depends(get_current_user)):
    result = await get_resume(decoded)
    return JSONResponse(status_code=result["status"], content=result["body"])


@router.post("/api/resume")
async def route_post_resume(
    name: Optional[str] = Form(None),
    position: Optional[str] = Form(None),
    oldAvatar: Optional[str] = Form(None),
    birthday: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    github: Optional[str] = Form(None),
    objective: Optional[str] = Form(None),
    educationName: Optional[str] = Form(None),
    educationMajor: Optional[str] = Form(None),
    educationCompletion: Optional[str] = Form(None),
    educationGPA: Optional[str] = Form(None),
    certificatesName: Optional[str] = Form(None),
    oldCertificates: Optional[str] = Form(None),
    editCertificates: Optional[str] = Form(None),
    experiences: Optional[str] = Form(None),
    skills: Optional[str] = Form(None),
    languages: Optional[str] = Form(None),
    projects: Optional[str] = Form(None),
    decoded=Depends(get_current_user),
    files: dict = Depends(save_uploaded_files),
):
    result = await post_resume(
        decoded_user=decoded,
        name=name,
        position=position,
        old_avatar=oldAvatar,
        birthday=birthday,
        email=email,
        address=address,
        phone=phone,
        github=github,
        objective=objective,
        education_name=educationName,
        education_major=educationMajor,
        education_completion=educationCompletion,
        education_gpa=educationGPA,
        certificates_name=certificatesName,
        old_certificates=oldCertificates,
        edit_certificates=editCertificates,
        experiences=experiences,
        skills=skills,
        languages=languages,
        projects=projects,
        files=files,
    )
    return JSONResponse(status_code=result["status"], content=result["body"])
