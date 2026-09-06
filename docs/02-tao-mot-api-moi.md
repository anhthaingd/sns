# 2. Tạo một API mới

Tài liệu này đi hai phần: **mổ xẻ một API có sẵn** để hiểu các mảnh ghép, rồi
**công thức từng bước** để tự làm một cái mới.

## 2.1. Mổ xẻ API `GET /api/jobs` (lấy danh sách việc làm)

Một endpoint hoàn chỉnh trong dự án này gồm **5 file**. Nghe nhiều, nhưng mỗi
file chỉ làm đúng một việc:

```
①  models/job.py        "Một tin tuyển dụng gồm những thông tin gì?"
②  controllers/jobs.py  "Nhận yêu cầu rồi làm gì? Lấy từ kho ra sao?"
③  schemas/responses.py "Trả về cho giao diện thì hình dạng phải thế nào?"
④  routes/jobs.py       "Địa chỉ URL là gì? Ai được gọi? Nhận tham số nào?"
⑤  tests/test_jobs_api.py "Làm sao biết nó đúng?"
```

### ① Model — mô tả dữ liệu

File `server_python/app/models/job.py` khai báo một tin tuyển dụng trông ra sao:

```python
class Job(Document):
    source: str                    # lấy từ trang nào: gaijinpot, daijob...
    title: str                     # tên vị trí
    company_name: str | None       # tên công ty
    prefecture: str | None         # tỉnh/thành ở Nhật
    salary_min: int | None         # lương thấp nhất (yên/năm)
    required_japanese: str | None  # trình độ tiếng Nhật yêu cầu
    required_skills: list[str]     # danh sách kỹ năng
    is_active: bool = True         # tin còn hiệu lực không
```

> 💡 **`str | None` nghĩa là gì?** Là "có thể là chữ, cũng có thể để trống".
> Nhiều tin tuyển dụng không ghi lương, nên trường `salary_min` bắt buộc phải
> cho phép trống — nếu bắt buộc phải có, hệ thống sẽ từ chối lưu những tin đó.

Model còn khai báo **index** (chỉ mục) — giống mục lục của một cuốn sách:

```python
class Settings:
    name = "jobs"
    indexes = [
        IndexModel([("prefecture", ASCENDING)], name="prefecture_idx"),
        ...
    ]
```

Không có mục lục, muốn tìm tin ở Tokyo thì máy phải đọc hết 430 tin. Có mục
lục thì nhảy thẳng tới nơi. Với 430 tin thì chưa thấy khác biệt, với 430.000
tin thì khác một trời một vực.

### ② Controller — phần xử lý

File `server_python/app/controllers/jobs.py`. Đây là nơi chứa **nghiệp vụ** —
tức là các quyết định mang tính "sản phẩm", không phải kỹ thuật thuần tuý.

```python
PAGE_SIZE = 12   # mỗi trang 12 tin

async def get_jobs(page=1, search=None, prefecture=None, ...):
    query = build_job_query(search=search, prefecture=prefecture, ...)
    total = await Job.find(query).count()
    jobs = await Job.find(query).skip((page - 1) * PAGE_SIZE).limit(PAGE_SIZE).to_list()
    return ok(jobs=[...], totalPage=math.ceil(total / PAGE_SIZE), curPage=page)
```

Đọc kỹ một quyết định nghiệp vụ có thật trong file này:

```python
if salary_min:
    # Tin không ghi lương vẫn hiện: lọc bỏ hẳn thì mất một phần ba số tin,
    # và "không ghi lương" không có nghĩa là "lương thấp".
    query["$and"] = [{"$or": [{"salary_max": {"$gte": salary_min}}, {"salary_max": None}]}]
```

Đây không phải chuyện kỹ thuật mà là chuyện **đối xử với dữ liệu thiếu**. Rất
nhiều lỗi khó chịu sinh ra từ chỗ này, nên trong dự án mọi quyết định kiểu vậy
đều được ghi chú ngay tại chỗ.

### ③ Schema — hợp đồng với giao diện

File `server_python/app/schemas/responses.py`:

```python
class JobListResponse(ApiEnvelope):
    jobs: list[dict[str, Any]]
    totalPage: int
    totalJobs: int
    curPage: int
```

Mọi phản hồi trong dự án đều có chung một "lớp vỏ" (`ApiEnvelope`):

