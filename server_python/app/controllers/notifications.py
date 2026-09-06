import math

from app.models.notification import Notification
from app.utils.ids import to_object_id
from app.utils.loaders import load_users, user_brief
from app.utils.responses import ok

PAGE_SIZE = 10


async def get_notifications(decoded_user: dict, page: int = 1):
    user_id = to_object_id(decoded_user["_id"], "user_id")
    total_notifications = await Notification.find(Notification.user == user_id).count()
    total_not_read = await Notification.find({"user": user_id, "isRead": False}).count()
    notifications = (
        await Notification.find(Notification.user == user_id)
        .sort("-created_at")
        .skip((page - 1) * PAGE_SIZE)
        .limit(PAGE_SIZE)
        .to_list()
    )

    seeder_map = await load_users([n.seeder for n in notifications])

    notif_list = []
    for n in notifications:
        d = {
            "_id": str(n.id),
            "user": str(n.user),
            "notification": n.notification,
            "code": n.code,
            "params": n.params,
            "url": n.url,
            "created_at": n.created_at.isoformat() if n.created_at else None,
            "isRead": n.isRead,
        }
        seeder = seeder_map.get(str(n.seeder)) if n.seeder else None
        if seeder:
            d["seeder"] = user_brief(seeder)
        notif_list.append(d)

    return ok(
        notifications=notif_list,
        notRead=total_not_read,
        totalPage=math.ceil(total_notifications / PAGE_SIZE) if total_notifications > 0 else 1,
    )


async def read_notification(decoded_user: dict, notification_id: str):
    user_id = to_object_id(decoded_user["_id"], "user_id")
    await Notification.find_one({"_id": to_object_id(notification_id, "notification_id"), "user": user_id}).update(
        {"$set": {"isRead": True}}
    )
    return ok()
