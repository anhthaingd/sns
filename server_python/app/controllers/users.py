import json
import math
import bcrypt as _bcrypt
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from unidecode import unidecode

from app.models.user import User
from app.models.follower import Follower
from app.models.following import Following
from app.models.role import Role
from app.models.post import Post
from app.models.channel import Channel
from app.models.resume import Resume
from app.utils.token import sign_token
from app.utils.blacklist import blacklist
from app.utils.file_utils import delete_file
from app.utils.serialization import serialize_doc



async def _populate_role(user_doc):
    d = serialize_doc(user_doc)
    if user_doc.role:
        role = await Role.get(user_doc.role)
        if role:
            d["role"] = serialize_doc(role)
    return d


async def _populate_followers(user_id):
    follower_doc = await Follower.find_one(Follower.user == ObjectId(user_id))
    if not follower_doc or not follower_doc.followers:
        return []
    users = await User.find({"_id": {"$in": follower_doc.followers}}).to_list()
    return [{"_id": str(u.id), "email": u.email, "username": u.username, "avatar": u.avatar} for u in users]


async def _populate_following(user_id):
    following_doc = await Following.find_one(Following.user == ObjectId(user_id))
    if not following_doc or not following_doc.following:
        return []
    users = await User.find({"_id": {"$in": following_doc.following}}).to_list()
    return [{"_id": str(u.id), "email": u.email, "username": u.username, "avatar": u.avatar} for u in users]


async def get_user_by_token(decoded_user: dict):
    try:
        user = await User.find_one(User.email == decoded_user["email"])
        if not user:
            return {"status": 404, "body": {"error": True, "success": False, "message": "Không tìm thấy người dùng!"}}
        user_data = await _populate_role(user)
        followers = await _populate_followers(str(decoded_user["_id"]))
        following = await _populate_following(str(decoded_user["_id"]))
        return {
            "status": 200,
            "body": {
                "error": False,
                "success": True,
                "user": user_data,
                "followers": followers,
                "following": following,
            },
        }
    except Exception as e:
        return {"status": 500, "body": {"error": True, "success": False, "message": str(e)}}


async def get_followers(decoded_user: dict, page: int = 1):
    try:
        user_id = ObjectId(decoded_user["_id"])
        total_followers = await Follower.find(Follower.user == user_id).count()
        follower_doc = await Follower.find_one(Follower.user == user_id)
        if not follower_doc:
            return {"status": 200, "body": {"error": False, "success": True, "followers": [], "totalPage": 1}}
        start = (page - 1) * 20
        end = start + 20
        follower_ids = follower_doc.followers[start:end] if follower_doc.followers else []
        users = await User.find({"_id": {"$in": follower_ids}}).to_list()
        followers_list = [{"_id": str(u.id), "email": u.email, "username": u.username, "avatar": u.avatar} for u in users]
        return {
            "status": 200,
            "body": {
                "error": False,
                "success": True,
                "user": str(follower_doc.user),
                "followers": followers_list,
                "totalPage": math.ceil(total_followers / 20) if total_followers > 0 else 1,
            },
        }
    except Exception as e:
        return {"status": 500, "body": {"error": True, "success": False, "message": str(e)}}


async def get_following(decoded_user: dict, page: int = 1):
    try:
        user_id = ObjectId(decoded_user["_id"])
        total_following = await Following.find(Following.user == user_id).count()
        following_doc = await Following.find_one(Following.user == user_id)
        if not following_doc:
            return {"status": 200, "body": {"error": False, "success": True, "following": [], "totalPage": 1}}
        start = (page - 1) * 20
        end = start + 20
        following_ids = following_doc.following[start:end] if following_doc.following else []
        users = await User.find({"_id": {"$in": following_ids}}).to_list()
        following_list = [{"_id": str(u.id), "email": u.email, "username": u.username, "avatar": u.avatar} for u in users]
        return {
            "status": 200,
            "body": {
                "error": False,
                "success": True,
                "user": str(following_doc.user),
                "following": following_list,
                "totalPage": math.ceil(total_following / 20) if total_following > 0 else 1,
            },
        }
    except Exception as e:
        return {"status": 500, "body": {"error": True, "success": False, "message": str(e)}}


