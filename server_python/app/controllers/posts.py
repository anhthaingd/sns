import json
import math
from datetime import datetime

from bson import ObjectId

from app.errors import ApiError
from app.models.channel import Channel
from app.models.notification import Notification
from app.models.post import Post
from app.models.user import User
from app.utils.file_utils import delete_file
from app.utils.ids import to_object_id, to_object_id_or_none
from app.utils.loaders import brief_list, load_channels, load_roles_of, load_users, role_brief, user_brief
from app.utils.permissions import require_admin
from app.utils.responses import ok
from app.utils.search import contains, normalize_search
from app.utils.serialization import serialize_doc, to_jsonable

PAGE_SIZE = 10


def _comment_user_id(comment: dict):
    return comment.get("user")


async def _populate_posts(posts: list[Post], *, with_author_role: bool = False) -> list[dict]:
    """Gắn quan hệ cho CẢ TRANG bài viết bằng 2-3 truy vấn.

    Bản cũ populate từng bài một: mỗi bài tốn 1 truy vấn cho tác giả, 1 cho
    channel, 1 cho mỗi người bình luận, cộng liked/book_marked. Đo được 53 truy
    vấn cho `GET /api/posts?page=1` với 10 bài. Ở đây gom toàn bộ id của cả
    trang rồi nạp một lần cho mỗi collection.
    """
    if not posts:
        return []

    user_ids = []
    channel_ids = []
    for post in posts:
        if post.user:
            user_ids.append(post.user)
        if post.channel:
            channel_ids.append(post.channel)
        user_ids.extend(post.liked or [])
        user_ids.extend(post.book_marked or [])
        for comment in post.comments or []:
            commenter = _comment_user_id(comment)
            if commenter:
                user_ids.append(commenter)

    user_map = await load_users(user_ids)
    channel_map = await load_channels(channel_ids)
    role_map = await load_roles_of(user_map.values()) if with_author_role else {}

    result = []
    for post in posts:
        data = serialize_doc(post)

        author = user_map.get(str(post.user)) if post.user else None
        if author is not None:
            author_data = user_brief(author)
            if with_author_role and author.role:
                author_data["role"] = role_brief(role_map.get(str(author.role)))
            data["user"] = author_data

        channel = channel_map.get(str(post.channel)) if post.channel else None
        if channel is not None:
            data["channel"] = {"_id": str(channel.id), "name": channel.name}

        if post.liked:
            data["liked"] = brief_list(post.liked, user_map)
        if post.book_marked:
            data["book_marked"] = brief_list(post.book_marked, user_map)

        if post.comments:
            comments = []
            for comment in post.comments:
                # to_jsonable xử lý cả ObjectId lẫn datetime (created_at).
                comment_data = to_jsonable(dict(comment))
                commenter = user_map.get(str(_comment_user_id(comment))) if _comment_user_id(comment) else None
                if commenter is not None:
                    comment_data["user"] = user_brief(commenter)
                comments.append(comment_data)
            data["comments"] = comments

        result.append(data)
    return result


async def _populate_post(post: Post) -> dict:
    return (await _populate_posts([post]))[0]


def _page(total: int) -> int:
    return math.ceil(total / PAGE_SIZE) if total > 0 else 1


async def get_all_posts(decoded_user: dict, page: int = 1, search: str = None):
    user_id = to_object_id(decoded_user["_id"], "user_id")
    channels = await Channel.find({"members": user_id}).to_list()
    query = {"channel": {"$in": [ch.id for ch in channels]}}

    keyword = normalize_search(search)
    if keyword:
        regex = contains(keyword)
        search_users = await User.find(
            {"_id": {"$ne": user_id}, "$or": [{"username": regex}, {"email": regex}]}
        ).to_list()
        search_channel = await Channel.find_one({"name": regex})
        query["$or"] = [
            {"user": {"$in": [u.id for u in search_users]}},
            {"channel": search_channel.id if search_channel else None},
            {"content": regex},
        ]

    total_posts = await Post.find(query).count()
    posts = await Post.find(query).sort("-created_at").skip((page - 1) * PAGE_SIZE).limit(PAGE_SIZE).to_list()

    return ok(posts=await _populate_posts(posts), totalPage=_page(total_posts), totalPosts=total_posts)


