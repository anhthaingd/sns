# Kế hoạch triển khai: Mô phỏng đối chứng + Bản đồ thị trường

Thiết kế đã duyệt: [2026-09-06-mo-phong-doi-chung-design.md](2026-09-06-mo-phong-doi-chung-design.md)

## Mục tiêu

Trả lời câu hỏi *"tôi chỉ học được một thứ — học cái nào thì mở ra nhiều cơ hội
nhất?"* bằng cách chấm lại toàn bộ 430 tin tuyển dụng với một bản CV giả định,
rồi so số tin đủ điều kiện trước và sau.

## Kiến trúc

```
                     ┌──────────────────────────────────────┐
                     │  app/services/matching.py  (KHÔNG SỬA)│
                     │  evaluate(job, resume) -> MatchResult │
                     └───────────────▲──────────────────────┘
                                     │ dùng lại nguyên vẹn
        ┌────────────────────────────┴───────────┐
        │  app/services/whatif.py       (MỚI)    │
        │  - sinh phương án                      │
        │  - áp dụng vào bản sao CV              │
        │  - đếm lại số tin đủ điều kiện         │
        └───────────────▲────────────────────────┘
                        │ lấy danh sách kỹ năng đang được săn
        ┌───────────────┴────────────────────────┐
        │  app/services/market.py       (MỚI)    │
        │  tổng hợp nhu cầu kỹ năng / lương /    │
        │  JLPT / tỉnh thành trên kho tin        │
        └────────────────────────────────────────┘
                        │
    GET  /api/match/whatif        gợi ý, xếp theo lợi ích
    POST /api/match/whatif        áp dụng một tổ hợp phương án
    GET  /api/jobs/market         bản đồ thị trường
```

Luồng một request `GET /api/match/whatif`:

```
CV của user  ─┐
              ├─> nạp 430 tin (JobMatchView, không kèm vector)
kho tin ──────┘
              ─> đếm số tin đủ điều kiện HIỆN TẠI            (1 lượt quét, ~2ms)
              ─> với mỗi phương án: nhân bản CV, sửa 1 trường,
                 đếm lại                                      (~2ms mỗi phương án)
              ─> xếp theo số tin mở thêm, kèm trung vị lương của nhóm mở thêm
```

## Công nghệ

Không thêm dependency nào — cả backend lẫn frontend.

| | |
|---|---|
| Backend | Python 3.12, FastAPI, Beanie/MongoDB (đã có) |
| Frontend | React 18, Redux Toolkit Query, react-i18next, SVG thuần (không thêm thư viện biểu đồ) |
| Test | pytest (API + logic thuần), Playwright (E2E) |

## Ràng buộc bắt buộc tuân thủ

1. **KHÔNG sửa `app/services/matching.py`.** Mô phỏng phải chạy đúng bộ luật mà
   trang gợi ý đang dùng. Tách đôi bộ luật là loại lỗi không ai phát hiện cho
   tới lúc demo.
2. **Không phụ thuộc `embedder`.** `is_qualified` thuần luật; mọi lời gọi
   `evaluate` trong `whatif.py` truyền `cosine=None`.
3. **Mọi câu chữ đi qua i18n.** Không viết chuỗi hiển thị vào JSX
   (`eslint-plugin-i18next` chặn), không trả câu tiếng Việt từ backend mà không
   kèm `code`.
4. **Mọi trung vị phải kèm cỡ mẫu `n`.** Nhóm quá nhỏ thì giấu trung vị hoặc gộp
   lại — xem Task 3.
5. Controller `raise ApiError`, không tự bắt `Exception`. Route mỏng, có
   `response_model`.
6. Chạy `ruff` **từ thư mục gốc dự án** (chạy trong `server_python/` cho 11 lỗi giả).

## Bản đồ file

```
server_python/
  app/services/whatif.py                 (mới)
  app/services/market.py                 (mới)
  app/controllers/match.py               (sửa: + 2 controller)
  app/controllers/jobs.py                (sửa: + 1 controller)
  app/controllers/posts.py               (sửa: 3 chỗ tạo Notification)
  app/controllers/channels.py            (sửa: 1 Notification + 1 ok())
  app/controllers/notifications.py       (sửa: trả thêm code/params)
  app/models/notification.py             (sửa: + code, params)
  app/messages.py                        (sửa: + 5 mã)
  app/routes/match.py                    (sửa: + 2 route)
  app/routes/jobs.py                     (sửa: + 1 route)
  app/schemas/responses.py               (sửa: + 3 schema)
  tests/test_whatif.py                   (mới)
  tests/test_market.py                   (mới)
  tests/test_message_codes.py            (sửa: mở rộng phép quét)

client/
  src/services/redux/query/api/matchApi.js   (sửa)
  src/services/redux/query/api/jobsApi.js    (sửa)
  src/services/utils/notificationText.js     (mới)
  src/components/dropdown/NotificationDropdown.jsx (sửa)
  src/layouts/home/Match/WhatIfLayout.jsx    (mới)
  src/layouts/home/Market/MarketLayout.jsx   (mới)
  src/components/ui/BarChart.jsx             (mới)
  src/i18n/locales/{ja,vi,en}/whatif.json    (mới)
  src/i18n/locales/{ja,vi,en}/market.json    (mới)
  src/i18n/locales/{ja,vi,en}/error.json     (sửa: + nhóm notification)
  src/i18n/locales/{ja,vi,en}/nav.json       (sửa: + 2 mục menu)
  src/services/router/router.jsx             (sửa)
  src/layouts/components/LeftAside.jsx       (sửa)

e2e/test_e2e.py                          (sửa: + 2 test)
docs/10-mo-phong-doi-chung.md            (mới)
```

## Lệnh dùng lại nhiều lần

```bash
# Test logic thuần (nhanh, không cần server)
docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm \
  api-tests python -m pytest tests/test_whatif.py -q

# Toàn bộ test API
docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm api-tests

# Lint backend (CHẠY TỪ GỐC DỰ ÁN)
ruff check server_python/app server_python/scripts server_python/tests embedder e2e \
  --config server_python/pyproject.toml

# Lint + đối chiếu bản dịch
cd client && npm run lint
```

---

# Task 1 — Vá lỗ trong bộ kiểm tra: `ok()` thiếu `code=`

**Vì sao làm trước:** đây là lỗi *của chính bộ kiểm tra*. Sửa sau thì mọi mã mới
viết trong các task tiếp theo đều không được canh.

### Step 1.1 — Viết phép kiểm còn thiếu (phải ĐỎ)

Trong `server_python/tests/test_message_codes.py`, thay thế hàm
`test_no_api_error_raised_without_code` bằng hai hàm dưới (giữ nguyên phần còn
lại của file):

```python
def _enclosing_function(tree: ast.AST, node: ast.AST) -> str:
    return next(
        (
            n.name
            for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            and n.lineno <= node.lineno <= (n.end_lineno or n.lineno)
        ),
        "?",
    )


def test_no_api_error_raised_without_code():
    """Mỗi `raise ApiError(...)` phải có `code=` để client dịch được.

    Ngoại lệ duy nhất: `require_admin` nhận câu tuỳ biến từ 8 controller nên
    tra mã ngược qua bảng `_MESSAGE_CODES`.
    """
    allowed_without_code = {("utils/permissions.py", "require_admin")}
    offenders = []
    for path in _python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call)):
                continue
            func = node.exc.func
            if not (isinstance(func, ast.Name) and func.id == "ApiError"):
                continue
            if any(kw.arg == "code" for kw in node.exc.keywords):
                continue
            rel = str(path.relative_to(APP_DIR))
            enclosing = _enclosing_function(tree, node)
            if (rel, enclosing) in allowed_without_code:
                continue
            offenders.append(f"{rel}:{node.lineno} trong {enclosing}()")
    assert not offenders, "ApiError thiếu `code=` (client sẽ không dịch được): " + ", ".join(offenders)


def test_no_success_message_without_code():
    """`ok(message="...")` không kèm `code=` cũng lọt ra tiếng Việt y như ApiError.

    Phép kiểm cũ chỉ soi `raise ApiError(...)` nên nhánh này đi lọt suốt: một
    `ok(message=f"...")` vẫn dựng toast bằng câu tiếng Việt cứng.

    `ok()` không truyền `message` thì không có câu nào để dịch -> hợp lệ.
    """
    offenders = []
    for path in _python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)):
                continue
            if node.func.id != "ok":
                continue
            kwargs = {kw.arg for kw in node.keywords}
            if "message" in kwargs and "code" not in kwargs:
                offenders.append(f"{path.relative_to(APP_DIR)}:{node.lineno} trong {_enclosing_function(tree, node)}()")
    assert not offenders, "ok(message=...) thiếu `code=`: " + ", ".join(offenders)
```

Chạy:

```bash
docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm \
  api-tests python -m pytest tests/test_message_codes.py -q
```

Kỳ vọng: **FAIL** với

```
AssertionError: ok(message=...) thiếu `code=`: controllers/channels.py:160 trong remove_user_from_channel()
```

### Step 1.2 — Thêm mã vào danh mục backend

`server_python/app/messages.py`, thêm vào dict `MESSAGES` cạnh các mã `channel.*`:

```python
    "channel.userRemoved": "Đã xóa người dùng khỏi channel!",
```

### Step 1.3 — Sửa chỗ gọi

`server_python/app/controllers/channels.py`, dòng 160:

```python
    return ok(code="channel.userRemoved")
```

> Câu cũ là `f"Đã xóa người dùng id:{user_id_to_remove} ra khỏi channel!"` — nó
> còn ném cả ObjectId thô ra cho người dùng cuối. Bỏ luôn.

