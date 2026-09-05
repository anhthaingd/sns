from fastapi import APIRouter, Depends, Form, Query
from fastapi.responses import JSONResponse

from app.controllers.posts import (
    book_mark_post,
    create_post,
    delete_comment_post,
    delete_post,
    delete_post_by_admin,
    get_all_posts,
    get_book_mark,
    get_post_details,
    get_post_from_another_user,
    get_posts_by_admin,
    get_posts_by_user,
    get_posts_in_channel,
    like_post,
    post_comment_post,
    updated_post,
)
from app.middleware.auth import get_current_user
from app.middleware.upload import save_uploaded_files

router = APIRouter()


@router.get("/api/posts")
async def route_get_all_posts(
    page: int | None = Query(1),
    search: str | None = Query(None),
    decoded=Depends(get_current_user),
):
    result = await get_all_posts(decoded, page or 1, search)
    return JSONResponse(status_code=result["status"], content=result["body"])


@router.get("/api/posts/get_by_users")
async def route_get_posts_by_user(
    page: int | None = Query(1),
    decoded=Depends(get_current_user),
):
    result = await get_posts_by_user(decoded, page or 1)
    return JSONResponse(status_code=result["status"], content=result["body"])


@router.get("/api/posts/get_by_admin")
async def route_get_posts_by_admin(
    page: int | None = Query(1),
    channel: str | None = Query(None),
    decoded=Depends(get_current_user),
):
    result = await get_posts_by_admin(decoded, page or 1, channel)
    return JSONResponse(status_code=result["status"], content=result["body"])


@router.get("/api/posts/get_from_another_users/{target_user_id}")
async def route_get_post_from_another_user(
    target_user_id: str,
    page: int | None = Query(1),
    decoded=Depends(get_current_user),
):
    result = await get_post_from_another_user(decoded, target_user_id, page or 1)
    return JSONResponse(status_code=result["status"], content=result["body"])


@router.get("/api/posts/get_book_marked")
async def route_get_book_mark(
    page: int | None = Query(1),
    decoded=Depends(get_current_user),
):
    result = await get_book_mark(decoded, page or 1)
    return JSONResponse(status_code=result["status"], content=result["body"])


@router.get("/api/posts/get_post_details_in_channel/{post_id}")
async def route_get_post_details(post_id: str, decoded=Depends(get_current_user)):
    result = await get_post_details(post_id)
    return JSONResponse(status_code=result["status"], content=result["body"])


@router.get("/api/posts/{channel_id}")
async def route_get_posts_in_channel(
    channel_id: str,
    page: int | None = Query(1),
    decoded=Depends(get_current_user),
):
    result = await get_posts_in_channel(channel_id, page or 1)
    return JSONResponse(status_code=result["status"], content=result["body"])


@router.post("/api/posts/{channel_id}")
async def route_create_post(
    channel_id: str,
    content: str | None = Form(None),
    decoded=Depends(get_current_user),
    files: dict = Depends(save_uploaded_files),
):
    result = await create_post(decoded, channel_id, content, files)
    return JSONResponse(status_code=result["status"], content=result["body"])


@router.put("/api/posts/{channel_id}/{post_id}")
async def route_updated_post(
    channel_id: str,
    post_id: str,
    content: str | None = Form(None),
    oldImages: str | None = Form(None),
    decoded=Depends(get_current_user),
    files: dict = Depends(save_uploaded_files),
):
    result = await updated_post(decoded, channel_id, post_id, content, oldImages, files)
    return JSONResponse(status_code=result["status"], content=result["body"])


@router.delete("/api/posts/{channel_id}/{post_id}")
async def route_delete_post(channel_id: str, post_id: str, decoded=Depends(get_current_user)):
    result = await delete_post(decoded, channel_id, post_id)
    return JSONResponse(status_code=result["status"], content=result["body"])


@router.delete("/api/delete_post_by_admin/{channel_id}/{post_id}")
async def route_delete_post_by_admin(channel_id: str, post_id: str, decoded=Depends(get_current_user)):
    result = await delete_post_by_admin(decoded, channel_id, post_id)
    return JSONResponse(status_code=result["status"], content=result["body"])


@router.post("/api/posts/{channel_id}/{post_id}/like_post")
async def route_like_post(channel_id: str, post_id: str, decoded=Depends(get_current_user)):
    result = await like_post(decoded, channel_id, post_id)
    return JSONResponse(status_code=result["status"], content=result["body"])


@router.post("/api/posts/{channel_id}/{post_id}/book_mark")
async def route_book_mark_post(channel_id: str, post_id: str, decoded=Depends(get_current_user)):
    result = await book_mark_post(decoded, channel_id, post_id)
    return JSONResponse(status_code=result["status"], content=result["body"])


@router.post("/api/posts/{channel_id}/{post_id}/comments")
async def route_post_comment(channel_id: str, post_id: str, body: dict, decoded=Depends(get_current_user)):
    result = await post_comment_post(decoded, channel_id, post_id, body.get("content", ""))
    return JSONResponse(status_code=result["status"], content=result["body"])


@router.delete("/api/posts/{channel_id}/{post_id}/comments")
async def route_delete_comment(channel_id: str, post_id: str, body: dict, decoded=Depends(get_current_user)):
    result = await delete_comment_post(decoded, channel_id, post_id, body.get("commentId", ""))
    return JSONResponse(status_code=result["status"], content=result["body"])
