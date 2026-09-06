# 8. Lỗi, log và kiểm thử

## 8.1. Nguyên tắc xử lý lỗi

Một hệ thống tử tế phải đạt ba điều cùng lúc khi có sự cố:

1. **Người dùng** thấy thông báo dễ hiểu, biết nên làm gì tiếp.
2. **Người phát triển** có đủ thông tin để tìm ra nguyên nhân.
3. **Kẻ xấu** không moi được thông tin nội bộ từ thông báo lỗi.

Ba mục tiêu này mâu thuẫn nhau, nên cách giải là: **thông báo ra ngoài thì
chung chung, chi tiết thì ghi vào log**.

## 8.2. Phía máy chủ — một cửa duy nhất

Toàn bộ nằm ở `server_python/app/errors.py`.

```python
class ApiError(Exception):
    def __init__(self, status_code, message=None, *, code=None, params=None): ...
```

Controller **không tự trả về lỗi**, mà chỉ việc "ném" ra:

```python
if job is None:
    raise ApiError(404, code="job.notFound")
```

`code` là **mã ổn định**; câu tiếng Việt tương ứng nằm trong
`server_python/app/messages.py`. Nhờ mã đó mà giao diện dịch được thông báo
sang tiếng Nhật và tiếng Anh — chi tiết ở [tài liệu 9](09-da-ngon-ngu.md).

Có bốn chốt chặn, xếp thành lưới:

| Chốt | Bắt loại lỗi nào | Trả về |
|---|---|---|
| `ApiError` | Lỗi nghiệp vụ mình chủ động báo | Mã và thông báo tiếng Việt của mình |
| `StarletteHTTPException` | 404, 405 do khung web sinh ra | Cùng một định dạng |
| `RequestValidationError` | Dữ liệu gửi lên sai kiểu | 422 kèm tên trường sai |
| `CatchAllErrorMiddleware` | **Mọi thứ còn lại** | 500 + thông báo chung, chi tiết ghi vào log |

Chốt cuối cùng là quan trọng nhất: nó bảo đảm **không có lỗi nào lọt ra ngoài
dưới dạng trang lỗi thô của Python**, vốn có thể lộ đường dẫn file và cấu trúc
mã nguồn.

Mọi phản hồi lỗi đều cùng một hình dạng, nên giao diện chỉ cần một chỗ để đọc:

```json
{
  "error": true,
  "success": false,
  "message": "Không tìm thấy tin tuyển dụng!",
  "code": "job.notFound"
}
```

`message` luôn có (giao diện đọc nó ở 24 chỗ). `code` chỉ xuất hiện khi chỗ ném
lỗi có đặt mã — giao diện ưu tiên dịch theo `code`, không có bản dịch thì hiện
`message`.

### Một chi tiết dễ sai: thứ tự middleware

```python
app.add_middleware(CatchAllErrorMiddleware)   # thêm TRƯỚC  = nằm trong
app.add_middleware(CORSMiddleware, ...)       # thêm SAU    = nằm ngoài
```

Thứ tự này **không được đảo**. Nếu chốt bắt lỗi nằm ngoài CORS, thì mọi phản
hồi 500 sẽ thiếu tiêu đề CORS, và trình duyệt sẽ chặn luôn — người dùng nhận
được lỗi mạng khó hiểu thay vì thông báo lỗi thật.

> 💡 **Middleware là gì?** Là lớp xử lý bọc quanh, chạy trước và sau mỗi
> request — giống mấy lớp bảo vệ ở cổng toà nhà. Thứ tự bọc quyết định ai gác
> ngoài, ai gác trong.

## 8.3. Phía trình duyệt — ba nguồn lỗi, một nơi ghi

Trước đây, lỗi phía trình duyệt chỉ nằm trong console máy người dùng. Ai đó báo
*"web bị lỗi"* thì không có gì để tra.

Nay cả ba nguồn đều đổ về một chỗ:

```
① Lỗi lúc vẽ giao diện  ──▶ ErrorScreen.jsx        ─┐
② Lỗi gọi API           ──▶ errorLogger.js         ─┼─▶ services/logger.js
③ Lỗi ngoài React       ──▶ window.onerror         ─┘         │
   (setTimeout, promise bị bỏ rơi)                            │
                                                              ▼
                                             POST /api/client_logs
                                                              │
                                                              ▼
                                         docker compose logs server
```

### ① Lỗi lúc vẽ giao diện

Một lỗi ở component con vốn làm **trắng cả trang**. Nay `router.jsx` khai báo:

```jsx
{
  path: '/',
  element: <App />,
  errorElement: <ErrorScreen />,   // ← bắt lỗi của MỌI trang con
  children: [ ... ],
}
```