### Step 1.4 — Thêm bản dịch cho 3 ngôn ngữ

`client/src/i18n/locales/vi/error.json`, trong nhóm `server.channel`:

```json
      "userRemoved": "Đã xóa người dùng khỏi channel!"
```

`client/src/i18n/locales/ja/error.json`:

```json
      "userRemoved": "ユーザーをチャンネルから削除しました。"
```

`client/src/i18n/locales/en/error.json`:

```json
      "userRemoved": "The user has been removed from the channel."
```

Chạy lại lệnh ở 1.1 → kỳ vọng **PASS** (20 test).

```bash
cd client && npm run check:i18n
```
Kỳ vọng: `✓ 3 ngôn ngữ (en, ja, vi) · 12 namespace · 461 khoá — khớp nhau hoàn toàn`

### Step 1.5 — Commit

```bash
git add server_python/tests/test_message_codes.py server_python/app/messages.py \
        server_python/app/controllers/channels.py client/src/i18n/locales
git commit -m "fix: canh ca ok(message=) thieu code=, va chan lo ObjectId ra toast"
```

---

# Task 2 — Thông báo đa ngôn ngữ

**Vấn đề:** `Notification.notification` lưu câu chữ **cứng** vào DB, lẫn hai ngôn ngữ:

```python
notification=f"{username} just liked your post!"        # posts.py:249
notification=f"Admin đã xóa bạn ra khỏi channel {c}!"   # channels.py:155
```

221 bản ghi đang có trong DB. **Không migrate** — thêm `code`/`params` và để bản
ghi cũ rơi về trường `notification` sẵn có.

### Step 2.1 — Phép kiểm mới (phải ĐỎ)

Thêm vào cuối `server_python/tests/test_message_codes.py`:

```python
# ---------------------------------------------------------------------------
# Thông báo trong chuông — cũng là câu chữ do backend sinh ra
# ---------------------------------------------------------------------------


def test_every_notification_has_a_code():
    """`Notification(notification="...")` là câu chữ cứng nằm lại trong DB.

    Khác với toast: toast sinh ra rồi mất, còn thông báo thì được LƯU. Một câu
    tiếng Anh ghi vào DB hôm nay sẽ còn hiện giữa giao diện tiếng Nhật nhiều
    tháng sau, và không phép dịch nào cứu được nữa.
    """
    offenders = []
    for path in _python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)):
                continue
            if node.func.id != "Notification":
                continue
            if any(kw.arg == "code" for kw in node.keywords):
                continue
            offenders.append(f"{path.relative_to(APP_DIR)}:{node.lineno} trong {_enclosing_function(tree, node)}()")
    assert not offenders, "Notification thiếu `code=`: " + ", ".join(offenders)
```

Đồng thời mở rộng phép quét mã ở đầu file để mã của thông báo cũng bị đối chiếu
với file dịch — sửa đúng một dòng:

```python
MESSAGE_CALLERS = {"ApiError", "ok", "Notification"}
```

Chạy lệnh ở 1.1 → kỳ vọng **FAIL**, liệt kê 4 chỗ:

```
Notification thiếu `code=`: controllers/channels.py:153 trong remove_user_from_channel(),
controllers/posts.py:247 trong like_post(), controllers/posts.py:267 trong book_mark_post(),
controllers/posts.py:296 trong create_comment()
```

### Step 2.2 — Thêm hai trường vào model

`server_python/app/models/notification.py`:

```python
class Notification(Document):
    user: PydanticObjectId | None = None
    seeder: PydanticObjectId | None = None
    # Câu chữ dựng sẵn. Với bản ghi mới đây chỉ là bản dự phòng; giao diện ưu
    # tiên dịch theo `code`. Giữ lại để 221 bản ghi cũ (tạo trước khi có `code`)
    # vẫn đọc được mà không phải migrate.
    notification: str | None = None
    # Mã ổn định + tham số thô, cùng cơ chế với `ApiError`/`ok`.
    code: str | None = None
    params: dict = Field(default_factory=dict)
    url: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    isRead: bool = False
```

### Step 2.3 — Thêm 4 mã vào danh mục

`server_python/app/messages.py`:

```python
    "notification.postLiked": "{username} vừa thích bài viết của bạn!",
    "notification.postSaved": "{username} vừa lưu bài viết của bạn!",
    "notification.postCommented": "{username} vừa bình luận bài viết của bạn!",
    "notification.removedFromChannel": "Bạn đã bị xóa khỏi channel {channel}!",
```

### Step 2.4 — Sửa 4 chỗ tạo thông báo

`server_python/app/controllers/posts.py` — `like_post`:

```python
        await Notification(
            user=post.user,
            seeder=user_id,
            code="notification.postLiked",
            params={"username": decoded_user.get("username", "")},
            notification=message_for("notification.postLiked", {"username": decoded_user.get("username", "")}),
            url=f"channels/{post.channel}/posts/{post.id}",
        ).insert()
```

`book_mark_post` — y hệt, đổi `postLiked` → `postSaved`, `url=None`.
`create_comment` — y hệt, đổi thành `postCommented`, giữ `url` như cũ.

`server_python/app/controllers/channels.py`:

```python
        await Notification(
            user=target_oid,
            seeder=to_object_id(decoded_user["_id"], "user_id"),
            code="notification.removedFromChannel",
            params={"channel": channel.name},
            notification=message_for("notification.removedFromChannel", {"channel": channel.name}),
            url=None,
        ).insert()
```

Thêm import ở cả hai file:

```python
from app.messages import message_for
```

> **Vì sao vẫn ghi `notification=`:** đó là bản dự phòng cho trường hợp client
> chưa có bản dịch cho mã mới. Cùng nguyên tắc với `ApiError`: không bao giờ để
> người dùng nhìn thấy khoá thô.

### Step 2.5 — Trả thêm `code`/`params` ra API

`server_python/app/controllers/notifications.py`, trong vòng lặp dựng `d`:

```python
        d = {
            "_id": str(n.id),
            "user": str(n.user),
            "notification": n.notification,
            "code": n.code,
            "params": n.params,
            "url": n.url,
            "created_at": n.created_at.isoformat() if n.created_at else None,
            "isRead": n.isRead,
        }
```

### Step 2.6 — Bản dịch 3 ngôn ngữ

`client/src/i18n/locales/vi/error.json`, thêm nhóm `notification` bên trong `server`:

```json
    "notification": {
      "postLiked": "{{username}} vừa thích bài viết của bạn!",
      "postSaved": "{{username}} vừa lưu bài viết của bạn!",
      "postCommented": "{{username}} vừa bình luận bài viết của bạn!",
      "removedFromChannel": "Bạn đã bị xóa khỏi channel {{channel}}!"
    }
```

`ja`:

```json
    "notification": {
      "postLiked": "{{username}}さんがあなたの投稿にいいねしました。",
      "postSaved": "{{username}}さんがあなたの投稿を保存しました。",
      "postCommented": "{{username}}さんがあなたの投稿にコメントしました。",
      "removedFromChannel": "チャンネル「{{channel}}」から削除されました。"
    }
```

`en`:

```json
    "notification": {
      "postLiked": "{{username}} liked your post.",
      "postSaved": "{{username}} saved your post.",
      "postCommented": "{{username}} commented on your post.",
      "removedFromChannel": "You were removed from the channel {{channel}}."
    }
```

> **Vì sao để trong `error.json` chứ không tạo namespace riêng:** phép kiểm
> `test_client_has_translation_for_every_backend_code` đối chiếu **toàn bộ**
> `MESSAGES` với đúng một file. Tách ra file thứ hai thì phải phân nhánh phép
> kiểm theo tiền tố mã, và mỗi nhánh là một chỗ để quên. Đổi lại, tên file
> `error.json` không còn khớp nội dung — nó là "câu chữ do máy chủ sinh ra", đã
> ghi chú ở đầu file.

### Step 2.7 — Client dịch theo mã

File mới `client/src/services/utils/notificationText.js`:

```js
/**
 * Chữ hiển thị cho một thông báo trong chuông.
 *
 * Cùng khuôn với `serverMessage`: ưu tiên dịch theo `code`, không có bản dịch
 * thì rơi về câu chữ mà backend đã dựng sẵn và lưu trong DB.
 *
 * Bản ghi tạo trước khi có `code` (221 cái tại thời điểm viết) không có mã —
 * chúng đi thẳng vào nhánh dự phòng, nên không cần migrate dữ liệu.
 */
export const notificationText = (t, notification) => {
  const code = notification?.code;
  if (code) {
    // Mã backend là `notification.postLiked`, khoá dịch là
    // `error:server.notification.postLiked` — cùng một đường dẫn.
    const translated = t(`error:server.${code}`, {
      ...(notification?.params || {}),
      defaultValue: '',
    });
    if (translated) return translated;
  }
  return notification?.notification || '';
};
```

`client/src/components/dropdown/NotificationDropdown.jsx`:

```jsx
import { notificationText } from '../../services/utils/notificationText';
```

và đổi dòng render (khoảng dòng 122):

```jsx
                  <p>{notificationText(t, n)}</p>
```

Kiểm `useTranslation` ở đầu component đã khai báo namespace `error`; nếu chưa:

```jsx
  const { t } = useTranslation(['nav', 'common', 'error']);
```

### Step 2.8 — Chạy lại

```bash
docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm \
  api-tests python -m pytest tests/test_message_codes.py -q
```
Kỳ vọng: **PASS**.

```bash
docker compose restart server && cd client && npm run lint
```
Kỳ vọng: `0 errors`, `✓ 3 ngôn ngữ ... khớp nhau hoàn toàn`.

