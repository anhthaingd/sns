"""Quan hệ theo dõi giữa các tài khoản."""

from app.controllers.user_common import FOLLOW_PAGE_SIZE, brief_users_of, total_page
from app.errors import ApiError
from app.models.follower import Follower
from app.models.following import Following
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

    await Following.find_one(Following.user == user_oid).update({"$push": {"following": target_oid}})
    await Follower.find_one(Follower.user == target_oid).update({"$push": {"followers": user_oid}})
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