async def get_posts_by_admin(decoded_user: dict, page: int = 1, channel: str = None):
    require_admin(decoded_user, "Bạn không đủ quyền!")

    query = {}
    channel_oid = to_object_id_or_none(channel, "channel")
    if channel_oid is not None:
        query["channel"] = channel_oid

    total_posts = await Post.find(query).count()
    posts = await Post.find(query).skip((page - 1) * PAGE_SIZE).limit(PAGE_SIZE).to_list()

    return ok(posts=await _populate_posts(posts, with_author_role=True), totalPage=_page(total_posts))


async def get_posts_by_user(decoded_user: dict, page: int = 1):
    user_id = to_object_id(decoded_user["_id"], "user_id")
    total_posts = await Post.find(Post.user == user_id).count()
    posts = await Post.find(Post.user == user_id).skip((page - 1) * PAGE_SIZE).limit(PAGE_SIZE).to_list()
    return ok(posts=await _populate_posts(posts), totalPage=_page(total_posts))


async def get_post_from_another_user(decoded_user: dict, target_user_id: str, page: int = 1):
    user_id = to_object_id(decoded_user["_id"], "user_id")
    channels = await Channel.find({"members": user_id}).to_list()

    query = {
        "user": to_object_id(target_user_id, "target_user_id"),
        "channel": {"$in": [ch.id for ch in channels]},
    }
    total_posts = await Post.find(query).count()
    posts = await Post.find(query).sort("-created_at").skip((page - 1) * PAGE_SIZE).limit(PAGE_SIZE).to_list()
    return ok(posts=await _populate_posts(posts), totalPage=_page(total_posts))


async def get_posts_in_channel(channel_id: str, page: int = 1):
    oid = to_object_id(channel_id, "channel_id")
    total_posts = await Post.find(Post.channel == oid).count()
    posts = (
        await Post.find(Post.channel == oid).sort("-updated_at").skip((page - 1) * PAGE_SIZE).limit(PAGE_SIZE).to_list()
    )
    return ok(posts=await _populate_posts(posts), totalPage=_page(total_posts))


async def get_post_details(post_id: str):
    post = await Post.get(to_object_id(post_id, "post_id"))
    if not post:
        raise ApiError(404, "Không tìm thấy bài viết!")
    return ok(post=await _populate_post(post))


async def create_post(decoded_user: dict, channel_id: str, content: str = None, files: dict = None):
    if not content or not channel_id:
        raise ApiError(400, "Yêu cầu bài viết phải có nội dung và channelId!")

    post_data = {
        "user": to_object_id(decoded_user["_id"], "user_id"),
        "content": content,
        "channel": to_object_id(channel_id, "channel_id"),
    }

    images = files.get("images", []) if files else []
    if images:
        post_data["images"] = {"name": images[0]["filename"], "url": images[0]["path"]}

    await Post(**post_data).insert()
    return ok(message="Tạo bài viết thành công!")


async def updated_post(
    decoded_user: dict, channel_id: str, post_id: str, content: str = None, old_images: str = None, files: dict = None
):
    try:
        parse_old_images = json.loads(old_images) if old_images else None
    except json.JSONDecodeError as err:
        raise ApiError(400, "Dữ liệu ảnh cũ không hợp lệ!") from err

    post_oid = to_object_id(post_id, "post_id")
    correct_post = await Post.find_one(
        {
            "_id": post_oid,
            "channel": to_object_id(channel_id, "channel_id"),
            "user": to_object_id(decoded_user["_id"], "user_id"),
        }
    )
    if not correct_post:
        raise ApiError(403, "Bạn không thể sửa bài viết của người khác hoặc bài viết trong channel đã bị xóa!")

    update_data = {"content": content, "updated_at": datetime.utcnow()}

    images = files.get("images", []) if files else []
    if images:
        if parse_old_images:
            await delete_file(parse_old_images.get("url", ""))
        update_data["images"] = {"name": images[0]["filename"], "url": images[0]["path"]}

    await Post.find_one(Post.id == post_oid).update({"$set": update_data})
    return ok(message="Cập nhật bài viết thành công")


async def _find_post_in_channel(channel_id: str, post_id: str, not_found_message: str) -> Post:
    post = await Post.find_one(
        {"_id": to_object_id(post_id, "post_id"), "channel": to_object_id(channel_id, "channel_id")}
    )
    if not post:
        raise ApiError(404, not_found_message)
    return post


