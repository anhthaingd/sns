import json
from bson import ObjectId

from app.models.web import Web
from app.utils.file_utils import delete_file
from app.utils.serialization import serialize_doc



async def get_web():
    try:
        websites = await Web.find_all().to_list()
        website = serialize_doc(websites[0]) if websites else None
        return {"status": 200, "body": {"error": False, "success": True, "website": website}}
    except Exception as e:
        return {"status": 500, "body": {"error": True, "success": False, "message": str(e)}}


async def update_web(decoded_user: dict, web_id: str, website_name: str = None, color_title: str = None, website_quotes_register: str = None, website_quotes_login: str = None, old_logo: str = None, files: dict = None):
    try:
        role_data = decoded_user.get("role")
        role_value = role_data.get("value", 0) if isinstance(role_data, dict) else 0
        if role_value != 1:
            return {"status": 403, "body": {"error": True, "success": False, "message": "Chức năng này chỉ dành cho admin!"}}

        parse_old_logo = json.loads(old_logo) if old_logo else None
        update_data = {
            "website_name": website_name,
            "color_title": color_title,
            "website_quotes_register": website_quotes_register,
            "website_quotes_login": website_quotes_login,
        }

        images = files.get("images", []) if files else []
        if images:
            if parse_old_logo and parse_old_logo.get("name") != "vite.svg":
                await delete_file(parse_old_logo.get("url", ""))
            update_data["logo"] = {"name": images[0]["filename"], "url": images[0]["path"]}

        await Web.find_one(Web.id == ObjectId(web_id)).update({"$set": update_data})
        return {"status": 200, "body": {"error": False, "success": True, "message": "Cập nhật thông tin website thành công!"}}
    except Exception as e:
        return {"status": 500, "body": {"error": True, "success": False, "message": str(e)}}
