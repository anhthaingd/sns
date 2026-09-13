"""Biết được request GỬI những field nào, khác với field nào có giá trị."""

from fastapi import Request

FORM_CONTENT_TYPES = ("multipart/form-data", "application/x-www-form-urlencoded")


async def submitted_fields(request: Request) -> set[str]:
    """Tên các field thực sự có mặt trong form của request.

    **Vì sao cần.** FastAPI khai báo `x: str | None = Form(None)` thì một field
    gửi lên RỖNG (`intro=`) tới controller dưới dạng `None` — không phân biệt
    được với field KHÔNG GỬI. Hai chuyện đó phải xử lý khác nhau:

      * không gửi  -> giữ nguyên giá trị đang có trong DB;
      * gửi rỗng   -> người dùng cố ý xoá sạch nội dung ô đó.

    Gộp hai trường hợp lại thì hoặc là cập nhật một phần sẽ xoá trắng dữ liệu
    (bản cũ của `update_user`), hoặc là người dùng không xoá nổi phần giới thiệu
    của mình. Đọc thẳng tên field từ form là cách duy nhất tách được.

    Starlette nhớ kết quả `request.form()` nên gọi ở nhiều dependency không tốn
    thêm lần đọc body nào.
    """
    content_type = request.headers.get("content-type", "")
    if not content_type.startswith(FORM_CONTENT_TYPES):
        return set()
    return set((await request.form()).keys())