**Kiểm bằng mắt:** đăng nhập hai tài khoản, A thích bài của B → chuông của B
hiện tiếng Nhật. Đổi sang `VI` → cùng thông báo đó đổi sang tiếng Việt **không
cần tải lại trang**. Cuộn xuống các thông báo cũ → vẫn hiện câu cũ, không vỡ.

### Step 2.9 — Commit

```bash
git add server_python/app/models/notification.py server_python/app/messages.py \
        server_python/app/controllers/posts.py server_python/app/controllers/channels.py \
        server_python/app/controllers/notifications.py server_python/tests/test_message_codes.py \
        client/src/services/utils/notificationText.js \
        client/src/components/dropdown/NotificationDropdown.jsx client/src/i18n/locales
git commit -m "feat: thong bao trong chuong dich duoc 3 ngon ngu, khong migrate ban ghi cu"
```

---

# Task 3 — Tầng thống kê thị trường

### Step 3.1 — Test (phải ĐỎ)

File mới `server_python/tests/test_market.py`:

```python
"""Test tầng thống kê thị trường.

Hai thứ được canh ở đây, và cả hai đều là chuyện trung thực chứ không phải
chuyện code chạy đúng:

  * mọi trung vị phải kèm cỡ mẫu, vì nhiều nhóm chỉ có 12-14 tin;
  * nhóm quá nhỏ không được đứng riêng như thể nó là một quy luật.
"""

from app.services.market import MIN_GROUP_SIZE, median


def test_median_ignores_missing_values():
    assert median([None, 100, None, 300, 200]) == 200


def test_median_returns_none_when_nothing_is_known():
    assert median([None, None]) is None
    assert median([]) is None


async def test_market_requires_authentication(client):
    assert (await client.get("/api/jobs/market")).status_code == 401


async def test_market_reports_skill_demand(client, user, has_jobs):
    r = await client.get("/api/jobs/market", headers=user.headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["totalJobs"] > 0
    assert body["skills"], "không có kỹ năng nào — dữ liệu ETL trống?"
    top = body["skills"][0]
    assert top["jobs"] >= body["skills"][-1]["jobs"], "phải xếp giảm dần theo số tin"


async def test_every_median_comes_with_its_sample_size(client, user, has_jobs):
    """Trung vị không kèm cỡ mẫu là trưng nhiễu như thể là quy luật."""
    body = (await client.get("/api/jobs/market", headers=user.headers)).json()
    for group in ("skills", "japanese", "prefectures"):
        for row in body[group]:
            assert "salarySample" in row, f"{group}: thiếu cỡ mẫu"
            if row["salaryMedian"] is not None:
                assert row["salarySample"] >= MIN_GROUP_SIZE, (
                    f"{group}/{row}: trung vị tính trên {row['salarySample']} tin thì không nói lên gì"
                )


async def test_small_skill_groups_are_merged_instead_of_listed(client, user, has_jobs):
    body = (await client.get("/api/jobs/market", headers=user.headers)).json()
    named = [s for s in body["skills"] if s["skill"] != "__other__"]
    assert all(s["jobs"] >= MIN_GROUP_SIZE for s in named), "nhóm nhỏ phải được gộp vào __other__"
```

Chạy:
```bash
docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm \
  api-tests python -m pytest tests/test_market.py -q
```
Kỳ vọng: **FAIL** với `ModuleNotFoundError: No module named 'app.services.market'`.

### Step 3.2 — Cài đặt

File mới `server_python/app/services/market.py`:

```python
"""Thống kê thị trường việc làm trên kho tin đã ETL.

Dùng cho hai việc: dựng màn hình "bản đồ thị trường", và cung cấp danh sách kỹ
năng đang được săn cho tầng mô phỏng đối chứng (`app/services/whatif.py`).

**Nguyên tắc trung thực của module này.** Đo trên chính dữ liệu dự án: nhóm tin
yêu cầu tiếng Nhật mức `none` chỉ có 12 tin ghi lương, mức `fluent` có 12 tin.
Một trung vị tính trên 12 mẫu mà hiển thị ngang hàng với trung vị tính trên 101
mẫu là đánh lừa người đọc. Nên:

  * mọi trung vị đi kèm `salarySample`;
  * `salarySample < MIN_GROUP_SIZE` thì KHÔNG trả trung vị (trả `None`);
  * riêng kỹ năng, nhóm dưới ngưỡng được gộp vào một mục `__other__` thay vì
    liệt kê thành hàng chục dòng nhiễu.
"""

from app.models.job import LANGUAGE_LEVELS, Job

# Dưới ngưỡng này thì con số là giai thoại, không phải số liệu.
MIN_GROUP_SIZE = 10

# Trần số dòng trả về, để response không phình theo số kỹ năng trong từ điển.
SKILL_LIMIT = 30
PREFECTURE_LIMIT = 15

OTHER = "__other__"


def median(values: list[int | None]) -> int | None:
    known = sorted(v for v in values if v is not None)
    if not known:
        return None
    return known[len(known) // 2]


def _salary_fields(salaries: list[int | None]) -> dict:
    known = [s for s in salaries if s is not None]
    return {
        "salaryMedian": median(known) if len(known) >= MIN_GROUP_SIZE else None,
        "salarySample": len(known),
    }


async def _grouped(field: str, unwind: bool = False) -> list[dict]:
    pipeline: list[dict] = [{"$match": {"is_active": True}}]
    if unwind:
        pipeline.append({"$unwind": f"${field}"})
    pipeline += [
        {"$group": {"_id": f"${field}", "jobs": {"$sum": 1}, "salaries": {"$push": "$salary_min"}}},
        {"$sort": {"jobs": -1}},
    ]
    return await Job.aggregate(pipeline).to_list()


async def skill_demand(limit: int = SKILL_LIMIT) -> list[dict]:
    rows = await _grouped("required_skills", unwind=True)

    big = [r for r in rows if r["jobs"] >= MIN_GROUP_SIZE][:limit]
    small = [r for r in rows if r["jobs"] < MIN_GROUP_SIZE]

    result = [{"skill": r["_id"], "jobs": r["jobs"], **_salary_fields(r["salaries"])} for r in big]
    if small:
        result.append(
            {
                "skill": OTHER,
                "jobs": sum(r["jobs"] for r in small),
                "distinct": len(small),
                **_salary_fields([s for r in small for s in r["salaries"]]),
            }
        )
    return result


async def japanese_distribution() -> list[dict]:
    rows = {r["_id"]: r for r in await _grouped("required_japanese")}
    out = []
    for level in LANGUAGE_LEVELS:
        r = rows.get(level)
        if not r:
            continue
        out.append({"level": level, "jobs": r["jobs"], **_salary_fields(r["salaries"])})
    unstated = rows.get(None)
    if unstated:
        out.append({"level": None, "jobs": unstated["jobs"], **_salary_fields(unstated["salaries"])})
    return out


async def prefecture_distribution(limit: int = PREFECTURE_LIMIT) -> list[dict]:
    rows = await _grouped("prefecture")
    named = [r for r in rows if r["_id"]][:limit]
    return [{"prefecture": r["_id"], "jobs": r["jobs"], **_salary_fields(r["salaries"])} for r in named]


async def snapshot() -> dict:
    """Toàn bộ số liệu cho một lần vẽ màn hình."""
    total = await Job.find({"is_active": True}).count()
    return {
        "totalJobs": total,
        "minGroupSize": MIN_GROUP_SIZE,
        "skills": await skill_demand(),
        "japanese": await japanese_distribution(),
        "prefectures": await prefecture_distribution(),
    }
```

### Step 3.3 — Controller + route + schema

`server_python/app/controllers/jobs.py`, thêm ở cuối file:

```python
async def job_market(decoded_user: dict):
    """Bản đồ thị trường — không phụ thuộc CV, ai đăng nhập cũng xem được."""
    return ok(**await market.snapshot())
```

Thêm import ở đầu file:

```python
from app.services import market
```

`server_python/app/schemas/responses.py`, thêm cạnh các schema việc làm:

```python
class MarketResponse(ApiEnvelope):
    totalJobs: int
    minGroupSize: int
    skills: list[dict[str, Any]]
    japanese: list[dict[str, Any]]
    prefectures: list[dict[str, Any]]
```

`server_python/app/routes/jobs.py` — thêm route. **Đặt TRƯỚC route
`/api/jobs/{job_id}`**, nếu không `market` sẽ bị bắt làm `job_id` và trả 400:

```python
@router.get("/api/jobs/market", response_model=MarketResponse)
async def route_job_market(decoded=Depends(get_current_user)):
    return await job_market(decoded)
```

và bổ sung `job_market` vào dòng import controller, `MarketResponse` vào import schema.

### Step 3.4 — Chạy lại

```bash
docker compose restart server
docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm \
  api-tests python -m pytest tests/test_market.py -q
```
Kỳ vọng: **PASS** (6 test).

Kiểm bằng mắt:
```bash
curl -s localhost:3000/api/jobs/market -H "Authorization: Bearer $TOKEN" | python3 -m json.tool | head -30
```

### Step 3.5 — Commit

```bash
git add server_python/app/services/market.py server_python/app/controllers/jobs.py \
        server_python/app/routes/jobs.py server_python/app/schemas/responses.py \
        server_python/tests/test_market.py
git commit -m "feat: tang thong ke thi truong viec lam, co nguong cho mau"
```

---

# Task 4 — Engine mô phỏng (logic thuần, không DB)

### Step 4.1 — Test (phải ĐỎ)

File mới `server_python/tests/test_whatif.py`:

```python
"""Test engine mô phỏng đối chứng — dựng CV và tin bằng tay, không cần DB.

Test quan trọng nhất trong file này là `test_deltas_do_not_add_up`: nó pin lại
đúng cái tính chất khiến chức năng này phải tồn tại dưới dạng một engine chấm
lại, chứ không phải một bảng tra sẵn.
"""

from app.models.job import JobMatchView
from app.models.resume import ResumeMatchView
from app.services.whatif import Action, apply_actions, candidate_actions, qualified_job_ids, simulate
from bson import ObjectId


def make_job(**kwargs) -> JobMatchView:
    defaults = {"_id": ObjectId(), "url": "https://example.com/1", "title": "Engineer"}
    return JobMatchView(**{**defaults, **kwargs})


def make_resume(**kwargs) -> ResumeMatchView:
    return ResumeMatchView(**kwargs)


# ---------------------------------------------------------------------------
# Áp dụng phương án
# ---------------------------------------------------------------------------


def test_applying_a_skill_does_not_mutate_the_original_resume():
    """Nhân bản chứ không sửa tại chỗ — nếu không, lượt mô phỏng thứ hai sẽ
    chấm trên một CV đã bị lượt trước làm bẩn."""
    resume = make_resume(skills_normalized=["Python"])
    after = apply_actions(resume, [Action(kind="skill", value="AWS")])

    assert resume.skills_normalized == ["Python"]
    assert set(after.skills_normalized) == {"Python", "AWS"}


def test_applying_a_japanese_level_replaces_it():
    resume = make_resume(japanese_level="basic")
    after = apply_actions(resume, [Action(kind="japanese", value="business")])
    assert after.japanese_level == "business"
    assert resume.japanese_level == "basic"


def test_applying_years_replaces_the_number():
    after = apply_actions(make_resume(years_of_experience=1), [Action(kind="years", value=4)])
    assert after.years_of_experience == 4


# ---------------------------------------------------------------------------
# Đếm số tin đủ điều kiện
# ---------------------------------------------------------------------------


def test_qualified_count_uses_the_same_rule_as_the_matching_page():
    """Tin đòi N2, CV mới N4 -> chưa đủ; nâng lên N2 -> đủ."""
    jobs = [make_job(required_japanese="business")]
    before = qualified_job_ids(jobs, make_resume(japanese_level="basic"))
    after = qualified_job_ids(jobs, make_resume(japanese_level="business"))

    assert len(before) == 0
    assert len(after) == 1


def test_qualified_count_needs_no_embedder():
    """`is_qualified` thuần luật; mô phỏng không được phụ thuộc service embedder."""
    jobs = [make_job(required_japanese="business", required_skills=["Python"])]
    resume = make_resume(japanese_level="business", skills_normalized=["python"])
    assert len(qualified_job_ids(jobs, resume)) == 1


# ---------------------------------------------------------------------------
# Tính chất trung tâm: lợi ích KHÔNG cộng được
# ---------------------------------------------------------------------------


def test_deltas_do_not_add_up():
    """Học A mở thêm 1 tin, học B mở thêm 1 tin, học cả hai KHÔNG mở thêm 2 tin.

    Tin dưới đây đòi CẢ tiếng Nhật mức nghiệp vụ LẪN kỹ năng Go. Bù một trong
    hai thứ thì vẫn còn điều kiện loại kia chặn, nên lợi ích lẻ của cả hai đều
    bằng 0; bù cả hai mới mở được tin.

    Đây chính là lý do không thể tính sẵn một bảng "học X được lợi bao nhiêu"
    rồi cộng lại: phải chấm lại với đúng tổ hợp mà người dùng chọn.
    """
    jobs = [make_job(required_japanese="business", required_skills=["Go"])]
    resume = make_resume(japanese_level="basic", skills_normalized=["Python"])

    base = len(qualified_job_ids(jobs, resume))
    only_japanese = len(qualified_job_ids(jobs, apply_actions(resume, [Action("japanese", "business")])))
    only_skill = len(qualified_job_ids(jobs, apply_actions(resume, [Action("skill", "Go")])))
    both = len(qualified_job_ids(jobs, apply_actions(resume, [Action("japanese", "business"), Action("skill", "Go")])))

    assert base == 0
    assert only_japanese - base == 0
    assert only_skill - base == 0
    assert both - base == 1
    assert (both - base) != (only_japanese - base) + (only_skill - base)


# ---------------------------------------------------------------------------
# Sinh phương án
# ---------------------------------------------------------------------------


def test_candidates_never_suggest_a_skill_the_resume_already_has():
    jobs = [make_job(required_skills=["Python", "AWS"]) for _ in range(3)]
    resume = make_resume(skills_normalized=["python"])  # khác hoa thường, vẫn phải nhận ra

    skills = [a.value for a in candidate_actions(jobs, resume) if a.kind == "skill"]
    assert "AWS" in skills
    assert not any(s.lower() == "python" for s in skills)


def test_candidates_offer_the_next_japanese_levels_only():
    jobs = [make_job(required_japanese="native")]
    resume = make_resume(japanese_level="conversational")

    levels = [a.value for a in candidate_actions(jobs, resume) if a.kind == "japanese"]
    assert levels == ["business", "fluent"], "chỉ gợi ý hai bậc kế tiếp, không nhảy cóc lên native"


def test_candidates_for_a_resume_without_japanese_skip_the_none_level():
    """`none` là 'không yêu cầu', gợi ý người ta 'học lên mức không yêu cầu' là vô nghĩa."""
    resume = make_resume(japanese_level=None)
    levels = [a.value for a in candidate_actions([make_job()], resume) if a.kind == "japanese"]
    assert "none" not in levels
    assert levels == ["basic", "conversational"]


# ---------------------------------------------------------------------------
# Kết quả mô phỏng
# ---------------------------------------------------------------------------


def test_simulate_reports_salary_of_the_jobs_it_opens():
    """Không bịa số giờ học; chỉ nói hai điều đo được: mở thêm mấy tin, lương bao nhiêu."""
    jobs = [
        make_job(required_skills=["Go"], salary_min=6_000_000),
        make_job(required_skills=["Go"], salary_min=8_000_000),
        make_job(required_skills=["Python"], salary_min=1_000_000),
    ]
    resume = make_resume(skills_normalized=["Python"])

    outcome = simulate(jobs, resume, [Action("skill", "Go")])

    assert outcome["deltaJobs"] == 2
    assert outcome["openedSalaryMedian"] == 8_000_000
    assert outcome["openedSalarySample"] == 2


def test_simulate_with_no_action_is_the_baseline():
    jobs = [make_job(required_skills=["Go"])]
    resume = make_resume(skills_normalized=["Go"])
    outcome = simulate(jobs, resume, [])
    assert outcome["deltaJobs"] == 0
    assert outcome["qualifiedJobs"] == 1
```

Chạy:
```bash
docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm \
  api-tests python -m pytest tests/test_whatif.py -q
```
Kỳ vọng: **FAIL** — `ModuleNotFoundError: No module named 'app.services.whatif'`.

### Step 4.2 — Cài đặt

File mới `server_python/app/services/whatif.py`:

