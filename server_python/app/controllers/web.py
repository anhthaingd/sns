import json

from app.errors import ApiError
from app.models.web import Web
from app.utils.file_utils import delete_file
from app.utils.ids import to_object_id
from app.utils.permissions import require_admin
from app.utils.responses import ok
from app.utils.serialization import serialize_doc


async def get_web():
    websites = await Web.find_all().to_list()
    return ok(website=serialize_doc(websites[0]) if websites else None)


async def update_web(
    decoded_user: dict,
    web_id: str,
    website_name: str = None,
    color_title: str = None,
    website_quotes_register: str = None,
    website_quotes_login: str = None,
    old_logo: str = None,
    files: dict = None,
    submitted: set[str] | None = None,
):
    require_admin(decoded_user)

    fields = (
        ("website_name", website_name),
        ("color_title", color_title),
        ("website_quotes_register", website_quotes_register),
        ("website_quotes_login", website_quotes_login),
    )
    submitted = submitted if submitted is not None else {name for name, _ in fields}

    try:
        parse_old_logo = json.loads(old_logo) if old_logo else None
    except json.JSONDecodeError as err:
        raise ApiError(400, code="web.invalidOldLogo") from err

    # Chỉ ghi trường request thật sự gửi lên; gán vô điều kiện thì một request
    # chỉ đổi logo sẽ xoá trắng tên website và hai câu chào.
    update_data = {name: (value if value is not None else "") for name, value in fields if name in submitted}

    images = files.get("images", []) if files else []
    if images:
        if parse_old_logo and parse_old_logo.get("name") != "vite.svg":
            await delete_file(parse_old_logo.get("url", ""))
        update_data["logo"] = {"name": images[0]["filename"], "url": images[0]["path"]}

    if update_data:
        await Web.find_one(Web.id == to_object_id(web_id, "web_id")).update({"$set": update_data})
    return ok(code="web.updated")
