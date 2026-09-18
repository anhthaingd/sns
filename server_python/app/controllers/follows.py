"""Quan hệ theo dõi giữa các tài khoản."""

from app.controllers.user_common import FOLLOW_PAGE_SIZE, brief_users_of, total_page
from app.errors import ApiError
from app.models.follower import Follower
from app.models.following import Following
from app.services.notify import create_and_push
from app.utils.ids import to_object_id
from app.utils.responses import ok


async def get_followers(decoded_user: dict, page: int = 1):
    user_id = to_object_id(decoded_user["_id"], "user_id")
    doc = await Follower.find_one(Follower.user == user_id)
    if not doc:
        return ok(followers=[], totalPage=1)

    all_ids = doc.followers or []
    start = (page - 1) * FOLLOW_PAGE_SIZE
    page_ids = all_ids[start : start + FOLLOW_PAGE_SIZE]
    return ok(
        user=str(doc.user),
        followers=await brief_users_of(page_ids),
        totalPage=total_page(len(all_ids), FOLLOW_PAGE_SIZE),
    )


async def get_following(decoded_user: dict, page: int = 1):
    user_id = to_object_id(decoded_user["_id"], "user_id")
    doc = await Following.find_one(Following.user == user_id)
    if not doc:
        return ok(following=[], totalPage=1)

    all_ids = doc.following or []
    start = (page - 1) * FOLLOW_PAGE_SIZE
    page_ids = all_ids[start : start + FOLLOW_PAGE_SIZE]
    return ok(
        user=str(doc.user),
        following=await brief_users_of(page_ids),
        totalPage=total_page(len(all_ids), FOLLOW_PAGE_SIZE),
    )


async def following_user(decoded_user: dict, target_id: str):
    """Bật/tắt theo dõi một người.

    Hai điểm sửa:

    1. **Dùng `upsert`.** Beanie KHÔNG tự tạo document khi `update` không khớp
       gì, nên tài khoản nào chưa có sẵn bản ghi `Following`/`Follower` sẽ nhận
       về "Follow tài khoản thành công!" mà thực tế không ghi được gì — hỏng âm
       thầm, không có lỗi nào để lần ra. Hiện `register_user` có tạo sẵn hai bản
       ghi đó, nhưng bất kỳ đường tạo user nào khác (script seed, nhập tay) đều
       sinh ra tài khoản hỏng chức năng follow.
    2. **Sinh thông báo khi được follow.** README mục 1.2 hứa "thích, bình luận,
       follow -> hiện trong chuông thông báo", nhưng chỉ có thích và bình luận
       là thật; follow chưa bao giờ tạo `Notification` nào.
    """
    user_id = decoded_user["_id"]
    if user_id == target_id:
        raise ApiError(409, code="follow.cannotFollowSelf")

    user_oid = to_object_id(user_id, "user_id")
    target_oid = to_object_id(target_id, "target_id")
    following_doc = await Following.find_one(Following.user == user_oid)

    if following_doc and target_oid in following_doc.following:
        await Following.find_one(Following.user == user_oid).update({"$pull": {"following": target_oid}})
        await Follower.find_one(Follower.user == target_oid).update({"$pull": {"followers": user_oid}})
        return ok(code="follow.unfollowed")

    await Following.get_pymongo_collection().update_one(
        {"user": user_oid}, {"$addToSet": {"following": target_oid}}, upsert=True
    )
    await Follower.get_pymongo_collection().update_one(
        {"user": target_oid}, {"$addToSet": {"followers": user_oid}}, upsert=True
    )

    username = decoded_user.get("username", "")
    await create_and_push(
        user_id=target_oid,
        seeder_id=user_oid,
        code="notification.userFollowed",
        params={"username": username},
        url=f"profile/{user_id}",
    )

    return ok(code="follow.followed")


async def remove_following(decoded_user: dict, target_id: str):
    user_oid = to_object_id(decoded_user["_id"], "user_id")
    target_oid = to_object_id(target_id, "target_id")
    await Following.find_one(Following.user == user_oid).update({"$pull": {"following": target_oid}})
    await Follower.find_one(Follower.user == target_oid).update({"$pull": {"followers": user_oid}})
    return ok(code="follow.followingRemoved")


async def remove_followers(decoded_user: dict, target_id: str):
    user_oid = to_object_id(decoded_user["_id"], "user_id")
    target_oid = to_object_id(target_id, "target_id")
    await Following.find_one(Following.user == target_oid).update({"$pull": {"following": user_oid}})
    await Follower.find_one(Follower.user == user_oid).update({"$pull": {"followers": target_oid}})
    return ok(code="follow.followerRemoved")


# ---------------------------------------------------------------------------
# Tìm kiếm & quản trị
# ---------------------------------------------------------------------------
