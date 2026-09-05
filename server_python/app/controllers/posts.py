import json
import math
from datetime import datetime

from bson import ObjectId

from app.models.channel import Channel
from app.models.notification import Notification
from app.models.post import Post
from app.models.role import Role
from app.models.user import User
from app.utils.file_utils import delete_file
from app.utils.serialization import serialize_doc, to_jsonable


async def _populate_post(post):
    d = serialize_doc(post)
    if post.user:
        u = await User.get(post.user)
        if u:
            d["user"] = {"_id": str(u.id), "email": u.email, "username": u.username, "avatar": u.avatar}
    if post.channel:
        ch = await Channel.get(post.channel)
        if ch:
            d["channel"] = {"_id": str(ch.id), "name": ch.name}
    if post.liked:
        liked_users = await User.find({"_id": {"$in": post.liked}}).to_list()
        d["liked"] = [
            {"_id": str(u.id), "email": u.email, "username": u.username, "avatar": u.avatar} for u in liked_users
        ]
    if post.book_marked:
        bm_users = await User.find({"_id": {"$in": post.book_marked}}).to_list()
        d["book_marked"] = [
            {"_id": str(u.id), "email": u.email, "username": u.username, "avatar": u.avatar} for u in bm_users
        ]
    if post.comments:
        populated_comments = []
        for c in post.comments:
            comment = dict(c) if isinstance(c, dict) else c
            # to_jsonable xử lý cả ObjectId lẫn datetime (created_at) trong comment.
            comment_copy = to_jsonable(dict(comment))
            user_id = comment.get("user")
            if user_id:
                cu = await User.get(ObjectId(str(user_id)))
                if cu:
                    comment_copy["user"] = {
                        "_id": str(cu.id),
                        "email": cu.email,
                        "username": cu.username,
                        "avatar": cu.avatar,
                    }
            populated_comments.append(comment_copy)
        d["comments"] = populated_comments
    return d


async def _populate_post_admin(post):
    d = await _populate_post(post)
    if post.user:
        u = await User.get(post.user)
        if u:
            user_data = {"_id": str(u.id), "email": u.email, "username": u.username, "avatar": u.avatar}
            if u.role:
                role = await Role.get(u.role)
                user_data["role"] = serialize_doc(role) if role else None
            d["user"] = user_data
    return d


async def get_all_posts(decoded_user: dict, page: int = 1, search: str = None):
    try:
        user_id = ObjectId(decoded_user["_id"])
        channels = await Channel.find({"members": user_id}).to_list()
        channel_ids = [ch.id for ch in channels]

        query = {"channel": {"$in": channel_ids}}

        if search:
            regex = {"$regex": search, "$options": "i"}
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
        posts = await Post.find(query).sort("-created_at").skip((page - 1) * 10).limit(10).to_list()
        posts_list = [await _populate_post(p) for p in posts]

        return {
            "status": 200,
            "body": {
                "error": False,
                "success": True,
                "posts": posts_list,
                "totalPage": math.ceil(total_posts / 10) if total_posts > 0 else 1,
                "totalPosts": total_posts,
            },
        }
    except Exception as e:
        return {"status": 500, "body": {"error": True, "success": False, "message": str(e)}}


async def get_posts_by_admin(decoded_user: dict, page: int = 1, channel: str = None):
    try:
        role_data = decoded_user.get("role")
        role_value = role_data.get("value", 0) if isinstance(role_data, dict) else 0
        if role_value != 1:
            return {"status": 403, "body": {"error": True, "success": False, "message": "Bạn không đủ quyền!"}}

        query = {}
        if channel and channel != "null":
            query["channel"] = ObjectId(channel)

        total_posts = await Post.find(query).count()
        posts = await Post.find(query).skip((page - 1) * 10).limit(10).to_list()
        posts_list = [await _populate_post_admin(p) for p in posts]

        return {
            "status": 200,
            "body": {
                "error": False,
                "success": True,
                "posts": posts_list,
                "totalPage": math.ceil(total_posts / 10) if total_posts > 0 else 1,
            },
        }
    except Exception as e:
        return {"status": 500, "body": {"error": True, "success": False, "message": str(e)}}