```python
"""Mô phỏng đối chứng: "nếu CV có thêm X thì mở ra bao nhiêu cơ hội?".

Cách làm: nhân bản CV, sửa đúng một trường, rồi chấm lại TOÀN BỘ kho tin bằng
chính `app/services/matching.evaluate` mà trang gợi ý đang dùng. Không có bộ
luật thứ hai — nếu tách đôi, hai màn hình sẽ nói khác nhau về cùng một CV.

**Vì sao phải chấm lại chứ không tra bảng.** Lợi ích của các phương án không
cộng được: một tin đòi cả tiếng Nhật mức nghiệp vụ lẫn Go thì bù riêng từng thứ
đều không mở được tin nào, bù cả hai mới mở được. `tests/test_whatif.py::
test_deltas_do_not_add_up` pin lại tính chất này.

**Không cần embedder.** `MatchResult.is_qualified` chỉ nhìn các `Gap` có
`blocking=True`, không đụng tới vector — nên mọi lời gọi ở đây truyền
`cosine=None`, và con số trả về vẫn đúng nguyên khi service embedder tắt.

**Chi phí.** Đo trên dữ liệu thật: một lượt quét 430 tin mất ~2ms, 15 phương án
là ~22ms. Đủ rẻ để tính ngay trong request, không cần cache.
"""

from collections import Counter
from dataclasses import dataclass
from typing import Any

from app.models.job import LANGUAGE_LEVELS
from app.models.resume import ResumeMatchView
from app.services.matching import evaluate

# Số kỹ năng đưa vào danh sách gợi ý. Nhiều hơn thì màn hình thành một bảng tra
# cứu, mà người dùng chỉ chọn được vài thứ để học.
SKILL_CANDIDATES = 8

# Số bậc ngôn ngữ gợi ý tiếp theo. Gợi ý nhảy thẳng từ N4 lên N1 là không dùng được.
LEVEL_STEPS = 2

# Các mốc kinh nghiệm để mô phỏng.
YEAR_STEPS = (1, 3)


@dataclass
class Action:
    """Một phương án giả định. `value` là dữ liệu thô, giao diện tự dịch."""

    kind: str  # "skill" | "japanese" | "english" | "years"
    value: Any

    def to_dict(self) -> dict:
        return {"kind": self.kind, "value": self.value}


def apply_actions(resume: ResumeMatchView, actions: list[Action]) -> ResumeMatchView:
    """Bản sao của CV đã áp dụng các phương án. KHÔNG sửa bản gốc."""
    draft = resume.model_copy(deep=True)
    for action in actions:
        if action.kind == "skill":
            draft.skills_normalized = [*(draft.skills_normalized or []), str(action.value)]
        elif action.kind == "japanese":
            draft.japanese_level = str(action.value)
        elif action.kind == "english":
            draft.english_level = str(action.value)
        elif action.kind == "years":
            draft.years_of_experience = int(action.value)
    return draft


def qualified_job_ids(jobs: list, resume: ResumeMatchView) -> set:
    """Id của những tin mà CV này qua được vòng lọc điều kiện.

    `cosine=None`: `is_qualified` không dùng tới phần ngữ nghĩa.
    """
    return {job.id for job in jobs if evaluate(job, resume, None).is_qualified}


def _company_key(job) -> str:
    """Gom theo công ty giống hệt `controllers/match.py` để hai màn hình khớp nhau."""
    return str(job.company) if job.company else f"name:{job.company_name or ''}"


def _median(values: list[int]) -> int | None:
    known = sorted(v for v in values if v is not None)
    return known[len(known) // 2] if known else None


def _next_levels(current: str | None, steps: int = LEVEL_STEPS) -> list[str]:
    """Các bậc ngôn ngữ ngay trên mức hiện tại.

    `none` bị loại: nó nghĩa là "tin không yêu cầu", không phải một bậc để học lên.
    """
    index = LANGUAGE_LEVELS.index(current) if current in LANGUAGE_LEVELS else -1
    return [level for level in LANGUAGE_LEVELS[index + 1 :] if level != "none"][:steps]


def candidate_actions(jobs: list, resume: ResumeMatchView) -> list[Action]:
    """Các phương án đáng cân nhắc, chưa xếp hạng.

    Kỹ năng lấy theo NHU CẦU THẬT của kho tin (kỹ năng được nhiều tin đòi nhất
    mà CV chưa có), không lấy theo từ điển — học một thứ không ai tuyển thì mở
    ra 0 cơ hội.
    """
    have = {s.lower() for s in resume.skills_normalized or []}
    demand: Counter = Counter()
    for job in jobs:
        for skill in job.required_skills or []:
            if skill.lower() not in have:
                demand[skill] += 1

    actions = [Action("skill", skill) for skill, _ in demand.most_common(SKILL_CANDIDATES)]
    actions += [Action("japanese", level) for level in _next_levels(resume.japanese_level)]
    actions += [Action("english", level) for level in _next_levels(resume.english_level, steps=1)]

    current_years = resume.years_of_experience or 0
    actions += [Action("years", current_years + step) for step in YEAR_STEPS]
    return actions


def simulate(jobs: list, resume: ResumeMatchView, actions: list[Action]) -> dict:
    """Kết quả khi áp dụng ĐỒNG THỜI các phương án.

    Trả về cả `openedSalaryMedian` — trung vị lương của đúng những tin vừa mở
    ra, tính trên dữ liệu thật. Đây là thứ thay cho "ước lượng số giờ học": số
    giờ thì không có nguồn đáng tin, còn lương của nhóm tin đó thì đo được.
    """
    by_id = {job.id: job for job in jobs}
    before = qualified_job_ids(jobs, resume)
    after = qualified_job_ids(jobs, apply_actions(resume, actions))
    opened = after - before

    opened_salaries = [by_id[jid].salary_min for jid in opened if by_id[jid].salary_min is not None]

    return {
        "actions": [a.to_dict() for a in actions],
        "qualifiedJobs": len(after),
        "qualifiedCompanies": len({_company_key(by_id[jid]) for jid in after}),
        "deltaJobs": len(after) - len(before),
        "openedSalaryMedian": _median(opened_salaries),
        "openedSalarySample": len(opened_salaries),
    }


def suggestions(jobs: list, resume: ResumeMatchView) -> dict:
    """Toàn bộ dữ liệu cho màn hình: hiện trạng + từng phương án đã xếp hạng."""
    before = qualified_job_ids(jobs, resume)
    by_id = {job.id: job for job in jobs}

    rows = []
    for action in candidate_actions(jobs, resume):
        outcome = simulate(jobs, resume, [action])
        outcome.pop("actions")
        rows.append({**action.to_dict(), **outcome})

    rows.sort(key=lambda r: (-r["deltaJobs"], r["kind"]))
    return {
        "totalJobs": len(jobs),
        "baseline": {
            "qualifiedJobs": len(before),
            "qualifiedCompanies": len({_company_key(by_id[jid]) for jid in before}),
        },
        "suggestions": rows,
    }
```

Chạy lại → kỳ vọng **PASS** (11 test).

### Step 4.3 — Commit

```bash
git add server_python/app/services/whatif.py server_python/tests/test_whatif.py
git commit -m "feat: engine mo phong doi chung, dung lai nguyen bo luat cham diem"
```

---

# Task 5 — Endpoint mô phỏng

### Step 5.1 — Test (phải ĐỎ)

Thêm vào cuối `server_python/tests/test_whatif.py`, và **bổ sung `import pytest` vào đầu file** — nhóm test ở Task 4 chưa dùng tới nên cố ý chưa import (ruff `F401` sẽ báo lỗi nếu import thừa):

```python
# ---------------------------------------------------------------------------
# Qua API thật
# ---------------------------------------------------------------------------


async def test_whatif_requires_authentication(client):
    assert (await client.get("/api/match/whatif")).status_code == 401


async def test_whatif_requires_a_resume(client, user, has_jobs):
    """Không có CV thì không có gì để mô phỏng — phải nói rõ, không trả rỗng."""
    r = await client.get("/api/match/whatif", headers=user.headers)
    assert r.status_code == 404
    assert r.json()["code"] == "match.noResume"


async def test_whatif_lists_suggestions_sorted_by_benefit(client, user_with_resume, has_jobs):
    r = await client.get("/api/match/whatif", headers=user_with_resume.headers)
    assert r.status_code == 200, r.text
    body = r.json()

    assert body["totalJobs"] > 0
    assert "qualifiedJobs" in body["baseline"]
    deltas = [s["deltaJobs"] for s in body["suggestions"]]
    assert deltas == sorted(deltas, reverse=True), "phải xếp giảm dần theo lợi ích"


async def test_whatif_matches_the_qualified_count_of_the_match_page(client, user_with_resume, has_jobs):
    """Hai màn hình phải nói cùng một con số về cùng một CV.

    Nếu lệch nghĩa là mô phỏng đã dùng một bộ luật khác — đúng loại lỗi không ai
    phát hiện cho tới lúc demo.
    """
    whatif = (await client.get("/api/match/whatif", headers=user_with_resume.headers)).json()
    page = (
        await client.get("/api/match/companies", params={"qualifiedOnly": True}, headers=user_with_resume.headers)
    ).json()
    assert whatif["baseline"]["qualifiedCompanies"] == page["totalCompanies"]


async def test_whatif_combination_is_not_the_sum_of_its_parts(client, user_with_resume, has_jobs):
    """Kiểm trên dữ liệu thật đúng tính chất đã pin ở test logic thuần."""
    body = (await client.get("/api/match/whatif", headers=user_with_resume.headers)).json()
    two = [s for s in body["suggestions"] if s["deltaJobs"] > 0][:2]
    if len(two) < 2:
        pytest.skip("CV mẫu không có đủ 2 phương án sinh lợi để so sánh")

    r = await client.post(
        "/api/match/whatif",
        json={"actions": [{"kind": s["kind"], "value": s["value"]} for s in two]},
        headers=user_with_resume.headers,
    )
    assert r.status_code == 200, r.text
    combined = r.json()
    assert combined["sumOfIndividualDeltas"] == sum(s["deltaJobs"] for s in two)
    assert combined["combined"]["deltaJobs"] <= combined["sumOfIndividualDeltas"]


async def test_whatif_rejects_an_unknown_action_kind(client, user_with_resume, has_jobs):
    r = await client.post(
        "/api/match/whatif",
        json={"actions": [{"kind": "salary", "value": 999}]},
        headers=user_with_resume.headers,
    )
    assert r.status_code == 400
    assert r.json()["code"] == "whatif.unknownAction"
```

### Step 5.2 — Mã lỗi mới

`server_python/app/messages.py`:

```python
    "whatif.unknownAction": "Loại phương án không hợp lệ!",
```

Bản dịch, trong `server` của `error.json` (nhóm mới `whatif`) — `vi`:

```json
    "whatif": { "unknownAction": "Loại phương án không hợp lệ!" }
```
`ja`:
```json
    "whatif": { "unknownAction": "シミュレーションの種類が正しくありません。" }
```
`en`:
```json
    "whatif": { "unknownAction": "That simulation option is not valid." }
```

### Step 5.3 — Controller

`server_python/app/controllers/match.py`, thêm import:

```python
from app.services.whatif import Action, simulate, suggestions
```

và hai controller ở cuối file:

```python
VALID_ACTION_KINDS = {"skill", "japanese", "english", "years"}


async def _active_jobs() -> list[JobMatchView]:
    return await Job.find({"is_active": True}, projection_model=JobMatchView).limit(MAX_JOBS_SCORED).to_list()


async def whatif_suggestions(decoded_user: dict):
    """Chức năng 3 — bù chỗ nào thì mở ra nhiều cơ hội nhất.

    Cố ý KHÔNG gọi `job_index.similarities`: số tin đủ điều kiện thuần luật, và
    không phụ thuộc embedder là một tính chất cần giữ chứ không phải chuyện tình cờ.
    """
    resume = await _require_resume(decoded_user)
    return ok(**suggestions(await _active_jobs(), resume))


async def whatif_simulate(decoded_user: dict, raw_actions: list[dict] | None):
    """Áp dụng một tổ hợp phương án do người dùng chọn."""
    resume = await _require_resume(decoded_user)

    actions = []
    for item in raw_actions or []:
        kind = (item or {}).get("kind")
        if kind not in VALID_ACTION_KINDS:
            raise ApiError(400, code="whatif.unknownAction")
        actions.append(Action(kind=kind, value=item.get("value")))

    jobs = await _active_jobs()
    combined = simulate(jobs, resume, actions)

    # Tổng lợi ích lẻ, để giao diện nói được vì sao con số kết hợp nhỏ hơn.
    individual = sum(simulate(jobs, resume, [a])["deltaJobs"] for a in actions)

    return ok(
        baseline={"qualifiedJobs": combined["qualifiedJobs"] - combined["deltaJobs"]},
        combined=combined,
        sumOfIndividualDeltas=individual,
    )
```