```json
{ "error": false, "success": true, "jobs": [ ... ], "totalPage": 36 }
```

Nhờ vỏ chung, giao diện chỉ cần một chỗ duy nhất để biết "thành công hay
thất bại", không phải mỗi API một kiểu.

> 💡 **Vì sao phần bên trong `jobs` chỉ ghi là `dict` chung chung?** Đây là lựa
> chọn có chủ đích, được ghi rõ ở đầu file: dữ liệu cũ trong kho không đồng
> nhất tuyệt đối (ví dụ tác giả bài viết là object khi tài khoản còn, nhưng chỉ
> là một dãy id khi tài khoản đã bị xoá). Khai báo quá chặt sẽ khiến API ném
> lỗi trên chính dữ liệu thật. Phần bên trong được canh bằng test riêng ở
> `tests/test_response_contract.py`.

### ④ Route — cái cửa

File `server_python/app/routes/jobs.py`:

```python
@router.get("/api/jobs", response_model=JobListResponse)
async def route_get_jobs(
    page: int | None = Query(1, ge=1),      # ge=1 nghĩa là phải >= 1
    search: str | None = Query(None),
    prefecture: str | None = Query(None),
    decoded=Depends(get_current_user),      # ← bắt buộc đăng nhập
):
    return await get_jobs(page=page or 1, search=search, prefecture=prefecture)
```

Ba chi tiết quan trọng:

**`ge=1`** — chặn `page=0` và `page=-5`. Trước khi có nó, `page=0` làm máy chủ
tính ra vị trí âm và trả lỗi 500. Đây là lỗi thật đã từng xảy ra trong dự án.

**`Depends(get_current_user)`** — dòng này bắt buộc phải có vé vào cửa. Thiếu
nó là ai cũng gọi được.

**Route chỉ có 3 dòng.** Nó không chứa nghiệp vụ, chỉ nhận tham số rồi chuyển
cho controller. Giữ route mỏng như vậy giúp test nghiệp vụ mà không cần dựng
cả máy chủ.

### ⑤ Test — bằng chứng

Test có thật trong dự án, ở `server_python/tests/test_input_validation.py`:

```python
@pytest.mark.parametrize("path", [
    "/api/channels?page=0",
    "/api/channels?page=-5",
    "/api/posts?page=-1",
])
async def test_non_positive_page_is_rejected_not_500(client, user, path):
    """`skip((page-1)*10)` với page <= 0 cho skip âm -> pymongo ném lỗi -> 500."""
    r = await client.get(path, headers=user.headers)
    assert r.status_code == 422       # từ chối ngay tại cửa, không phải lỗi 500
```

Dòng mô tả trong test giải thích luôn *vì sao* test đó tồn tại — đây là quy ước
của dự án: test không chỉ kiểm tra, mà còn ghi lại lỗi đã từng xảy ra.

## 2.2. Công thức tạo API mới

Giả sử bạn muốn thêm chức năng **"đếm số tin tuyển dụng theo từng tỉnh"** ở
địa chỉ `GET /api/jobs/by_prefecture`.

### Bước 1 — Viết controller

Mở `server_python/app/controllers/jobs.py`, thêm vào cuối:

```python
async def count_jobs_by_prefecture():
    """Đếm số tin đang tuyển theo từng tỉnh, nhiều nhất xếp trước."""
    pipeline = [
        {"$match": {"is_active": True, "prefecture": {"$ne": None}}},
        {"$group": {"_id": "$prefecture", "total": {"$sum": 1}}},
        {"$sort": {"total": -1}},
    ]
    rows = await Job.aggregate(pipeline).to_list()
    return ok(prefectures=[{"name": r["_id"], "total": r["total"]} for r in rows])
```

Ba quy tắc bắt buộc trong dự án:

1. **Luôn trả về qua `ok(...)`** để có lớp vỏ chung.
2. **Báo lỗi bằng `raise ApiError(404, code="job.notFound")`**, đừng tự trả về
   `{"error": ...}`. Có một chỗ duy nhất xử lý mọi lỗi (xem tài liệu 8). Mã
   (`job.notFound`) phải có trong `app/messages.py` — nhờ nó mà giao diện dịch
   được thông báo sang tiếng Nhật và tiếng Anh (xem tài liệu 9).
