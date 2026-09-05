import math
from bson import ObjectId

from app.models.notification import Notification
from app.models.user import User


async def get_notifications(decoded_user: dict, page: int = 1):
    try:
        user_id = ObjectId(decoded_user["_id"])
        total_notifications = await Notification.find(Notification.user == user_id).count()
        total_not_read = await Notification.find({"user": user_id, "isRead": False}).count()
        notifications = await Notification.find(Notification.user == user_id).sort("-created_at").skip((page - 1) * 10).limit(10).to_list()

        notif_list = []
        for n in notifications:
            d = {
                "_id": str(n.id),
                "user": str(n.user),
                "notification": n.notification,
                "url": n.url,
                "created_at": n.created_at.isoformat() if n.created_at else None,
                "isRead": n.isRead,
            }
            if n.seeder:
                seeder = await User.get(n.seeder)
                if seeder:
                    d["seeder"] = {"_id": str(seeder.id), "username": seeder.username, "email": seeder.email, "avatar": seeder.avatar}
            notif_list.append(d)

        return {
            "status": 200,
            "body": {
                "error": False,
                "success": True,
                "notifications": notif_list,
                "notRead": total_not_read,
                "totalPage": math.ceil(total_notifications / 10) if total_notifications > 0 else 1,
            },
        }
    except Exception as e:
        return {"status": 500, "body": {"error": True, "success": False, "message": str(e)}}


async def read_notification(decoded_user: dict, notification_id: str):
    try:
        user_id = ObjectId(decoded_user["_id"])
        await Notification.find_one({"_id": ObjectId(notification_id), "user": user_id}).update({"$set": {"isRead": True}})
        return {"status": 200, "body": {"error": False, "success": True}}
    except Exception as e:
        return {"status": 500, "body": {"error": True, "success": False, "message": str(e)}}