async def get_posts_by_user(decoded_user: dict, page: int = 1):
    try:
        user_id = ObjectId(decoded_user["_id"])
        total_posts = await Post.find(Post.user == user_id).count()
        posts = await Post.find(Post.user == user_id).skip((page - 1) * 10).limit(10).to_list()
        posts_list = [await _populate_post(p) for p in posts]
        return {
            "status": 200,
            "body": {
                "error": False,
                "success": True,
                "posts": posts_list,
                "totalPage": math.ceil(total_posts / 10) if total_posts > 0 else 1,
            },
        }
    except Exception as e:
        return {"status": 500, "body": {"error": True, "success": False, "message": str(e)}}


async def get_post_from_another_user(decoded_user: dict, target_user_id: str, page: int = 1):
    try:
        user_id = ObjectId(decoded_user["_id"])
        channels = await Channel.find({"members": user_id}).to_list()
        channel_ids = [ch.id for ch in channels]

        query = {"user": ObjectId(target_user_id), "channel": {"$in": channel_ids}}
        total_posts = await Post.find(query).count()
        posts = await Post.find(query).sort("-created_at").skip((page - 1) * 10).limit(10).to_list()
        posts_list = [await _populate_post(p) for p in posts]
        return {
            "status": 200,
            "body": {
                "error": False,
                "success": True,
                "posts": posts_list,
                "totalPage": math.ceil(total_posts / 10) if total_posts > 0 else 1,
            },
        }
    except Exception as e:
        return {"status": 500, "body": {"error": True, "success": False, "message": str(e)}}


async def get_posts_in_channel(channel_id: str, page: int = 1):
    try:
        oid = ObjectId(channel_id)
        total_posts = await Post.find(Post.channel == oid).count()
        posts = await Post.find(Post.channel == oid).sort("-updated_at").skip((page - 1) * 10).limit(10).to_list()
        posts_list = [await _populate_post(p) for p in posts]
        return {
            "status": 200,
            "body": {
                "error": False,
                "success": True,
                "posts": posts_list,
                "totalPage": math.ceil(total_posts / 10) if total_posts > 0 else 1,
            },
        }
    except Exception as e:
        return {"status": 500, "body": {"error": True, "success": False, "message": str(e)}}


async def get_post_details(post_id: str):
    try:
        post = await Post.get(ObjectId(post_id))
        if post:
            post_data = await _populate_post(post)
            return {"status": 200, "body": {"error": False, "success": True, "post": post_data}}
        return {"status": 404, "body": {"error": False, "success": True, "message": "Không tìm thấy bài viết!"}}
    except Exception as e:
        return {"status": 500, "body": {"error": True, "success": False, "message": str(e)}}


async def create_post(decoded_user: dict, channel_id: str, content: str = None, files: dict = None):
    try:
        if not content or not channel_id:
            return {
                "status": 400,
                "body": {"error": True, "success": False, "message": "Yêu cầu bài viết phải có nội dung và channelId!"},
            }

        post_data = {
            "user": ObjectId(decoded_user["_id"]),
            "content": content,
            "channel": ObjectId(channel_id),
        }

        images = files.get("images", []) if files else []
        if images:
            post_data["images"] = {"name": images[0]["filename"], "url": images[0]["path"]}

        post = Post(**post_data)
        await post.insert()
        return {"status": 201, "body": {"error": False, "success": True, "message": "Tạo bài viết thành công!"}}
    except Exception as e:
        return {"status": 500, "body": {"error": True, "success": False, "message": str(e)}}


