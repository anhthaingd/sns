from fastapi import APIRouter, Depends, Form, Query

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
from app.schemas.requests import CommentCreateRequest, CommentDeleteRequest
from app.schemas.responses import (
    ERROR_RESPONSES,
    HomePostListResponse,
    MessageResponse,
    PostDetailsResponse,
    PostListResponse,
)

router = APIRouter(tags=["posts"], responses=ERROR_RESPONSES)


@router.get("/api/posts", response_model=HomePostListResponse)
async def route_get_all_posts(
    page: int | None = Query(1, ge=1),
    search: str | None = Query(None),
    decoded=Depends(get_current_user),
):
    return await get_all_posts(decoded, page or 1, search)


@router.get("/api/posts/get_by_users", response_model=PostListResponse)
async def route_get_posts_by_user(page: int | None = Query(1, ge=1), decoded=Depends(get_current_user)):
    return await get_posts_by_user(decoded, page or 1)


@router.get("/api/posts/get_by_admin", response_model=PostListResponse)
async def route_get_posts_by_admin(
    page: int | None = Query(1, ge=1),
    channel: str | None = Query(None),
    decoded=Depends(get_current_user),
):
    return await get_posts_by_admin(decoded, page or 1, channel)


@router.get("/api/posts/get_from_another_users/{target_user_id}", response_model=PostListResponse)
async def route_get_post_from_another_user(
    target_user_id: str,
    page: int | None = Query(1, ge=1),
    decoded=Depends(get_current_user),
):
    return await get_post_from_another_user(decoded, target_user_id, page or 1)


@router.get("/api/posts/get_book_marked", response_model=PostListResponse)
async def route_get_book_mark(page: int | None = Query(1, ge=1), decoded=Depends(get_current_user)):
    return await get_book_mark(decoded, page or 1)


@router.get("/api/posts/get_post_details_in_channel/{post_id}", response_model=PostDetailsResponse)
async def route_get_post_details(post_id: str, decoded=Depends(get_current_user)):
    return await get_post_details(post_id)


@router.get("/api/posts/{channel_id}", response_model=PostListResponse)
async def route_get_posts_in_channel(
    channel_id: str,
    page: int | None = Query(1, ge=1),
    decoded=Depends(get_current_user),
):
    return await get_posts_in_channel(channel_id, page or 1)


@router.post("/api/posts/{channel_id}", status_code=201, response_model=MessageResponse)
async def route_create_post(
    channel_id: str,
    content: str | None = Form(None),
    decoded=Depends(get_current_user),
    files: dict = Depends(save_uploaded_files),
):
    return await create_post(decoded, channel_id, content, files)


@router.put("/api/posts/{channel_id}/{post_id}", response_model=MessageResponse)
async def route_updated_post(
    channel_id: str,
    post_id: str,
    content: str | None = Form(None),
    oldImages: str | None = Form(None),
    decoded=Depends(get_current_user),
    files: dict = Depends(save_uploaded_files),
):
    return await updated_post(decoded, channel_id, post_id, content, oldImages, files)


@router.delete("/api/posts/{channel_id}/{post_id}", response_model=MessageResponse)
async def route_delete_post(channel_id: str, post_id: str, decoded=Depends(get_current_user)):
    return await delete_post(decoded, channel_id, post_id)


@router.delete("/api/delete_post_by_admin/{channel_id}/{post_id}", response_model=MessageResponse)
async def route_delete_post_by_admin(channel_id: str, post_id: str, decoded=Depends(get_current_user)):
    return await delete_post_by_admin(decoded, channel_id, post_id)


@router.post("/api/posts/{channel_id}/{post_id}/like_post", response_model=MessageResponse)
async def route_like_post(channel_id: str, post_id: str, decoded=Depends(get_current_user)):
    return await like_post(decoded, channel_id, post_id)


@router.post("/api/posts/{channel_id}/{post_id}/book_mark", response_model=MessageResponse)
async def route_book_mark_post(channel_id: str, post_id: str, decoded=Depends(get_current_user)):
    return await book_mark_post(decoded, channel_id, post_id)


@router.post("/api/posts/{channel_id}/{post_id}/comments", response_model=MessageResponse)
async def route_post_comment(
    channel_id: str,
    post_id: str,
    body: CommentCreateRequest,
    decoded=Depends(get_current_user),
):
    return await post_comment_post(decoded, channel_id, post_id, body.content)


@router.delete("/api/posts/{channel_id}/{post_id}/comments", response_model=MessageResponse)
async def route_delete_comment(
    channel_id: str,
    post_id: str,
    body: CommentDeleteRequest,
    decoded=Depends(get_current_user),
):
    return await delete_comment_post(decoded, channel_id, post_id, body.commentId)
