from fastapi import APIRouter, Depends, Form, Header, Query
from fastapi.responses import JSONResponse

from app.controllers.users import (
    following_user,
    get_followers,
    get_following,
    get_resume,
    get_user_by_token,
    get_user_details,
    get_users_by_admin,
    login_user,
    logout_user,
    post_resume,
    register_user,
    remove_followers,
    remove_following,
    search_users,
    update_user,
)
from app.middleware.auth import get_current_user
from app.middleware.upload import save_uploaded_files

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
async def route_logout(authorization: str | None = Header(default=None)):
    result = await logout_user(authorization or "")
    return JSONResponse(status_code=result["status"], content=result["body"])


@router.get("/api/users/{user_id}")
async def route_get_user_details(user_id: str):
    result = await get_user_details(user_id)
    return JSONResponse(status_code=result["status"], content=result["body"])


@router.put("/api/users/{user_id}")
async def route_update_user(
    user_id: str,
    username: str | None = Form(None),
    oldPassword: str | None = Form(None),
    newPassword: str | None = Form(None),
    address: str | None = Form(None),
    intro: str | None = Form(None),
    oldAvatar: str | None = Form(None),
    oldCoverBg: str | None = Form(None),
    update_images: str | None = Form(None),
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
    search: str | None = Query(None),
    page: int | None = Query(None),
    decoded=Depends(get_current_user),
):
    result = await search_users(decoded, search, page or 1)
    return JSONResponse(status_code=result["status"], content=result["body"])


@router.get("/api/get_users_by_admin")
async def route_get_users_by_admin(
    page: int | None = Query(1),
    search: str | None = Query(None),
    decoded=Depends(get_current_user),
):
    result = await get_users_by_admin(decoded, page or 1, search)
    return JSONResponse(status_code=result["status"], content=result["body"])


@router.get("/api/get_following")
async def route_get_following(
    page: int | None = Query(1),
    decoded=Depends(get_current_user),
):
    result = await get_following(decoded, page or 1)
    return JSONResponse(status_code=result["status"], content=result["body"])


@router.get("/api/get_followers")
async def route_get_followers(
    page: int | None = Query(1),
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
    name: str | None = Form(None),
    position: str | None = Form(None),
    oldAvatar: str | None = Form(None),
    birthday: str | None = Form(None),
    email: str | None = Form(None),
    address: str | None = Form(None),
    phone: str | None = Form(None),
    github: str | None = Form(None),
    objective: str | None = Form(None),
    educationName: str | None = Form(None),
    educationMajor: str | None = Form(None),
    educationCompletion: str | None = Form(None),
    educationGPA: str | None = Form(None),
    certificatesName: str | None = Form(None),
    oldCertificates: str | None = Form(None),
    editCertificates: str | None = Form(None),
    experiences: str | None = Form(None),
    skills: str | None = Form(None),
    languages: str | None = Form(None),
    projects: str | None = Form(None),
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