async def register_user(email: str, password: str, username: str = None, address: str = None, intro: str = None):
    try:
        if not email or not password:
            return {"status": 400, "body": {"error": True, "success": False, "message": "Yêu cầu cần có email và password!"}}
        duplicated = await User.find_one(User.email == email)
        if duplicated:
            return {"status": 409, "body": {"error": False, "success": True, "message": "Địa chỉ email đã tồn tại!"}}
        user_role = await Role.find_one(Role.value == 0)
        hashed_pwd = _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt(10)).decode("utf-8")
        created_user = User(
            email=email,
            password=hashed_pwd,
            username=username,
            address=address,
            intro=intro,
            role=user_role.id if user_role else None,
        )
        try:
            await created_user.insert()
        except DuplicateKeyError:
            # Hai request đăng ký cùng lúc: unique index là chốt chặn cuối.
            return {"status": 409, "body": {"error": False, "success": True, "message": "Địa chỉ email đã tồn tại!"}}
        await Follower(user=created_user.id).insert()
        await Following(user=created_user.id).insert()
        return {"status": 201, "body": {"error": False, "success": True, "message": "Tạo tài khoản thành công!"}}
    except Exception as e:
        return {"status": 500, "body": {"error": True, "success": False, "message": str(e)}}


async def login_user(email: str, password: str):
    try:
        user = await User.find_one(User.email == email)
        if not user:
            return {"status": 404, "body": {"error": True, "success": False, "message": "Tài khoản chưa được đăng ký!"}}
        if not _bcrypt.checkpw(password.encode("utf-8"), user.password.encode("utf-8")):
            return {"status": 403, "body": {"error": True, "success": False, "message": "Sai mật khẩu!"}}
        role = await Role.get(user.role) if user.role else None
        user_data = serialize_doc(user)
        if role:
            user_data["role"] = serialize_doc(role)
        token = await sign_token(user_data)
        return {"status": 200, "body": {"error": False, "success": True, "accessToken": token}}
    except Exception as e:
        return {"status": 500, "body": {"error": True, "success": False, "message": str(e)}}


async def logout_user(authorization: str):
    parts = authorization.split(" ") if authorization else []
    token = parts[1] if len(parts) > 1 else None
    if token:
        blacklist.add(token)
    return {"status": 200, "body": {"error": False, "success": True, "message": "Đăng xuất tài khoản thành công!"}}


async def get_user_details(user_id: str):
    try:
        oid = ObjectId(user_id)
        user = await User.get(oid)
        if not user:
            return {"status": 404, "body": {"error": True, "success": False, "message": "Không tìm thấy người dùng!"}}

        user_data = {
            "_id": str(user.id),
            "avatar": user.avatar,
            "cover_bg": user.cover_bg,
            "username": user.username,
            "email": user.email,
            "intro": user.intro,
            "address": user.address,
        }
        if user.role:
            role = await Role.get(user.role)
            user_data["role"] = serialize_doc(role) if role else None

        followers = await _populate_followers(user_id)
        following = await _populate_following(user_id)
        posts_count = await Post.find(Post.user == oid).count()
        channels_count = await Channel.find({"members": oid}).count()

        return {
            "status": 200,
            "body": {
                "error": False,
                "success": True,
                "user": user_data,
                "followers": followers,
                "following": following,
                "posts": posts_count,
                "channels": channels_count,
            },
        }
    except Exception as e:
        return {"status": 500, "body": {"error": True, "success": False, "message": str(e)}}


async def update_user(
    user_id: str,
    decoded_user: dict,
    username: str = None,
    old_password: str = None,
    new_password: str = None,
    address: str = None,
    intro: str = None,
    old_avatar: str = None,
    old_cover_bg: str = None,
    update_images: str = None,
    files: dict = None,
):
    try:
        from datetime import datetime

        if str(decoded_user.get("_id")) != str(user_id):
            return {"status": 403, "body": {"error": True, "success": False, "message": "Bạn không thể sửa thông tin của người khác!"}}

        parse_old_avatar = json.loads(old_avatar) if old_avatar else None
        parse_old_cover_bg = json.loads(old_cover_bg) if old_cover_bg else None

        update_data = {
            "username": username,
            "address": address,
            "intro": intro,
            "updated_at": datetime.utcnow(),
        }

        if new_password and new_password != old_password:
            current = await User.get(ObjectId(user_id))
            if not current or not old_password or not _bcrypt.checkpw(
                old_password.encode("utf-8"), (current.password or "").encode("utf-8")
            ):
                return {"status": 403, "body": {"error": True, "success": False, "message": "Mật khẩu cũ không chính xác!"}}
            update_data["password"] = _bcrypt.hashpw(new_password.encode("utf-8"), _bcrypt.gensalt(10)).decode("utf-8")

        images = files.get("images", []) if files else []
        if images and len(images) > 0:
            if update_images == "both":
                update_data["avatar"] = {"name": images[0]["filename"], "url": images[0]["path"]}
                if parse_old_avatar and parse_old_avatar.get("name") != "avatar_trang.jpg":
                    await delete_file(parse_old_avatar.get("url"))
                if len(images) > 1:
                    update_data["cover_bg"] = {"name": images[1]["filename"], "url": images[1]["path"]}
            elif update_images == "avatar":
                if parse_old_avatar and parse_old_avatar.get("name") != "avatar_trang.jpg":
                    await delete_file(parse_old_avatar.get("url"))
                update_data["avatar"] = {"name": images[0]["filename"], "url": images[0]["path"]}
            elif update_images == "cover_bg":
                update_data["cover_bg"] = {"name": images[0]["filename"], "url": images[0]["path"]}
                if parse_old_cover_bg:
                    await delete_file(parse_old_cover_bg.get("url", ""))

        await User.find_one(User.id == ObjectId(user_id)).update({"$set": update_data})
        return {"status": 200, "body": {"error": False, "success": True, "message": "Cập nhật người dùng thành công!"}}
    except Exception as e:
        return {"status": 500, "body": {"error": True, "success": False, "message": str(e)}}


