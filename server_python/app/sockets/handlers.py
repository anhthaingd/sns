from datetime import datetime
from bson import ObjectId

from app.models.user import User
from app.models.chat import Chat
from app.models.newest_message import NewestMessage


def register_handlers(sio):

    @sio.on("joinCall")
    async def handle_join_call(sid, user):
        if user and user.get("_id"):
            await User.find_one(User.id == ObjectId(user["_id"])).update(
                {"$set": {"socketCallId": sid}}
            )

    @sio.on("callUser")
    async def handle_call_user(sid, data):
        signal_data = data.get("signalData")
        seeder = data.get("seeder")
        receiver = data.get("receiver")
        if receiver and receiver.get("_id"):
            receiver_user = await User.get(ObjectId(receiver["_id"]))
            if receiver_user and receiver_user.socketCallId:
                await sio.emit(
                    "callUser",
                    {"signal": signal_data, "from": seeder},
                    to=receiver_user.socketCallId,
                )

    @sio.on("answerCall")
    async def handle_answer_call(sid, data):
        to_user = data.get("to")
        if to_user and to_user.get("_id"):
            receiver_user = await User.get(ObjectId(to_user["_id"]))
            if receiver_user and receiver_user.socketCallId:
                await sio.emit(
                    "callAccepted",
                    data.get("signal"),
                    to=receiver_user.socketCallId,
                )

    @sio.on("callEnd")
    async def handle_call_end(sid, data):
        receiver = data.get("receiver")
        if receiver and receiver.get("_id"):
            receiver_user = await User.get(ObjectId(receiver["_id"]))
            if receiver_user and receiver_user.socketCallId:
                await sio.emit(
                    "callEnd",
                    {"receiver": {"_id": str(receiver_user.id), "username": receiver_user.username}},
                    to=receiver_user.socketCallId,
                )

    @sio.on("joinChat")
    async def handle_join_chat(sid, user):
        if user and user.get("_id"):
            await User.find_one(User.id == ObjectId(user["_id"])).update(
                {"$set": {"socketId": sid}}
            )

    @sio.on("sendMessage")
    async def handle_send_message(sid, data):
        sender = data.get("sender", {})
        receiver = data.get("receiver", {})
        content = data.get("content", "")
        last_sent = data.get("lastSent", {})

        sender_id = ObjectId(sender["_id"])
        receiver_id = ObjectId(receiver["_id"])

        new_message = Chat(sender=sender_id, receiver=receiver_id, content=content)
        await new_message.insert()

        existed_message = await NewestMessage.find_one({
            "$or": [
                {"sender.user": sender_id, "receiver.user": receiver_id},
                {"sender.user": receiver_id, "receiver.user": sender_id},
            ]
        })

        if not existed_message:
            newest = NewestMessage(
                sender={"user": sender_id, "isRead": True},
                receiver={"user": receiver_id, "isRead": False},
                content=content,
                lastSent=sender_id,
            )
            await newest.insert()
        else:
            if existed_message.sender and str(existed_message.sender.get("user")) == str(sender_id):
                await NewestMessage.find_one({
                    "sender.user": sender_id,
                    "receiver.user": receiver_id,
                }).update({"$set": {
                    "sender.user": sender_id,
                    "sender.isRead": True,
                    "receiver.user": receiver_id,
                    "receiver.isRead": False,
                    "lastSent": sender_id,
                    "content": content,
                    "updated_at": datetime.utcnow(),
                }})
            if existed_message.receiver and str(existed_message.receiver.get("user")) == str(sender_id):
                await NewestMessage.find_one({
                    "sender.user": receiver_id,
                    "receiver.user": sender_id,
                }).update({"$set": {
                    "sender.user": receiver_id,
                    "sender.isRead": False,
                    "receiver.user": sender_id,
                    "receiver.isRead": True,
                    "lastSent": sender_id,
                    "content": content,
                    "updated_at": datetime.utcnow(),
                }})

        await sio.emit("receiveMessage", {**data, "refetch": True}, to=sid)

        receiver_user = await User.get(receiver_id)
        if receiver_user and receiver_user.socketId:
            await sio.emit(
                "receiveMessage",
                {**data, "refetch": True},
                to=receiver_user.socketId,
            )

    @sio.on("disconnect")
    async def handle_disconnect(sid):
        await User.find_one(User.socketId == sid).update(
            {"$set": {"socketId": None}}
        )
        print("Client disconnected")