### Step 5.4 — Schema + route

`server_python/app/schemas/responses.py`:

```python
class WhatIfSuggestionsResponse(ApiEnvelope):
    totalJobs: int
    baseline: dict[str, Any]
    suggestions: list[dict[str, Any]]


class WhatIfSimulateResponse(ApiEnvelope):
    baseline: dict[str, Any]
    combined: dict[str, Any]
    sumOfIndividualDeltas: int
```

`server_python/app/routes/match.py` — **đặt trước** `/api/match/jobs/{job_id}/gap`
không bắt buộc (đường dẫn không đụng nhau), nhưng để cạnh nhóm match cho dễ đọc:

```python
@router.get("/api/match/whatif", response_model=WhatIfSuggestionsResponse)
async def route_whatif(decoded=Depends(get_current_user)):
    return await whatif_suggestions(decoded)


@router.post("/api/match/whatif", response_model=WhatIfSimulateResponse)
async def route_whatif_simulate(
    actions: list[dict] | None = Body(default=None, embed=True),
    decoded=Depends(get_current_user),
):
    return await whatif_simulate(decoded, actions)
```

Bổ sung vào các dòng import sẵn có: `whatif_simulate, whatif_suggestions` từ
controller, `WhatIfSimulateResponse, WhatIfSuggestionsResponse` từ schema.

### Step 5.5 — Chạy lại

```bash
docker compose restart server
docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm \
  api-tests python -m pytest tests/test_whatif.py -q
```
Kỳ vọng: **PASS** (17 test).

**Kiểm tính chất "không cần embedder":**
```bash
docker compose stop embedder
curl -s -o /dev/null -w "%{http_code}\n" localhost:3000/api/match/whatif -H "Authorization: Bearer $TOKEN"
docker compose start embedder
```
Kỳ vọng: `200`, và `baseline.qualifiedJobs` giống hệt lúc embedder đang bật.

### Step 5.6 — Commit

```bash
git add server_python/app/controllers/match.py server_python/app/routes/match.py \
        server_python/app/schemas/responses.py server_python/app/messages.py \
        server_python/tests/test_whatif.py client/src/i18n/locales
git commit -m "feat: endpoint mo phong doi chung (goi y + to hop)"
```

---

# Task 6 — Màn hình mô phỏng

### Step 6.1 — Khai báo endpoint

`client/src/services/redux/query/api/matchApi.js`, thêm vào `endpoints`:

```js
    getWhatIf: builder.query({
      query: () => 'match/whatif',
      providesTags: ['matches'],
    }),
    simulateWhatIf: builder.mutation({
      query: (actions) => ({
        url: 'match/whatif',
        method: 'POST',
        body: { actions },
      }),
    }),
```

và bổ sung vào phần export:

```js
  useGetWhatIfQuery,
  useSimulateWhatIfMutation,
```

`client/src/services/redux/query/api/jobsApi.js`:

```js
    getJobMarket: builder.query({
      query: () => 'jobs/market',
      providesTags: ['jobs'],
    }),
```
export thêm `useGetJobMarketQuery`.

### Step 6.2 — File dịch

`client/src/i18n/locales/vi/whatif.json`:

```json
{
  "title": "Nếu tôi học thêm thì sao?",
  "intro": "Chọn những thứ bạn định bù, hệ thống chấm lại toàn bộ {{total}} tin tuyển dụng để xem mở ra thêm bao nhiêu cơ hội.",
  "baseline": "Hiện tại bạn qua vòng lọc điều kiện ở {{count}} tin",
  "baseline_one": "Hiện tại bạn qua vòng lọc điều kiện ở {{count}} tin",
  "baseline_other": "Hiện tại bạn qua vòng lọc điều kiện ở {{count}} tin",
  "companies": "thuộc {{count}} công ty",
  "companies_one": "thuộc {{count}} công ty",
  "companies_other": "thuộc {{count}} công ty",
  "opens": "+{{count}} tin",
  "opens_one": "+{{count}} tin",
  "opens_other": "+{{count}} tin",
  "noBenefit": "Không mở thêm tin nào",
  "openedSalary": "Trung vị lương của nhóm tin mở thêm: {{salary}} (tính trên {{sample}} tin có ghi lương)",
  "openedSalaryUnknown": "Nhóm tin mở thêm chưa đủ dữ liệu lương để tính",
  "action": {
    "skill": "Học {{value}}",
    "japanese": "Nâng tiếng Nhật lên mức {{value}}",
    "english": "Nâng tiếng Anh lên mức {{value}}",
    "years": "Có {{value}} năm kinh nghiệm"
  },
  "combined": {
    "title": "Nếu làm tất cả những điều đã chọn",
    "result": "Bạn sẽ qua vòng lọc ở {{count}} tin",
    "result_one": "Bạn sẽ qua vòng lọc ở {{count}} tin",
    "result_other": "Bạn sẽ qua vòng lọc ở {{count}} tin",
    "notAdditive": "Cộng riêng từng mục sẽ ra {{sum}} tin — con số thật thấp hơn vì nhiều tin đòi cùng lúc nhiều điều kiện, bù một thứ vẫn còn thứ kia chặn.",
    "empty": "Chọn ít nhất một mục ở trên để xem kết quả kết hợp."
  },
  "disclaimer": "Đây là số tin bạn qua được VÒNG LỌC ĐIỀU KIỆN, không phải số tin chắc chắn trúng tuyển.",
  "needResume": "Bạn cần tạo CV trước khi dùng chức năng này."
}
```

`ja` (bản dịch tương ứng, giữ nguyên mọi tên tham số):

```json
{
  "title": "スキルを追加したらどうなる？",
  "intro": "身につけたい項目を選ぶと、{{total}}件の求人すべてを採点し直して、応募できる求人がどれだけ増えるかを表示します。",
  "baseline_one": "現在、条件を満たす求人は{{count}}件です",
  "baseline_other": "現在、条件を満たす求人は{{count}}件です",
  "companies_one": "{{count}}社の求人です",
  "companies_other": "{{count}}社の求人です",
  "opens_one": "+{{count}}件",
  "opens_other": "+{{count}}件",
  "noBenefit": "増える求人はありません",
  "openedSalary": "新たに応募できる求人の年収中央値：{{salary}}（年収の記載がある{{sample}}件で算出）",
  "openedSalaryUnknown": "新たに応募できる求人は年収データが足りず算出できません",
  "action": {
    "skill": "{{value}}を習得する",
    "japanese": "日本語を{{value}}まで上げる",
    "english": "英語を{{value}}まで上げる",
    "years": "実務経験{{value}}年を積む"
  },
  "combined": {
    "title": "選んだ項目をすべて達成した場合",
    "result_one": "条件を満たす求人は{{count}}件になります",
    "result_other": "条件を満たす求人は{{count}}件になります",
    "notAdditive": "個別の増加分を足すと{{sum}}件になりますが、実際はそれより少なくなります。複数の条件を同時に求める求人では、片方だけ満たしても、もう片方が条件として残るためです。",
    "empty": "上の項目を1つ以上選ぶと、組み合わせた結果が表示されます。"
  },
  "disclaimer": "これは「応募条件を満たす求人の件数」であり、必ず採用される件数ではありません。",
  "needResume": "この機能を使うには、まず履歴書を作成してください。"
}
```

`en`:

```json
{
  "title": "What if I learned more?",
  "intro": "Pick what you plan to add and we re-score all {{total}} job posts to see how many more open up.",
  "baseline_one": "You currently clear the requirements on {{count}} job",
  "baseline_other": "You currently clear the requirements on {{count}} jobs",
  "companies_one": "at {{count}} company",
  "companies_other": "at {{count}} companies",
  "opens_one": "+{{count}} job",
  "opens_other": "+{{count}} jobs",
  "noBenefit": "Opens no new jobs",
  "openedSalary": "Median salary of the newly opened jobs: {{salary}} (from {{sample}} jobs that state a salary)",
  "openedSalaryUnknown": "Not enough salary data on the newly opened jobs",
  "action": {
    "skill": "Learn {{value}}",
    "japanese": "Reach {{value}} Japanese",
    "english": "Reach {{value}} English",
    "years": "Reach {{value}} years of experience"
  },
  "combined": {
    "title": "If you did everything you selected",
    "result_one": "You would clear the requirements on {{count}} job",
    "result_other": "You would clear the requirements on {{count}} jobs",
    "notAdditive": "Adding the individual gains gives {{sum}} — the real number is lower, because many posts demand several requirements at once, so closing one still leaves the other blocking you.",
    "empty": "Select at least one item above to see the combined result."
  },
  "disclaimer": "This is how many posts you CLEAR THE REQUIREMENTS for — not how many you would be hired for.",
  "needResume": "Create a CV first to use this feature."
}
```

> `baseline`/`companies`/`opens`/`combined.result` là khoá có `{{count}}` nên
> **bắt buộc** có đủ `_one`/`_other`; `scripts/check-i18n.mjs` sẽ báo lỗi nếu thiếu.

Thêm 2 mục menu vào `nav.json` của cả ba ngôn ngữ:

| khoá | vi | ja | en |
|---|---|---|---|
| `whatif` | Nếu tôi học thêm | スキルを追加したら | What if |
| `market` | Bản đồ thị trường | 求人market | Market map |

### Step 6.3 — Màn hình

File mới `client/src/layouts/home/Match/WhatIfLayout.jsx`:

```jsx
import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Page from '../../Page';
import {
  useGetWhatIfQuery,
  useSimulateWhatIfMutation,
} from '../../../services/redux/query/api/matchApi';
import { formatSalary } from '../../../services/utils/jobFormat';

// Khoá nhận diện một phương án. Dùng cả cho `key` của React lẫn cho tập đã chọn.
const actionKey = (a) => `${a.kind}:${a.value}`;

function WhatIfLayout() {
  const { t } = useTranslation(['whatif', 'job', 'common']);
  const { data, isSuccess, isError } = useGetWhatIfQuery();
  const [simulate, { data: combined }] = useSimulateWhatIfMutation();
  const [selected, setSelected] = useState([]);

  const toggle = (action) => {
    const key = actionKey(action);
    const next = selected.some((a) => actionKey(a) === key)
      ? selected.filter((a) => actionKey(a) !== key)
      : [...selected, { kind: action.kind, value: action.value }];
    setSelected(next);
    if (next.length) simulate(next);
  };

  const rows = useMemo(
    () =>
      (data?.suggestions || []).map((s) => {
        const chosen = selected.some((a) => actionKey(a) === actionKey(s));
        return (
          <li key={actionKey(s)}>
            <button
              type='button'
              data-testid='whatif-option'
              aria-pressed={chosen}
              onClick={() => toggle(s)}
              className={`w-full text-left px-4 py-3 rounded-lg border transition-colors ${
                chosen
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-950'
                  : 'border-neutral-300 dark:border-neutral-700'
              }`}
            >
              <span className='font-bold'>
                {t(`action.${s.kind}`, {
                  value:
                    s.kind === 'japanese' || s.kind === 'english'
                      ? t(`job:level.${s.value}`, { defaultValue: s.value })
                      : s.value,
                })}
              </span>
              <span className='ml-2' data-testid='whatif-delta'>
                {s.deltaJobs > 0 ? t('opens', { count: s.deltaJobs }) : t('noBenefit')}
              </span>
              <span className='block text-sm text-neutral-500'>
                {s.openedSalaryMedian
                  ? t('openedSalary', {
                      salary: formatSalary(t, s.openedSalaryMedian, s.openedSalaryMedian),
                      sample: s.openedSalarySample,
                    })
                  : t('openedSalaryUnknown')}
              </span>
            </button>
          </li>
        );
      }),
    // `t` trong mảng phụ thuộc: đổi ngôn ngữ -> `t` mới -> danh sách phải dựng lại.
    [data, selected, t]
  );

  if (isError) {
    return (
      <Page>
        <p className='p-4'>{t('needResume')}</p>
      </Page>
    );
  }

  return (
    <Page>
      <div className='border border-neutral-300 dark:border-neutral-700 rounded-lg p-4 flex flex-col gap-6'>
        <div className='flex flex-col gap-2'>
          <h1 className='text-xl md:text-2xl font-bold'>{t('title')}</h1>
          {isSuccess && (
            <>
              <p>{t('intro', { total: data.totalJobs })}</p>
              <p className='font-bold' data-testid='whatif-baseline'>
                {t('baseline', { count: data.baseline.qualifiedJobs })}{' '}
                {t('companies', { count: data.baseline.qualifiedCompanies })}
              </p>
            </>
          )}
        </div>

        <ul className='flex flex-col gap-2'>{rows}</ul>

        <section className='border-t border-neutral-300 dark:border-neutral-700 pt-4'>
          <h2 className='text-lg font-bold'>{t('combined.title')}</h2>
          {selected.length === 0 && <p>{t('combined.empty')}</p>}
          {selected.length > 0 && combined && (
            <>
              <p className='font-bold' data-testid='whatif-combined'>
                {t('combined.result', { count: combined.combined.qualifiedJobs })}
              </p>
              {combined.sumOfIndividualDeltas !== combined.combined.deltaJobs && (
                <p className='text-sm text-neutral-500'>
                  {t('combined.notAdditive', {
                    sum: combined.baseline.qualifiedJobs + combined.sumOfIndividualDeltas,
                  })}
                </p>
              )}
            </>
          )}
        </section>

        <p className='text-sm text-neutral-500'>{t('disclaimer')}</p>
      </div>
    </Page>
  );
}

export default WhatIfLayout;
```

### Step 6.4 — Route + menu

`client/src/services/router/router.jsx` — thêm vào `children` của `match`:

```jsx
          {
            path: 'whatif',
            element: (
              <ProtectedRoute>
                <WhatIfLayout />
              </ProtectedRoute>
            ),
          },
```

và khai báo lazy ở đầu file:

```jsx
const WhatIfLayout = lazy(() => import('../../layouts/home/Match/WhatIfLayout'));
```

`client/src/layouts/components/LeftAside.jsx` — thêm mục menu trỏ tới
`/match/whatif` với nhãn `t('nav:whatif')`, đặt ngay sau mục `match`.

### Step 6.5 — Kiểm

```bash
cd client && npm run lint && npm run build
```
Kỳ vọng: `0 errors`, `✓ 3 ngôn ngữ (en, ja, vi) · 14 namespace · ... khớp nhau hoàn toàn`, `✓ built`.

Mở http://localhost:5173/match/whatif bằng tài khoản `demo@fuurin.local`:
- danh sách phương án xếp giảm dần theo số tin mở thêm;
- tick 2 ô → phần "kết hợp" hiện số nhỏ hơn tổng, kèm câu giải thích;
- đổi `JA / VI / EN` → toàn bộ đổi theo, không tải lại trang.

### Step 6.6 — Commit

```bash
git add client/src
git commit -m "feat: man hinh mo phong doi chung"
```

---

# Task 7 — Màn hình bản đồ thị trường

### Step 7.1 — Biểu đồ cột dùng chung

File mới `client/src/components/ui/BarChart.jsx`:

```jsx
/**
 * Biểu đồ cột ngang bằng SVG thuần.
 *
 * Không thêm thư viện chart cho ba biểu đồ đơn giản: 200KB dependency cho thứ
 * vẽ được bằng vài chục dòng là không đáng, và thư viện chart là loại phụ thuộc
 * mục nhanh nhất.
 *
 * `rows`: [{ label, value, caption }]
 */
function BarChart({ rows, emptyLabel }) {
  if (!rows?.length) return <p>{emptyLabel}</p>;
  const max = Math.max(...rows.map((r) => r.value), 1);

  return (
    <ul className='flex flex-col gap-2'>
      {rows.map((r) => (
        <li key={r.label} className='flex items-center gap-3'>
          <span className='w-32 shrink-0 truncate text-sm'>{r.label}</span>
          <span className='flex-1 h-5 bg-neutral-200 dark:bg-neutral-700 rounded overflow-hidden'>
            <span
              className='block h-full bg-blue-500'
              style={{ width: `${(r.value / max) * 100}%` }}
            />
          </span>
          <span className='w-40 shrink-0 text-sm text-right'>{r.caption}</span>
        </li>
      ))}
    </ul>
  );
}

export default BarChart;
```

### Step 7.2 — File dịch `market.json` (3 ngôn ngữ)

`vi`:

```json
{
  "title": "Bản đồ thị trường việc làm",
  "intro": "Tổng hợp trên {{total}} tin tuyển dụng đang hoạt động.",
  "skills": { "title": "Kỹ năng được săn nhiều nhất", "other": "Các kỹ năng lẻ khác" },
  "japanese": { "title": "Yêu cầu tiếng Nhật", "unstated": "Tin không ghi rõ" },
  "prefectures": { "title": "Nơi làm việc" },
  "jobs": "{{count}} tin",
  "jobs_one": "{{count}} tin",
  "jobs_other": "{{count}} tin",
  "median": "trung vị {{salary}} · n={{sample}}",
  "medianUnknown": "chưa đủ dữ liệu lương (n={{sample}})",
  "caveat": "Chỉ hiện trung vị lương khi nhóm có từ {{min}} tin ghi lương trở lên — dưới ngưỡng đó con số là giai thoại, không phải số liệu.",
  "finding": "Tiếng Nhật mở ra SỐ LƯỢNG cơ hội; MỨC LƯƠNG lại do kỹ năng quyết định. Trong kho tin này, nhóm đòi tiếng Nhật cao phần lớn là giảng dạy và dịch vụ, không phải kỹ thuật.",
  "empty": "Chưa có dữ liệu việc làm. Chạy ETL trước."
}
```

`ja`:

```json
{
  "title": "求人market",
  "intro": "掲載中の求人{{total}}件を集計しています。",
  "skills": { "title": "需要の高いスキル", "other": "その他のスキル" },
  "japanese": { "title": "日本語の要件", "unstated": "記載なし" },
  "prefectures": { "title": "勤務地" },
  "jobs_one": "{{count}}件",
  "jobs_other": "{{count}}件",
  "median": "中央値 {{salary}}・n={{sample}}",
  "medianUnknown": "年収データが不足しています（n={{sample}}）",
  "caveat": "年収の中央値は、年収の記載が{{min}}件以上あるグループにのみ表示します。それ未満の数値は統計として扱えないためです。",
  "finding": "日本語力は応募できる求人の「件数」を増やしますが、「年収」を決めるのはスキルです。このデータでは、高い日本語力を求める求人の多くは教育やサービス職であり、技術職ではありません。",
  "empty": "求人データがありません。先にETLを実行してください。"
}
```

