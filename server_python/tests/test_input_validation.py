"""Kiểm tra tầng validate đầu vào — nơi bản đầu để lọt mọi thứ xuống DB."""

import pytest
from app.errors import ApiError
from app.utils.ids import to_object_id, to_object_id_or_none


@pytest.mark.parametrize("bad", [None, "", "khong-phai-id", 123, [], {}, b""])
def test_to_object_id_rejects_bad_values(bad):
    """`ObjectId(None)` KHÔNG ném lỗi mà sinh id mới ngẫu nhiên.

    Nếu để lọt, một tham số bị thiếu sẽ lặng lẽ thành truy vấn theo một id
    không tồn tại — người dùng thấy 404 khó hiểu thay vì "dữ liệu không hợp lệ",
    và tệ hơn là `$pull`/`$push` chạy trên id vô nghĩa mà không ai biết.
    """
    with pytest.raises(ApiError) as err:
        to_object_id(bad, "test_field")
    assert err.value.status_code == 400
    assert "test_field" in err.value.message


def test_to_object_id_accepts_valid_hex():
    assert str(to_object_id("507f1f77bcf86cd799439011")) == "507f1f77bcf86cd799439011"


@pytest.mark.parametrize("empty", [None, "", "null", "undefined"])
def test_to_object_id_or_none_treats_empty_as_none(empty):
    """Client gửi chuỗi "null" cho tham số lọc không chọn gì — phải hiểu là bỏ lọc."""
    assert to_object_id_or_none(empty, "channel") is None


@pytest.mark.parametrize(
    "path",
    [
        "/api/channels?page=0",
        "/api/channels?page=-5",
        "/api/notifications?page=0",
        "/api/posts?page=-1",
    ],
)
async def test_non_positive_page_is_rejected_not_500(client, user, path):
    """`skip((page-1)*10)` với page <= 0 cho skip âm -> pymongo ném lỗi -> 500."""
    r = await client.get(path, headers=user.headers)
    assert r.status_code == 422, f"{path} trả {r.status_code}: {r.text}"
    assert r.json()["message"]


async def test_comment_body_wrong_type_is_422(client, user, admin, channel):
    """Body JSON sai kiểu phải bị chặn ở cửa, không đi xuống Mongo."""
    await client.post(f"/api/channels/{channel['_id']}", headers=user.headers)
    r = await client.post(f"/api/posts/{channel['_id']}", headers=user.headers, data={"content": "x"})
    assert r.status_code == 201, r.text
    posts = (await client.get(f"/api/posts/{channel['_id']}", headers=user.headers)).json()["posts"]
    post_id = posts[0]["_id"]

    r = await client.post(
        f"/api/posts/{channel['_id']}/{post_id}/comments",
        headers=user.headers,
        json={"content": {"nested": "object"}},
    )
    assert r.status_code == 422, r.text


async def test_bad_object_id_in_path_returns_400_with_safe_message(client, user, admin, channel):
    """Mọi endpoint nhận id trên URL đều phải trả thông báo an toàn, không phải lỗi driver."""
    paths = [
        "/api/users/khong-phai-id",
        "/api/channels/khong-phai-id",
        "/api/posts/get_post_details_in_channel/khong-phai-id",
        "/api/notifications/khong-phai-id",
    ]
    for path in paths:
        method = client.post if path.startswith("/api/notifications") else client.get
        r = await method(path, headers=user.headers)
        assert r.status_code == 400, f"{path} trả {r.status_code}: {r.text}"
        message = r.json()["message"]
        assert "ObjectId" not in message and "12-byte" not in message, f"{path} rò chi tiết driver: {message}"