async def following_user(decoded_user: dict, target_id: str):
    try:
        user_id = decoded_user["_id"]
        if user_id == target_id:
            return {"status": 409, "body": {"error": True, "success": False, "message": "Bạn không thể tự follow bản thân!"}}

        following_doc = await Following.find_one(Following.user == ObjectId(user_id))
        target_oid = ObjectId(target_id)

        if following_doc and target_oid in following_doc.following:
            await Following.find_one(Following.user == ObjectId(user_id)).update({"$pull": {"following": target_oid}})
            await Follower.find_one(Follower.user == target_oid).update({"$pull": {"followers": ObjectId(user_id)}})
            return {"status": 200, "body": {"error": False, "success": True, "message": "Hủy follow tài khoản thành công!"}}
        else:
            await Following.find_one(Following.user == ObjectId(user_id)).update({"$push": {"following": target_oid}})
            await Follower.find_one(Follower.user == target_oid).update({"$push": {"followers": ObjectId(user_id)}})
            return {"status": 200, "body": {"error": False, "success": True, "message": "Follow tài khoản thành công!"}}
    except Exception as e:
        return {"status": 500, "body": {"error": True, "success": False, "message": str(e)}}


async def remove_following(decoded_user: dict, target_id: str):
    try:
        user_id = decoded_user["_id"]
        target_oid = ObjectId(target_id)
        await Following.find_one(Following.user == ObjectId(user_id)).update({"$pull": {"following": target_oid}})
        await Follower.find_one(Follower.user == target_oid).update({"$pull": {"followers": ObjectId(user_id)}})
        return {"status": 200, "body": {"error": False, "success": True, "message": "Hủy theo dõi người dùng thành công!"}}
    except Exception as e:
        return {"status": 500, "body": {"error": True, "success": False, "message": str(e)}}


async def remove_followers(decoded_user: dict, target_id: str):
    try:
        user_id = decoded_user["_id"]
        target_oid = ObjectId(target_id)
        await Following.find_one(Following.user == target_oid).update({"$pull": {"following": ObjectId(user_id)}})
        await Follower.find_one(Follower.user == ObjectId(user_id)).update({"$pull": {"followers": target_oid}})
        return {"status": 200, "body": {"error": False, "success": True, "message": "Gỡ thành công người dùng ra khỏi danh sách theo dõi!"}}
    except Exception as e:
        return {"status": 500, "body": {"error": True, "success": False, "message": str(e)}}


async def search_users(decoded_user: dict, search: str = None, page: int = 1):
    try:
        if not search or not page:
            return {"status": 200, "body": {"error": True, "success": False, "users": [], "totalPage": 1, "totalUsers": 0}}

        user_id = ObjectId(decoded_user["_id"])
        regex = {"$regex": search, "$options": "i"}
        query = {
            "_id": {"$ne": user_id},
            "$or": [{"username": regex}, {"email": regex}],
        }
        total_users = await User.find(query).count()
        users = await User.find(query).skip((page - 1) * 10).limit(10).to_list()
        users_list = [
            {"_id": str(u.id), "avatar": u.avatar, "username": u.username, "email": u.email}
            for u in users
        ]
        return {
            "status": 200,
            "body": {
                "error": False,
                "success": True,
                "users": users_list,
                "totalPage": math.ceil(total_users / 10) if total_users > 0 else 1,
                "totalUsers": total_users,
            },
        }
    except Exception as e:
        return {"status": 500, "body": {"error": True, "success": False, "message": str(e)}}