async def updated_post(
    decoded_user: dict, channel_id: str, post_id: str, content: str = None, old_images: str = None, files: dict = None
):
    try:
        parse_old_images = json.loads(old_images) if old_images else None

        correct_post = await Post.find_one(
            {"_id": ObjectId(post_id), "channel": ObjectId(channel_id), "user": ObjectId(decoded_user["_id"])}
        )
        if not correct_post:
            return {
                "status": 403,
                "body": {
                    "error": True,
                    "success": False,
                    "message": "Bạn không thể sửa bài viết của người khác hoặc bài viết trong channel đã bị xóa!",
                },
            }

        update_data = {"content": content, "updated_at": datetime.utcnow()}

        images = files.get("images", []) if files else []
        if images:
            if parse_old_images:
                await delete_file(parse_old_images.get("url", ""))
            update_data["images"] = {"name": images[0]["filename"], "url": images[0]["path"]}

        await Post.find_one(Post.id == ObjectId(post_id)).update({"$set": update_data})
        return {"status": 200, "body": {"error": False, "success": True, "message": "Cập nhật bài viết thành công"}}
    except Exception as e:
        return {"status": 500, "body": {"error": True, "success": False, "message": str(e)}}


async def like_post(decoded_user: dict, channel_id: str, post_id: str):
    try:
        user_id = ObjectId(decoded_user["_id"])
        post = await Post.find_one({"_id": ObjectId(post_id), "channel": ObjectId(channel_id)})
        if not post:
            return {
                "status": 404,
                "body": {"error": True, "success": False, "message": f"Không tìm thấy bài viết {post_id}!"},
            }

        if user_id in post.liked:
            await Post.find_one(Post.id == ObjectId(post_id)).update({"$pull": {"liked": user_id}})
            return {
                "status": 200,
                "body": {"error": False, "success": True, "message": "Hủy thích bài viết thành công!"},
            }

        if str(post.user) != decoded_user["_id"]:
            await Notification(
                user=post.user,
                seeder=user_id,
                notification=f"{decoded_user.get('username', '')} just liked your post!",
                url=f"channels/{post.channel}/posts/{post.id}",
            ).insert()

        await Post.find_one(Post.id == ObjectId(post_id)).update({"$push": {"liked": user_id}})
        return {"status": 200, "body": {"error": False, "success": True, "message": "Thích bài viết thành công!"}}
    except Exception as e:
        return {"status": 500, "body": {"error": True, "success": False, "message": str(e)}}


async def book_mark_post(decoded_user: dict, channel_id: str, post_id: str):
    try:
        user_id = ObjectId(decoded_user["_id"])
        post = await Post.find_one({"_id": ObjectId(post_id), "channel": ObjectId(channel_id)})
        if not post:
            return {
                "status": 404,
                "body": {"error": True, "success": False, "message": f"Không tìm thấy bài viết {post_id}!"},
            }

        if user_id in post.book_marked:
            await Post.find_one(Post.id == ObjectId(post_id)).update({"$pull": {"book_marked": user_id}})
            return {"status": 200, "body": {"error": False, "success": True, "message": "Hủy lưu bài viết thành công!"}}

        if str(post.user) != decoded_user["_id"]:
            await Notification(
                user=post.user,
                seeder=user_id,
                notification=f"{decoded_user.get('username', '')} just saved your post!",
                url=None,
            ).insert()

        await Post.find_one(Post.id == ObjectId(post_id)).update({"$push": {"book_marked": user_id}})
        return {"status": 200, "body": {"error": False, "success": True, "message": "Lưu bài viết thành công!"}}
    except Exception as e:
        return {"status": 500, "body": {"error": True, "success": False, "message": str(e)}}


async def get_book_mark(decoded_user: dict, page: int = 1):
    try:
        user_id = ObjectId(decoded_user["_id"])
        total_posts = await Post.find({"book_marked": user_id}).count()
        posts = await Post.find({"book_marked": user_id}).skip((page - 1) * 10).limit(10).to_list()
        posts_list = [await _populate_post(p) for p in posts]
        return {
            "status": 200,
            "body": {
                "error": False,
                "success": True,
                "posts": posts_list,
                "totalPage": math.ceil(total_posts / 10) if total_posts > 0 else 1,
            },
        }
    except Exception as e:
        return {"status": 500, "body": {"error": True, "success": False, "message": str(e)}}


