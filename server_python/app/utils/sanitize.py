"""Làm sạch HTML của bài viết trước khi lưu và trước khi trả về.

Vì sao cần
----------
Nội dung bài viết là HTML thật (soạn bằng ReactQuill) và được render bằng
`dangerouslySetInnerHTML` ở `client/src/components/ui/SinglePost.jsx`. Trình
soạn thảo không bao giờ sinh ra `<script>` hay `onerror=`, nhưng **API thì
nhận tuốt** — một lệnh `curl` là đủ để nhét mã chạy vào bài viết, và mã đó sẽ
chạy trên phiên đăng nhập của mọi người đọc bài (XSS lưu trữ).

Nguyên tắc: tin trình soạn thảo là sai chỗ. Chốt chặn phải nằm ở máy chủ, nơi
duy nhất mọi đường ghi đều phải đi qua.

Danh sách thẻ cho phép cố ý **hẹp đúng bằng những gì thanh công cụ của Quill
sinh ra** — thêm thẻ vào đây là mở thêm bề mặt tấn công, nên chỉ thêm khi
thanh công cụ thật sự có nút tương ứng.
"""

import bleach

# Đúng bằng các nút đang bật trong `PostComposer.jsx` / `UpdatePostModal.jsx`:
# in đậm, in nghiêng, gạch chân, gạch ngang, danh sách, trích dẫn, khối mã,
# tiêu đề, liên kết, xuống dòng.
ALLOWED_TAGS = {
    "p",
    "br",
    "span",
    "div",
    "b",
    "strong",
    "i",
    "em",
    "u",
    "s",
    "strike",
    "ul",
    "ol",
    "li",
    "blockquote",
    "pre",
    "code",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "a",
}

# `class` để giữ được canh lề / thụt đầu dòng của Quill (`ql-align-center`,
# `ql-indent-1`). KHÔNG cho `style`: `style` mở đường cho `expression()` và
# `url(javascript:...)` trên trình duyệt cũ.
ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "target", "rel"],
    "span": ["class"],
    "p": ["class"],
    "div": ["class"],
    "li": ["class"],
    "ol": ["class"],
    "ul": ["class"],
    "pre": ["class"],
    "code": ["class"],
    "blockquote": ["class"],
}

# Chặn `javascript:` và `data:` — `data:text/html` chạy được script.
ALLOWED_PROTOCOLS = ["http", "https", "mailto"]

_cleaner = bleach.Cleaner(
    tags=ALLOWED_TAGS,
    attributes=ALLOWED_ATTRIBUTES,
    protocols=ALLOWED_PROTOCOLS,
    # `strip=True`: bỏ hẳn thẻ không cho phép thay vì hiện chữ `&lt;script&gt;`
    # ra màn hình cho người đọc.
    strip=True,
)


def sanitize_html(value: str | None) -> str | None:
    """Trả về HTML chỉ còn thẻ/thuộc tính an toàn. `None` giữ nguyên `None`."""
    if value is None:
        return None
    if not value:
        return value
    return _cleaner.clean(value)