async def like_post(decoded_user: dict, channel_id: str, post_id: str):
    user_id = to_object_id(decoded_user["_id"], "user_id")
    post = await _find_post_in_channel(channel_id, post_id, f"Không tìm thấy bài viết {post_id}!")

    if user_id in post.liked:
        await Post.find_one(Post.id == post.id).update({"$pull": {"liked": user_id}})
        return ok(message="Hủy thích bài viết thành công!")

    if str(post.user) != decoded_user["_id"]:
        await Notification(
            user=post.user,
            seeder=user_id,
            notification=f"{decoded_user.get('username', '')} just liked your post!",
            url=f"channels/{post.channel}/posts/{post.id}",
        ).insert()

    await Post.find_one(Post.id == post.id).update({"$push": {"liked": user_id}})
    return ok(message="Thích bài viết thành công!")


async def book_mark_post(decoded_user: dict, channel_id: str, post_id: str):
    user_id = to_object_id(decoded_user["_id"], "user_id")
    post = await _find_post_in_channel(channel_id, post_id, f"Không tìm thấy bài viết {post_id}!")

    if user_id in post.book_marked:
        await Post.find_one(Post.id == post.id).update({"$pull": {"book_marked": user_id}})
        return ok(message="Hủy lưu bài viết thành công!")

    if str(post.user) != decoded_user["_id"]:
        await Notification(
            user=post.user,
            seeder=user_id,
            notification=f"{decoded_user.get('username', '')} just saved your post!",
            url=None,
        ).insert()

    await Post.find_one(Post.id == post.id).update({"$push": {"book_marked": user_id}})
    return ok(message="Lưu bài viết thành công!")


async def get_book_mark(decoded_user: dict, page: int = 1):
    user_id = to_object_id(decoded_user["_id"], "user_id")
    total_posts = await Post.find({"book_marked": user_id}).count()
    posts = await Post.find({"book_marked": user_id}).skip((page - 1) * PAGE_SIZE).limit(PAGE_SIZE).to_list()
    return ok(posts=await _populate_posts(posts), totalPage=_page(total_posts))


async def post_comment_post(decoded_user: dict, channel_id: str, post_id: str, content: str):
    if not content:
        raise ApiError(400, "Không thể đăng bình luận trống!")

    user_id = to_object_id(decoded_user["_id"], "user_id")
    post = await _find_post_in_channel(channel_id, post_id, "Không tìm thấy bài viết!")

    comment = {"_id": ObjectId(), "user": user_id, "content": content, "created_at": datetime.utcnow()}
    await Post.find_one(Post.id == post.id).update({"$push": {"comments": comment}})

    if str(post.user) != decoded_user["_id"]:
        await Notification(
            user=post.user,
            seeder=user_id,
            notification=f"{decoded_user.get('username', '')} just commented your post!",
            url=f"channels/{post.channel}/posts/{post.id}",
        ).insert()

    return ok(message="Đăng bình luận thành công")


async def delete_comment_post(decoded_user: dict, channel_id: str, post_id: str, comment_id: str):
    user_id = to_object_id(decoded_user["_id"], "user_id")
    await Post.find_one(
        {"_id": to_object_id(post_id, "post_id"), "channel": to_object_id(channel_id, "channel_id")}
    ).update({"$pull": {"comments": {"_id": to_object_id(comment_id, "commentId"), "user": user_id}}})
    return ok(message="Xoá bình luận thành công!")


async def delete_post(decoded_user: dict, channel_id: str, post_id: str):
    user_id = to_object_id(decoded_user["_id"], "user_id")
    post = await _find_post_in_channel(channel_id, post_id, "Không tìm thấy bài viết!")
    if post.user != user_id:
        raise ApiError(403, "Bạn không thể xóa bài viết của người khác")

    await post.delete()
    if post.images:
        await delete_file(post.images.get("url", ""))
    return ok(message="Xóa bài viết thành công!")


async def delete_post_by_admin(decoded_user: dict, channel_id: str, post_id: str):
    require_admin(decoded_user, "Bạn không đủ quyền!")

    post = await _find_post_in_channel(channel_id, post_id, "Không tìm thấy bài viết!")
    await post.delete()
    if post.images:
        await delete_file(post.images.get("url", ""))
    return ok(message="Xóa bài viết thành công!")