Người dùng thấy màn hình tiếng Việt kèm nút *"Tải lại trang"* và *"Về trang
chủ"*. Chi tiết kỹ thuật **chỉ hiện khi chạy ở chế độ phát triển** — người dùng
cuối không cần, mà stack trace còn có thể lộ đường dẫn nội bộ.

### ② Lỗi gọi API

`client/src/services/redux/middleware/errorLogger.js` đứng ở tầng RTK Query nên
thấy được **mọi** request hỏng, kể cả các query chạy ngầm mà không trang nào
hiển thị.

Một ngoại lệ có chủ đích:

```js
// 401 KHÔNG được coi là lỗi: baseQueryWithReauth gặp 401 sẽ tự gia hạn token
// rồi thử lại, đó là luồng bình thường. Ghi lại chỉ tạo nhiễu.
```

### ③ Lỗi ngoài React

`installGlobalErrorHandlers()` trong `services/logger.js` bắt `window.onerror`
và `unhandledrejection` — những lỗi mà ErrorBoundary của React không nhìn thấy.

### Ba chốt an toàn của bộ ghi log

**Logger không bao giờ được ném lỗi.** Một bộ ghi log làm sập ứng dụng thì tệ
hơn là không có log. Mọi thứ trong file đều bọc `try/catch` và thất bại trong
im lặng.

**Gộp trùng và giới hạn.** Một vòng lặp render hỏng có thể bắn hàng nghìn lỗi
giống hệt nhau trong vài giây:

```js
const DEDUPE_WINDOW_MS = 30_000;      // lỗi giống nhau trong 30s chỉ gửi 1 lần
const MAX_SENT_PER_SESSION = 50;      // tối đa 50 bản ghi mỗi phiên
```

**Chống giả mạo dòng log.** Phía máy chủ đổi ký tự xuống dòng thành `⏎`:

```python
def _one_line(value, limit):
    """Ép về một dòng: log nhiều dòng làm hỏng việc grep và có thể bị giả mạo."""
```

Không có bước này, kẻ xấu gửi lên một "thông báo lỗi" chứa ký tự xuống dòng là
chèn được một dòng trông y hệt log thật của hệ thống.

### Cách xem log

```bash
# Tất cả log của máy chủ
docker compose logs -f server

# Chỉ lỗi từ trình duyệt gửi lên
docker compose logs server | grep fuurin.client
```

Một dòng thật trông như sau:

```
ERROR fuurin.client: [error] render.crash | Cannot read properties of null
  | url=/search?tab=posts | ip=192.168.163.7 | ua=Mozilla/5.0…
  | stack=TypeError: ... ⏎ at Posts.jsx:84 ⏎ at Array.map…
```

Từ dòng này biết ngay: lỗi gì, ở trang nào, dòng nào trong file nào.

### Bảo vệ endpoint mở

`POST /api/client_logs` **không yêu cầu đăng nhập** — vì lỗi có thể xảy ra ngay
ở màn hình đăng nhập, mà đó lại đúng là lúc cần log nhất. Đổi lại phải có ba
lớp chặn:

| Lớp | Giá trị |
|---|---|
| Giới hạn theo IP | 60 request/phút |
| Giới hạn độ dài từng trường | `message` 500 ký tự, `stack` 2000 ký tự |
| Chỉ nhận `level` là `error` hoặc `warn` | không cho client tự chọn mức tuỳ ý |

## 8.4. Kiểm thử

### Ba tầng

```
┌───────────────────────────────────────────────────────────────┐
│ Test đơn vị — hàm thuần, không mạng, không DB                 │
│ tests/test_etl_extract.py    (đọc lương, trình độ, số năm)     │
│ tests/test_matching.py       (chấm điểm, tìm thiếu sót)        │
│ → chạy trong vài mili-giây                                     │
├───────────────────────────────────────────────────────────────┤
│ Test API — gọi thật vào máy chủ đang chạy                     │
│ tests/test_auth.py, test_posts.py, test_jobs_api.py, …         │
│ → 334 test, khoảng 30 giây                                     │
├───────────────────────────────────────────────────────────────┤
│ Test E2E — mở trình duyệt thật, bấm chuột thật                │
│ e2e/test_e2e.py                                                │
│ → 15 test, khoảng 50 giây                                      │
└───────────────────────────────────────────────────────────────┘
```

### Chạy test

```bash
# Test API
docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm api-tests

# Test giao diện (mở trình duyệt thật bên trong container)
docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm e2e-tests

# Sau khi chạy E2E, trả container client về cấu hình thường
docker compose up -d client
```

### Vài quyết định đáng chú ý