3. **Viết chú thích cho quyết định nghiệp vụ**, ví dụ vì sao lại bỏ qua tin
   không có tỉnh.

### Bước 2 — Khai báo hình dạng phản hồi

Mở `server_python/app/schemas/responses.py`, thêm:

```python
class PrefectureCountResponse(ApiEnvelope):
    prefectures: list[dict[str, Any]]
```

### Bước 3 — Mở cửa

Mở `server_python/app/routes/jobs.py`:

```python
from app.controllers.jobs import count_jobs_by_prefecture     # thêm vào phần import
from app.schemas.responses import PrefectureCountResponse     # thêm vào phần import

@router.get("/api/jobs/by_prefecture", response_model=PrefectureCountResponse)
async def route_count_by_prefecture(decoded=Depends(get_current_user)):
    return await count_jobs_by_prefecture()
```

> ⚠️ **Thứ tự khai báo route rất quan trọng.** Endpoint mới phải đặt **TRƯỚC**
> `@router.get("/api/jobs/{job_id}")`. Nếu đặt sau, hệ thống sẽ hiểu chữ
> `by_prefecture` là một `job_id` và trả về "không tìm thấy tin tuyển dụng".
> Đây chính là lý do `server_python/app/routes/users.py` được cố ý giữ nguyên
> một file dù đã tách controller ra làm bốn.

### Bước 4 — Viết test

Mở `server_python/tests/test_jobs_api.py`:

```python
async def test_dem_tin_theo_tinh(client, auth_headers):
    res = await client.get("/api/jobs/by_prefecture", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    # Sắp xếp giảm dần: phần tử đầu phải >= phần tử sau.
    totals = [p["total"] for p in data["prefectures"]]
    assert totals == sorted(totals, reverse=True)


async def test_can_dang_nhap_moi_goi_duoc(client):
    res = await client.get("/api/jobs/by_prefecture")
    assert res.status_code == 401
```

### Bước 5 — Chạy thử

```bash
# 1. Nạp lại máy chủ với code mới
docker compose up -d --build server

# 2. Chạy test
docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm api-tests

# 3. Kiểm tra định dạng code (bắt buộc, CI cũng chạy đúng lệnh này)
docker run --rm -v "$PWD":/w -w /w ghcr.io/astral-sh/ruff:0.15.1 \
  check server_python/app --config server_python/pyproject.toml
```

Rồi mở <http://localhost:3000/docs>, tìm endpoint mới và bấm **Try it out**.

## 2.3. Bảng tra nhanh: cần gì thì mở file nào

| Việc cần làm | Mở file |
|---|---|
| Thêm một trường mới cho tin tuyển dụng | `app/models/job.py` |
| Đổi số tin trên mỗi trang | `app/controllers/jobs.py`, hằng `PAGE_SIZE` |
| Đổi nội dung thông báo lỗi | `server_python/app/messages.py` (câu tiếng Việt) + `client/src/i18n/locales/*/error.json` (bản dịch) |
| Thêm quy tắc kiểm tra dữ liệu gửi lên | `app/schemas/requests.py` |
| Cho phép gọi API mà không cần đăng nhập | bỏ `Depends(get_current_user)` ở route |
| Giới hạn số lần gọi (chống spam) | thêm `dependencies=[Depends(rate_limit(...))]`, xem `app/routes/client_logs.py` |

## 2.4. Những lỗi hay gặp

| Hiện tượng | Nguyên nhân thường gặp |
|---|---|
| Gọi API trả 404 | Route đặt sau một route có `{tham_số}` trùng dạng, hoặc quên `include_router` trong `app/main.py` |
| Trả 401 dù đã đăng nhập | Vé vào cửa hết hạn (15 phút). Giao diện tự gia hạn, còn gọi tay bằng `curl` thì phải lấy vé mới |
| Trả 422 | Dữ liệu gửi lên sai kiểu hoặc thiếu — FastAPI chặn ngay tại cửa. Xem thông báo để biết trường nào |
| Trả 500 | Lỗi ngoài dự kiến. Xem `docker compose logs server` để đọc chi tiết |
| Sửa code mà không thấy đổi | Máy chủ chạy trong container theo bản đã đóng gói. Phải `docker compose up -d --build server` |

---

Tiếp theo: [3. Tạo một màn hình mới](03-tao-mot-man-hinh-moi.md)
