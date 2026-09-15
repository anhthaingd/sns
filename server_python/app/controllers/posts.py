import json
import math
from datetime import datetime

from bson import ObjectId

from app.errors import ApiError
from app.messages import message_for
from app.models.channel import Channel
from app.models.notification import Notification
from app.models.post import Post
from app.models.user import User
from app.utils.file_utils import delete_file
from app.utils.ids import to_object_id, to_object_id_or_none
from app.utils.loaders import brief_list, load_channels, load_roles_of, load_users, role_brief, user_brief
from app.utils.permissions import require_admin
from app.utils.responses import ok
from app.utils.sanitize import sanitize_html
from app.utils.search import contains, normalize_search
from app.utils.serialization import serialize_doc, to_jsonable

PAGE_SIZE = 10


def _comment_user_id(comment: dict):
    return comment.get("user")


async def _require_member(decoded_user: dict, channel_id: str):
    """Chỉ thành viên channel mới được ghi vào channel đó.

    Bản cũ chỉ chặn ở đường ĐỌC (`get_channel_details` trả 403
    `channel.notJoined`) mà bỏ trống mọi đường GHI: một `curl` là đăng được bài,
    thích, lưu và bình luận trong channel chưa hề tham gia. Quy tắc đã có sẵn,
    chỉ là chưa áp cho đúng nửa còn lại.

    Trả về ObjectId của channel để chỗ gọi khỏi phải chuyển đổi lần nữa.
    """
    channel_oid = to_object_id(channel_id, "channel_id")
    user_id = to_object_id(decoded_user["_id"], "user_id")
    channel = await Channel.find_one({"_id": channel_oid, "members": user_id})
    if not channel:
        raise ApiError(403, code="channel.notJoined")
    return channel_oid


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
        # Làm sạch cả ở đường ĐỌC: những bài lưu trước khi có bước làm sạch vẫn
        # đang nằm trong DB với HTML thô. Không có dòng này thì phải chạy
        # migration mới an toàn được, và quên chạy là vẫn dính XSS.
        if data.get("content"):
            data["content"] = sanitize_html(data["content"])

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


async def get_posts_in_channel(decoded_user: dict, channel_id: str, page: int = 1):
    # Cùng quy tắc với `get_channel_details`: chưa tham gia thì không đọc được
    # nội dung của channel. Bản cũ chặn ở màn hình chi tiết channel nhưng để hở
    # endpoint danh sách bài, nên gọi thẳng API là đọc được.
    oid = await _require_member(decoded_user, channel_id)
    total_posts = await Post.find(Post.channel == oid).count()
    posts = (
        await Post.find(Post.channel == oid).sort("-updated_at").skip((page - 1) * PAGE_SIZE).limit(PAGE_SIZE).to_list()
    )
    return ok(posts=await _populate_posts(posts), totalPage=_page(total_posts))


async def get_post_details(decoded_user: dict, post_id: str):
    post = await Post.get(to_object_id(post_id, "post_id"))
    if not post:
        raise ApiError(404, code="post.notFound")
    await _require_member(decoded_user, str(post.channel))
    return ok(post=await _populate_post(post))


async def create_post(decoded_user: dict, channel_id: str, content: str = None, files: dict = None):
    if not content or not channel_id:
        raise ApiError(400, code="post.contentAndChannelRequired")

    channel_oid = await _require_member(decoded_user, channel_id)

    # `content` là HTML do trình soạn thảo sinh ra và sẽ được render bằng
    # `dangerouslySetInnerHTML`. Làm sạch TẠI ĐÂY, chỗ duy nhất mọi đường ghi
    # đều đi qua — tin vào trình soạn thảo phía client là tin nhầm chỗ.
    clean = sanitize_html(content)
    if not clean or not clean.strip():
        raise ApiError(400, code="post.contentAndChannelRequired")

    post_data = {
        "user": to_object_id(decoded_user["_id"], "user_id"),
        "content": clean,
        "channel": channel_oid,
    }

    images = files.get("images", []) if files else []
    if images:
        post_data["images"] = {"name": images[0]["filename"], "url": images[0]["path"]}

    await Post(**post_data).insert()
    return ok(code="post.created")


async def updated_post(
    decoded_user: dict,
    channel_id: str,
    post_id: str,
    content: str = None,
    old_images: str = None,
    files: dict = None,
    submitted: set[str] | None = None,
):
    submitted = submitted if submitted is not None else {"content"}
    try:
        parse_old_images = json.loads(old_images) if old_images else None
    except json.JSONDecodeError as err:
        raise ApiError(400, code="post.invalidOldImages") from err

    await _require_member(decoded_user, channel_id)

    post_oid = to_object_id(post_id, "post_id")
    correct_post = await Post.find_one(
        {
            "_id": post_oid,
            "channel": to_object_id(channel_id, "channel_id"),
            "user": to_object_id(decoded_user["_id"], "user_id"),
        }
    )
    if not correct_post:
        raise ApiError(403, code="post.cannotEditOthers")

    # Chỉ ghi `content` khi request thật sự gửi lên. Bản cũ gán vô điều kiện,
    # nên một request chỉ muốn đổi ảnh sẽ ghi `content=None` và xoá trắng bài
    # viết. Client hiện luôn gửi đủ nên chưa ai gặp — đó là may mắn, không phải
    # thiết kế (cùng loại lỗi đã sửa ở `users.update_user`).
    update_data = {"updated_at": datetime.utcnow()}
    if "content" in submitted:
        update_data["content"] = sanitize_html(content) or ""

    images = files.get("images", []) if files else []
    if images:
        if parse_old_images:
            await delete_file(parse_old_images.get("url", ""))
        update_data["images"] = {"name": images[0]["filename"], "url": images[0]["path"]}

    await Post.find_one(Post.id == post_oid).update({"$set": update_data})
    return ok(code="post.updated")