`en`:

```json
{
  "title": "Job market map",
  "intro": "Aggregated over {{total}} active job posts.",
  "skills": { "title": "Most in-demand skills", "other": "Other individual skills" },
  "japanese": { "title": "Japanese requirement", "unstated": "Not stated" },
  "prefectures": { "title": "Work location" },
  "jobs_one": "{{count}} job",
  "jobs_other": "{{count}} jobs",
  "median": "median {{salary}} · n={{sample}}",
  "medianUnknown": "not enough salary data (n={{sample}})",
  "caveat": "A median salary is shown only for groups with at least {{min}} posts that state a salary — below that the number is an anecdote, not a statistic.",
  "finding": "Japanese opens up the NUMBER of opportunities; SALARY is driven by skills. In this dataset, posts demanding high Japanese are mostly teaching and service roles rather than engineering.",
  "empty": "No job data yet. Run the ETL first."
}
```

### Step 7.3 — Màn hình

File mới `client/src/layouts/home/Market/MarketLayout.jsx`:

```jsx
import { useTranslation } from 'react-i18next';
import Page from '../../Page';
import BarChart from '../../../components/ui/BarChart';
import { useGetJobMarketQuery } from '../../../services/redux/query/api/jobsApi';
import { formatSalary } from '../../../services/utils/jobFormat';

function MarketLayout() {
  const { t } = useTranslation(['market', 'job', 'common']);
  const { data, isSuccess } = useGetJobMarketQuery();

  // Trung vị chỉ hiện khi nhóm đủ lớn — backend đã trả `null` dưới ngưỡng,
  // ở đây chỉ diễn đạt lại cho đúng.
  const caption = (row) =>
    `${t('jobs', { count: row.jobs })} · ${
      row.salaryMedian
        ? t('median', {
            salary: formatSalary(t, row.salaryMedian, row.salaryMedian),
            sample: row.salarySample,
          })
        : t('medianUnknown', { sample: row.salarySample })
    }`;

  if (!isSuccess) return <Page><p className='p-4'>{t('empty')}</p></Page>;

  return (
    <Page>
      <div className='border border-neutral-300 dark:border-neutral-700 rounded-lg p-4 flex flex-col gap-8'>
        <div className='flex flex-col gap-2'>
          <h1 className='text-xl md:text-2xl font-bold'>{t('title')}</h1>
          <p>{t('intro', { total: data.totalJobs })}</p>
          <p className='text-sm text-neutral-500'>{t('caveat', { min: data.minGroupSize })}</p>
        </div>

        <section className='flex flex-col gap-3'>
          <h2 className='text-lg font-bold'>{t('skills.title')}</h2>
          <BarChart
            emptyLabel={t('empty')}
            rows={data.skills.map((s) => ({
              label: s.skill === '__other__' ? t('skills.other') : s.skill,
              value: s.jobs,
              caption: caption(s),
            }))}
          />
        </section>

        <section className='flex flex-col gap-3'>
          <h2 className='text-lg font-bold'>{t('japanese.title')}</h2>
          <BarChart
            emptyLabel={t('empty')}
            rows={data.japanese.map((r) => ({
              label: r.level ? t(`job:level.${r.level}`, { defaultValue: r.level }) : t('japanese.unstated'),
              value: r.jobs,
              caption: caption(r),
            }))}
          />
          <p className='text-sm'>{t('finding')}</p>
        </section>

        <section className='flex flex-col gap-3'>
          <h2 className='text-lg font-bold'>{t('prefectures.title')}</h2>
          <BarChart
            emptyLabel={t('empty')}
            rows={data.prefectures.map((r) => ({
              label: r.prefecture,
              value: r.jobs,
              caption: caption(r),
            }))}
          />
        </section>
      </div>
    </Page>
  );
}

export default MarketLayout;
```

### Step 7.4 — Route + menu + kiểm

Thêm route `/market` và mục menu `t('nav:market')` giống Step 6.4.

```bash
cd client && npm run lint && npm run build
```
Kỳ vọng: `0 errors`, `✓ 3 ngôn ngữ (en, ja, vi) · 14 namespace ... khớp nhau hoàn toàn`.

### Step 7.5 — Commit

```bash
git add client/src
git commit -m "feat: man hinh ban do thi truong viec lam, bieu do SVG thuan"
```

---

# Task 8 — E2E, tài liệu, kiểm chứng cuối

### Step 8.1 — E2E

Thêm vào `e2e/test_e2e.py`:

```python
def test_whatif_recalculates_when_an_option_is_picked(page_with_console, api, tr):
    """Tick một phương án -> con số kết hợp phải xuất hiện.

    Chọn selector theo `data-testid` chứ không theo câu chữ: test này phải sống
    được ở cả ba ngôn ngữ.
    """
    page = page_with_console
    login_as_demo_user(page)
    page.goto(f"{APP_URL}/match/whatif")

    page.wait_for_selector("[data-testid='whatif-baseline']")
    options = page.locator("[data-testid='whatif-option']")
    assert options.count() > 0, "không có phương án nào để mô phỏng"

    options.first.click()
    page.wait_for_selector("[data-testid='whatif-combined']")
    assert page.locator("[data-testid='whatif-combined']").inner_text().strip()


def test_market_page_shows_the_sample_size_next_to_every_median(page_with_console, tr):
    """Không được có trung vị nào đứng một mình — cỡ mẫu luôn đi kèm."""
    page = page_with_console
    login_as_demo_user(page)
    page.goto(f"{APP_URL}/market")

    page.wait_for_selector("h1")
    body = page.inner_text("body")
    assert "n=" in body, "trang thống kê không hiện cỡ mẫu"
```

> Dùng lại đúng fixture và helper đang có trong `e2e/conftest.py`
> (`page_with_console`, `tr`, `APP_URL`). Nếu chưa có helper đăng nhập bằng tài
> khoản demo thì thêm một hàm nhỏ dùng lại luồng đăng nhập của các test sẵn có.

```bash
docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm e2e-tests
docker compose up -d client
```
Kỳ vọng: **14 passed**.

### Step 8.2 — Tài liệu

File mới `docs/10-mo-phong-doi-chung.md`, viết cho người chưa quen lập trình, gồm:

1. Chức năng này trả lời câu hỏi gì
2. Số tin "đủ điều kiện" nghĩa là gì (và **không** nghĩa là gì)
3. Vì sao lợi ích không cộng được — kèm ví dụ tin đòi cả N2 lẫn Go
4. Vì sao không có "số giờ học" — và cái gì được hiển thị thay thế
5. Vì sao trung vị lương luôn kèm `n`, và phát hiện "tiếng Nhật ≠ lương cao"
6. Thêm một loại phương án mới thì sửa ở đâu (`whatif.py` → `Action.kind`, file dịch `whatif.json`)

Cập nhật `docs/README.md`: thêm dòng thứ 10 vào bảng mục lục, cập nhật bảng "Con
số của dự án" (endpoint 60 → 63, trang 18 → 20, test API 291 → 316, E2E 12 → 14).

Cập nhật `README.md`: thêm mục 1.4 hai dòng chức năng mới, và mục 5 hai bước sử dụng.

### Step 8.3 — Kiểm chứng cuối

```bash
# 1. Lint
ruff check server_python/app server_python/scripts server_python/tests embedder e2e \
  --config server_python/pyproject.toml
ruff format --check server_python/app server_python/scripts server_python/tests embedder e2e \
  --config server_python/pyproject.toml
cd client && npm run lint && cd ..

# 2. Toàn bộ test API
docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm api-tests

# 3. E2E
docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm e2e-tests
docker compose up -d client

# 4. Không phụ thuộc embedder
docker compose stop embedder
curl -s localhost:3000/api/match/whatif -H "Authorization: Bearer $TOKEN" | python3 -c "import json,sys; print(json.load(sys.stdin)['baseline'])"
docker compose start embedder

# 5. Clone sạch sang đường dẫn khác rồi dựng lại
rsync -a --exclude .git --exclude node_modules . /tmp/fuurin-clone/
cd /tmp/fuurin-clone && docker compose up -d --build && docker compose ps
```

| Kiểm | Kỳ vọng |
|---|---|
| ruff | `All checks passed!` |
| npm run lint | `0 errors`, ≤ 37 warnings, bản dịch khớp |
| Test API | **316 passed** |
| E2E | **14 passed** |
| Tắt embedder | `/api/match/whatif` vẫn 200, `baseline` **không đổi** |
| Clone sạch | 5 container healthy |

### Step 8.4 — Commit

```bash
git add e2e docs README.md
git commit -m "test: E2E cho mo phong doi chung; docs: bai 10 va cap nhat so lieu"
```

---

## Bảng tự kiểm trước khi coi là xong

- [ ] `matching.py` **không bị sửa một dòng nào** (`git diff --stat` không có file này)
- [ ] Không có chuỗi hiển thị nào viết thẳng vào JSX (ESLint 0 error)
- [ ] Mọi `ApiError` / `ok(message=)` / `Notification` mới đều có `code=`
- [ ] Mọi mã mới có bản dịch đủ 3 ngôn ngữ, tham số `{x}` ↔ `{{x}}` khớp
- [ ] Mọi khoá có `{{count}}` đều có `_one` và `_other`
- [ ] Mọi trung vị hiển thị đều kèm `n`
- [ ] Không có số giờ học nào bịa ra cho kỹ năng
- [ ] Tắt embedder, `baseline.qualifiedJobs` không đổi
- [ ] `baseline.qualifiedCompanies` khớp `totalCompanies` của `/api/match/companies?qualifiedOnly=true`
- [ ] 221 thông báo cũ vẫn hiển thị được, không migrate