async def post_comment_post(decoded_user: dict, channel_id: str, post_id: str, content: str):
    try:
        if not content:
            return {
                "status": 400,
                "body": {"error": True, "success": False, "message": "Không thể đăng bình luận trống!"},
            }

        user_id = ObjectId(decoded_user["_id"])
        comment = {"_id": ObjectId(), "user": user_id, "content": content, "created_at": datetime.utcnow()}

        post = await Post.find_one({"_id": ObjectId(post_id), "channel": ObjectId(channel_id)})
        if not post:
            return {"status": 404, "body": {"error": True, "success": False, "message": "Không tìm thấy bài viết!"}}

        await Post.find_one({"_id": ObjectId(post_id), "channel": ObjectId(channel_id)}).update(
            {"$push": {"comments": comment}}
        )

        if str(post.user) != decoded_user["_id"]:
            await Notification(
                user=post.user,
                seeder=user_id,
                notification=f"{decoded_user.get('username', '')} just commented your post!",
                url=f"channels/{post.channel}/posts/{post.id}",
            ).insert()

        return {"status": 200, "body": {"error": False, "success": True, "message": "Đăng bình luận thành công"}}
    except Exception as e:
        return {"status": 500, "body": {"error": True, "success": False, "message": str(e)}}


async def delete_comment_post(decoded_user: dict, channel_id: str, post_id: str, comment_id: str):
    try:
        user_id = ObjectId(decoded_user["_id"])
        await Post.find_one({"_id": ObjectId(post_id), "channel": ObjectId(channel_id)}).update(
            {"$pull": {"comments": {"_id": ObjectId(comment_id), "user": user_id}}}
        )
        return {"status": 200, "body": {"error": False, "success": True, "message": "Xoá bình luận thành công!"}}
    except Exception as e:
        return {"status": 500, "body": {"error": True, "success": False, "message": str(e)}}


async def delete_post(decoded_user: dict, channel_id: str, post_id: str):
    try:
        user_id = ObjectId(decoded_user["_id"])
        post = await Post.find_one({"channel": ObjectId(channel_id), "_id": ObjectId(post_id)})
        if not post:
            return {"status": 404, "body": {"error": True, "success": False, "message": "Không tìm thấy bài viết!"}}
        if post.user != user_id:
            return {
                "status": 403,
                "body": {"error": True, "success": False, "message": "Bạn không thể xóa bài viết của người khác"},
            }

        await post.delete()
        if post.images:
            await delete_file(post.images.get("url", ""))
        return {"status": 200, "body": {"error": False, "success": True, "message": "Xóa bài viết thành công!"}}
    except Exception as e:
        return {"status": 500, "body": {"error": True, "success": False, "message": str(e)}}


async def delete_post_by_admin(decoded_user: dict, channel_id: str, post_id: str):
    try:
        role_data = decoded_user.get("role")
        role_value = role_data.get("value", 0) if isinstance(role_data, dict) else 0
        if role_value != 1:
            return {"status": 403, "body": {"error": True, "success": False, "message": "Bạn không đủ quyền!"}}

        post = await Post.find_one({"channel": ObjectId(channel_id), "_id": ObjectId(post_id)})
        if post:
            await post.delete()
            if post.images:
                await delete_file(post.images.get("url", ""))
            return {"status": 200, "body": {"error": False, "success": True, "message": "Xóa bài viết thành công!"}}
        return {"status": 404, "body": {"error": True, "success": False, "message": "Không tìm thấy bài viết!"}}
    except Exception as e:
        return {"status": 500, "body": {"error": True, "success": False, "message": str(e)}}