async def _find_post_in_channel(channel_id: str, post_id: str) -> Post:
    """Tìm bài viết trong đúng channel, không thấy thì 404.

    Trước đây hàm này nhận sẵn câu thông báo, và hai chỗ gọi truyền
    `f"Không tìm thấy bài viết {post_id}!"` — tức là ném nguyên ObjectId ra
    cho người dùng đọc, đồng thời sinh ra hai câu khác nhau cho cùng một tình
    huống nên client không dịch được. Giờ chỉ còn một mã duy nhất.
    """
    post = await Post.find_one(
        {"_id": to_object_id(post_id, "post_id"), "channel": to_object_id(channel_id, "channel_id")}
    )
    if not post:
        raise ApiError(404, code="post.notFound")
    return post


async def like_post(decoded_user: dict, channel_id: str, post_id: str):
    await _require_member(decoded_user, channel_id)
    user_id = to_object_id(decoded_user["_id"], "user_id")
    post = await _find_post_in_channel(channel_id, post_id)

    if user_id in post.liked:
        await Post.find_one(Post.id == post.id).update({"$pull": {"liked": user_id}})
        return ok(code="post.unliked")

    if str(post.user) != decoded_user["_id"]:
        await Notification(
            user=post.user,
            seeder=user_id,
            code="notification.postLiked",
            params={"username": decoded_user.get("username", "")},
            notification=message_for("notification.postLiked", {"username": decoded_user.get("username", "")}),
            url=f"channels/{post.channel}/posts/{post.id}",
        ).insert()

    await Post.find_one(Post.id == post.id).update({"$push": {"liked": user_id}})
    return ok(code="post.liked")


async def book_mark_post(decoded_user: dict, channel_id: str, post_id: str):
    await _require_member(decoded_user, channel_id)
    user_id = to_object_id(decoded_user["_id"], "user_id")
    post = await _find_post_in_channel(channel_id, post_id)

    if user_id in post.book_marked:
        await Post.find_one(Post.id == post.id).update({"$pull": {"book_marked": user_id}})
        return ok(code="post.unsaved")

    if str(post.user) != decoded_user["_id"]:
        await Notification(
            user=post.user,
            seeder=user_id,
            code="notification.postSaved",
            params={"username": decoded_user.get("username", "")},
            notification=message_for("notification.postSaved", {"username": decoded_user.get("username", "")}),
            url=None,
        ).insert()

    await Post.find_one(Post.id == post.id).update({"$push": {"book_marked": user_id}})
    return ok(code="post.saved")


async def get_book_mark(decoded_user: dict, page: int = 1):
    user_id = to_object_id(decoded_user["_id"], "user_id")
    total_posts = await Post.find({"book_marked": user_id}).count()
    posts = await Post.find({"book_marked": user_id}).skip((page - 1) * PAGE_SIZE).limit(PAGE_SIZE).to_list()
    return ok(posts=await _populate_posts(posts), totalPage=_page(total_posts))


async def post_comment_post(decoded_user: dict, channel_id: str, post_id: str, content: str):
    if not content:
        raise ApiError(400, code="post.emptyComment")

    await _require_member(decoded_user, channel_id)
    user_id = to_object_id(decoded_user["_id"], "user_id")
    post = await _find_post_in_channel(channel_id, post_id)

    comment = {"_id": ObjectId(), "user": user_id, "content": content, "created_at": datetime.utcnow()}
    await Post.find_one(Post.id == post.id).update({"$push": {"comments": comment}})

    if str(post.user) != decoded_user["_id"]:
        await Notification(
            user=post.user,
            seeder=user_id,
            code="notification.postCommented",
            params={"username": decoded_user.get("username", "")},
            notification=message_for("notification.postCommented", {"username": decoded_user.get("username", "")}),
            url=f"channels/{post.channel}/posts/{post.id}",
        ).insert()

    return ok(code="post.commented")


async def delete_comment_post(decoded_user: dict, channel_id: str, post_id: str, comment_id: str):
    user_id = to_object_id(decoded_user["_id"], "user_id")
    await Post.find_one(
        {"_id": to_object_id(post_id, "post_id"), "channel": to_object_id(channel_id, "channel_id")}
    ).update({"$pull": {"comments": {"_id": to_object_id(comment_id, "commentId"), "user": user_id}}})
    return ok(code="post.commentDeleted")


async def delete_post(decoded_user: dict, channel_id: str, post_id: str):
    user_id = to_object_id(decoded_user["_id"], "user_id")
    post = await _find_post_in_channel(channel_id, post_id)
    if post.user != user_id:
        raise ApiError(403, code="post.cannotDeleteOthers")

    await post.delete()
    if post.images:
        await delete_file(post.images.get("url", ""))
    return ok(code="post.deleted")


async def delete_post_by_admin(decoded_user: dict, channel_id: str, post_id: str):
    require_admin(decoded_user, "Bạn không đủ quyền!")

    post = await _find_post_in_channel(channel_id, post_id)
    await post.delete()
    if post.images:
        await delete_file(post.images.get("url", ""))
    return ok(code="post.deleted")
