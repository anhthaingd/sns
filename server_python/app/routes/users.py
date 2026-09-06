from fastapi import APIRouter, Cookie, Depends, Form, Header, Query, Request, Response

from app.config.settings import (
    REFRESH_COOKIE_NAME,
    REFRESH_RATE_LIMIT_MAX,
    REFRESH_RATE_LIMIT_WINDOW_SECONDS,
    REGISTER_RATE_LIMIT_MAX,
    REGISTER_RATE_LIMIT_WINDOW_SECONDS,
)

# Controller đã tách theo mối quan tâm, nhưng ROUTER thì cố ý vẫn là một file:
# thứ tự khai báo ở đây có ý nghĩa. `/api/users/refresh` phải được khai báo
# TRƯỚC `/api/users/{user_id}`, nếu không FastAPI sẽ khớp "refresh" thành một
# user_id. Tách thành nhiều router là mất quyền kiểm soát thứ tự đó.
from app.controllers.auth import (
    login_user,
    logout_user,
    refresh_access_token,
    register_user,
)
from app.controllers.follows import (
    following_user,
    get_followers,
    get_following,
    remove_followers,
    remove_following,
)
from app.controllers.resume import get_resume, post_resume
from app.controllers.users import (
    get_user_by_token,
    get_user_details,
    get_users_by_admin,
    search_users,
    update_user,
)
from app.middleware.auth import get_current_user
from app.middleware.upload import save_uploaded_files
from app.schemas.requests import LoginRequest, RegisterRequest
from app.schemas.responses import (
    ERROR_RESPONSES,
    AdminUserListResponse,
    CurrentUserResponse,
    FollowersResponse,
    FollowingResponse,
    MessageResponse,
    ResumeResponse,
    TokenResponse,
    UserDetailsResponse,
    UserListResponse,
)
from app.services.rate_limit import client_ip, rate_limit

router = APIRouter(tags=["users"], responses=ERROR_RESPONSES)

# Đăng ký và refresh đếm MỌI lần gọi theo IP. Đăng nhập không dùng dependency
# vì chỉ được đếm lần THẤT BẠI — logic đó nằm trong `login_user`.
register_rate_limit = Depends(rate_limit("register", REGISTER_RATE_LIMIT_MAX, REGISTER_RATE_LIMIT_WINDOW_SECONDS))
refresh_rate_limit = Depends(rate_limit("refresh", REFRESH_RATE_LIMIT_MAX, REFRESH_RATE_LIMIT_WINDOW_SECONDS))


@router.get("/api/users/getByToken", response_model=CurrentUserResponse)
async def route_get_user_by_token(decoded=Depends(get_current_user)):
    return await get_user_by_token(decoded)


@router.post("/api/users/login", response_model=TokenResponse)
async def route_login(body: LoginRequest, request: Request, response: Response):
    return await login_user(body.email, body.password, response, client_ip(request))


@router.post("/api/users/register", status_code=201, response_model=MessageResponse, dependencies=[register_rate_limit])
async def route_register(body: RegisterRequest):
    return await register_user(
        email=body.email,
        password=body.password,
        username=body.username,
        address=body.address,
        intro=body.intro,
    )


@router.post("/api/users/refresh", response_model=TokenResponse, dependencies=[refresh_rate_limit])
async def route_refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE_NAME),
):
    return await refresh_access_token(refresh_token, response)


@router.post("/api/users/logout", response_model=MessageResponse)
async def route_logout(
    response: Response,
    authorization: str | None = Header(default=None),
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE_NAME),
):
    return await logout_user(authorization, refresh_token, response)


@router.get("/api/users/{user_id}", response_model=UserDetailsResponse)
async def route_get_user_details(user_id: str):
    return await get_user_details(user_id)


@router.put("/api/users/{user_id}", response_model=MessageResponse)
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
    return await update_user(
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


@router.post("/api/users/{user_id}/following", response_model=MessageResponse)
async def route_following_user(user_id: str, decoded=Depends(get_current_user)):
    return await following_user(decoded, user_id)


@router.get("/api/users", response_model=UserListResponse)
async def route_search_users(
    search: str | None = Query(None),
    page: int | None = Query(None, ge=1),
    decoded=Depends(get_current_user),
):
    return await search_users(decoded, search, page or 1)


@router.get("/api/get_users_by_admin", response_model=AdminUserListResponse)
async def route_get_users_by_admin(
    page: int | None = Query(1, ge=1),
    search: str | None = Query(None),
    decoded=Depends(get_current_user),
):
    return await get_users_by_admin(decoded, page or 1, search)


@router.get("/api/get_following", response_model=FollowingResponse)
async def route_get_following(page: int | None = Query(1, ge=1), decoded=Depends(get_current_user)):
    return await get_following(decoded, page or 1)


@router.get("/api/get_followers", response_model=FollowersResponse)
async def route_get_followers(page: int | None = Query(1, ge=1), decoded=Depends(get_current_user)):
    return await get_followers(decoded, page or 1)


@router.delete("/api/remove_following/{target_id}", response_model=MessageResponse)
async def route_remove_following(target_id: str, decoded=Depends(get_current_user)):
    return await remove_following(decoded, target_id)


@router.delete("/api/remove_followers/{target_id}", response_model=MessageResponse)
async def route_remove_followers(target_id: str, decoded=Depends(get_current_user)):
    return await remove_followers(decoded, target_id)


@router.get("/api/resume", response_model=ResumeResponse)
async def route_get_resume(decoded=Depends(get_current_user)):
    return await get_resume(decoded)


@router.post("/api/resume", response_model=MessageResponse)
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
    japaneseLevel: str | None = Form(None),
    englishLevel: str | None = Form(None),
    yearsOfExperience: str | None = Form(None),
    desiredSalaryMin: str | None = Form(None),
    desiredLocations: str | None = Form(None),
    decoded=Depends(get_current_user),
    files: dict = Depends(save_uploaded_files),
):
    return await post_resume(
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
        japanese_level=japaneseLevel,
        english_level=englishLevel,
        years_of_experience=yearsOfExperience,
        desired_salary_min=desiredSalaryMin,
        desired_locations=desiredLocations,
        files=files,
    )