**Test parser chạy trên HTML thật đã lưu.** Thư mục
`server_python/tests/fixtures/` chứa HTML lấy về từ 4 trang nguồn. Nhờ vậy test
không cần mạng và không hỏng khi trang nguồn đổi giao diện.

**Có test đếm số truy vấn.** `tests/test_query_count.py` đếm số lệnh thật sự
gửi xuống MongoDB. Nếu ai đó vô tình tạo lại vấn đề N+1, test báo đỏ ngay.

**Có test canh việc suy giảm êm.** `test_score_falls_back_to_rules_when_embedder_is_unavailable`
bảo đảm tắt embedder thì API vẫn trả 200.

**Test E2E phải chờ đúng thứ đang kiểm.** Một test từng chập chờn vì chờ chữ
"Login" — vốn nằm sẵn trong mã giao diện nên xuất hiện **trước** khi dữ liệu từ
máy chủ về. Sửa thành chờ tên website (do API trả về) thì hết chập chờn.

## 8.5. CI — kiểm tự động mỗi lần đẩy code

File `.github/workflows/ci.yml`, gồm ba việc:

| Việc | Chạy gì |
|---|---|
| **Lint backend** | `ruff check` + `ruff format --check` |
| **Lint + build frontend** | `npm ci` → `npm run lint` → `npm run build` |
| **Test** | Dựng cả 5 container → nạp dữ liệu mẫu → 334 test API + 15 test E2E |

### Vì sao phần frontend mới được thêm vào

Trước đây CI **không kiểm gì** cho 10.000 dòng giao diện. Hậu quả đo được: một
biến `Pagination` chưa import và một chỗ `p?.images[0]` đọc sai kiểu dữ liệu đã
nằm trong nhánh chính và **làm sập cả trang tìm kiếm** — trong khi ESLint đã
chỉ đúng cả hai chỗ từ lâu, chỉ là không ai chạy.

### Về con số 37 cảnh báo

```
npm run lint  →  eslint . --max-warnings 37
```

Hiện còn 37 cảnh báo, tất cả thuộc loại `react-hooks/exhaustive-deps`. Chúng
**cố ý chưa được sửa**: sửa mảng phụ thuộc có thể đổi hành vi lúc chạy, nên
phải sửa từng chỗ có kiểm chứng chứ không sửa hàng loạt.

Con số 37 được chốt lại để nó **chỉ được giảm**. Thêm một cảnh báo mới là CI
báo đỏ. Đây gọi là "bánh cóc" — không lùi lại được.

### Ảnh chụp màn hình khi test hỏng

CI được cấu hình tự lưu ảnh màn hình khi test E2E thất bại
(`e2e/artifacts/`), nên đọc log không đoán ra thì còn có ảnh để nhìn.

## 8.6. Tra cứu nhanh khi có sự cố

| Hiện tượng | Xem ở đâu |
|---|---|
| Trang trắng / "Trang gặp sự cố" | `docker compose logs server \| grep fuurin.client` |
| API trả 500 | `docker compose logs server` — tìm dòng ERROR gần nhất |
| API trả 401 dù đã đăng nhập | Vé hết hạn. Xem [tài liệu 4](04-luong-dang-nhap.md) |
| API trả 422 | Dữ liệu gửi lên sai — thông báo có ghi rõ trường nào |
| Gợi ý công ty không có điểm ngữ nghĩa | `docker compose ps` xem `fuurin-embedder` có healthy không |
| Trang việc làm rỗng | Chưa nạp dữ liệu: `docker compose run --rm server python -m scripts.seed_jobs_from_fixtures` |
| Sửa code mà không thấy đổi | Phải build lại: `docker compose up -d --build server` (hoặc `client`) |
| Container không lên | `docker compose logs <tên service>` |

## 8.7. Bản đồ file

| File | Vai trò |
|---|---|
| `server_python/app/errors.py` | Toàn bộ xử lý lỗi phía máy chủ |
| `server_python/app/controllers/client_logs.py` | Nhận log từ trình duyệt |
| `server_python/app/routes/client_logs.py` | Endpoint mở, có giới hạn tần suất |
| `client/src/services/logger.js` | Bộ ghi log dùng chung |
| `client/src/services/redux/middleware/errorLogger.js` | Ghi mọi API hỏng |
| `client/src/components/common/ErrorScreen.jsx` | Màn hình khi trang gặp sự cố |
| `client/src/hooks/useMutationToast.jsx` | Thông báo sau khi lưu/xoá, kèm ghi log |
| `.github/workflows/ci.yml` | Cấu hình kiểm tự động |
| `server_python/tests/` | 334 test API |
| `e2e/test_e2e.py` | 15 test giao diện |

---

Quay lại [Mục lục](README.md)