async def get_users_by_admin(decoded_user: dict, page: int = 1, search: str = None):
    try:
        role_data = decoded_user.get("role")
        if isinstance(role_data, dict):
            role_value = role_data.get("value", 0)
            role_id = role_data.get("_id")
        else:
            role_value = 0
            role_id = None

        if role_value != 1:
            return {"status": 403, "body": {"error": True, "success": False, "message": "Bạn không đủ quyền!"}}

        query = {}
        if role_id:
            query["role"] = {"$ne": ObjectId(role_id)}

        if search and search != "null" and search.strip():
            unaccented = unidecode(search)
            query["username"] = {"$regex": unaccented, "$options": "i"}

        total_users = await User.find(query).count()
        users = await User.find(query).skip((page - 1) * 10).limit(10).to_list()
        users_list = [
            {
                "_id": str(u.id),
                "username": u.username,
                "email": u.email,
                "avatar": u.avatar,
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "updated_at": u.updated_at.isoformat() if u.updated_at else None,
                "address": u.address,
            }
            for u in users
        ]
        return {
            "status": 200,
            "body": {
                "error": False,
                "success": True,
                "users": users_list,
                "totalPage": math.ceil(total_users / 10) if total_users > 0 else 1,
                "totalUsers": total_users,
                "curPage": page,
            },
        }
    except Exception as e:
        return {"status": 500, "body": {"error": True, "success": False, "message": str(e)}}


async def get_resume(decoded_user: dict):
    try:
        user_id = ObjectId(decoded_user["_id"])
        resume = await Resume.find_one(Resume.user == user_id)
        resume_data = serialize_doc(resume) if resume else None
        return {"status": 200, "body": {"error": False, "success": True, "resume": resume_data}}
    except Exception as e:
        return {"status": 500, "body": {"error": True, "success": False, "message": str(e)}}


def _parse_json(json_string):
    try:
        return json.loads(json_string) if json_string else None
    except Exception:
        return None


def _filter_different_elements(arr1, arr2):
    different = [obj1 for obj1 in arr1 if not any(obj2.get("name") == obj1.get("name") and obj2.get("value") == obj1.get("value") for obj2 in arr2)]
    different += [obj2 for obj2 in arr2 if not any(obj1.get("name") == obj2.get("name") and obj1.get("value") == obj2.get("value") for obj1 in arr1)]
    return different


async def post_resume(
    decoded_user: dict,
    name: str = None,
    position: str = None,
    old_avatar: str = None,
    birthday: str = None,
    email: str = None,
    address: str = None,
    phone: str = None,
    github: str = None,
    objective: str = None,
    education_name: str = None,
    education_major: str = None,
    education_completion: str = None,
    education_gpa: str = None,
    certificates_name: str = None,
    old_certificates: str = None,
    edit_certificates: str = None,
    experiences: str = None,
    skills: str = None,
    languages: str = None,
    projects: str = None,
    files: dict = None,
):
    try:
        user_id = ObjectId(decoded_user["_id"])
        parse_old_avatar = _parse_json(old_avatar)
        parse_certificate_name = _parse_json(certificates_name) or []
        parse_old_certificates = _parse_json(old_certificates) or []
        parse_edit_certificates = _parse_json(edit_certificates) or []

        resume_data = {
            "user": user_id,
            "name": name,
            "position": position,
            "birthday": birthday,
            "email": email,
            "address": address,
            "phone": phone,
            "github": github,
            "objective": objective,
            "educationName": education_name,
            "educationMajor": education_major,
            "educationCompletion": education_completion,
            "educationGPA": education_gpa,
            "experiences": _parse_json(experiences) or [],
            "skills": _parse_json(skills) or [],
            "languages": _parse_json(languages) or [],
            "projects": _parse_json(projects) or [],
        }

        existed_resume = await Resume.find_one(Resume.user == user_id)
        if existed_resume:
            if parse_old_certificates:
                filter_certs = _filter_different_elements(parse_old_certificates, parse_edit_certificates)
                for f in filter_certs:
                    await delete_file(f.get("url", ""))

            avatar_files = files.get("avatar", []) if files else []
            if avatar_files:
                if parse_old_avatar and parse_old_avatar.get("url"):
                    await delete_file(parse_old_avatar["url"])
                resume_data["avatar"] = {"name": avatar_files[0]["filename"], "url": avatar_files[0]["path"]}

            cert_files = files.get("certificates", []) if files else []
            if cert_files and parse_certificate_name:
                new_certs = [{"name": parse_certificate_name[i] if i < len(parse_certificate_name) else "", "url": cf["path"]} for i, cf in enumerate(cert_files)]
                resume_data["certificates"] = parse_edit_certificates + new_certs
            else:
                resume_data["certificates"] = parse_edit_certificates

            await Resume.find_one(Resume.user == user_id).update({"$set": resume_data})
            return {"status": 200, "body": {"error": False, "success": True, "message": "Lưu CV thành công!"}}

        new_resume = Resume(**resume_data)
        await new_resume.insert()
        return {"status": 200, "body": {"error": False, "success": True, "message": "Lưu CV thành công!"}}
    except Exception as e:
        return {"status": 500, "body": {"error": True, "success": False, "message": str(e)}}
