# 9. Đa ngôn ngữ (Nhật · Việt · Anh)

> Tài liệu này viết cho người chưa quen lập trình web. Mọi khái niệm đều được
> giải thích trước khi dùng.

Giao diện Fuurin nói được ba thứ tiếng: **日本語 (Nhật)**, **Tiếng Việt**,
**English**. Người dùng bấm ba nút `JA / VI / EN` ở góc phải thanh trên cùng.

Mặc định là **tiếng Nhật**, vì đây là sản phẩm cho thị trường việc làm Nhật Bản.

---

## 9.1. Trước khi bắt đầu: bốn khái niệm

> 💡 **i18n là gì?**
> Viết tắt của *internationalization* — chữ `i`, 18 chữ cái ở giữa, rồi chữ `n`.
> Nghĩa là: làm cho phần mềm hiển thị được nhiều ngôn ngữ mà **không phải viết
> lại code**. Mỗi câu chữ được lấy ra khỏi code, cất vào một cuốn từ điển riêng.

> 💡 **Khoá (key) là gì?**
> Thay vì viết thẳng chữ `"Đăng nhập"` vào code, ta viết một cái tên đại diện:
> `auth.login.title`. Cái tên đó gọi là **khoá**. Từ điển sẽ nói khoá đó ứng với
> chữ gì trong từng ngôn ngữ:
>
> | khoá | 日本語 | Tiếng Việt | English |
> |---|---|---|---|
> | `auth.login.title` | ログイン | Đăng nhập | Login |
>
> Code chỉ nói *"cho tôi khoá `auth.login.title`"*, không quan tâm người dùng
> đang xem ngôn ngữ nào.

> 💡 **Namespace là gì?**
> Là cách chia cuốn từ điển thành nhiều chương cho dễ tìm. Dự án có 12 chương:
> `common` (nút bấm dùng chung), `auth` (đăng nhập), `post` (bài viết),
> `job` (việc làm)… Khoá đầy đủ gồm cả tên chương: `auth:login.title`.

> 💡 **Tham số (placeholder) là gì?**
> Có câu cần chèn con số hoặc tên vào giữa. Chỗ để chèn viết là `{{...}}`:
>
> ```
> ja:  ファイルサイズが{{max}}MBを超えています。
> vi:  File vượt quá {{max}}MB.
> ```
>
> Khi hiển thị, `{{max}}` được thay bằng giá trị thật (ví dụ `5`). Quan trọng:
> **không được ghép sẵn con số vào câu rồi mới dịch** — vì mỗi ngôn ngữ đặt con
> số ở vị trí khác nhau trong câu.

---

## 9.2. Bản đồ: chữ trong ứng dụng đến từ đâu

Chữ hiển thị trên màn hình đến từ **ba nguồn khác nhau**, và ba nguồn này hỏng
độc lập với nhau — biết phân biệt là biết phải sửa ở đâu:

```
① Chữ cố định trên giao diện          ② Thông báo do máy chủ sinh ra
   "Đăng nhập", "Lưu", "Tìm kiếm"        "Địa chỉ email đã tồn tại!"
            │                                      │
            │                          máy chủ gửi MÃ: auth.emailExists
            │                                      │
            ▼                                      ▼
   client/src/i18n/locales/            client/src/i18n/locales/
     <ngôn ngữ>/nav.json                 <ngôn ngữ>/error.json
     <ngôn ngữ>/auth.json                  ("server" → "auth" → "emailExists")
            │                                      │
            └──────────────┬───────────────────────┘
                           ▼
                    Hiện trên màn hình

③ Nội dung do người dùng và trang tuyển dụng tạo ra
   Bài viết, bình luận, tên công ty, mô tả công việc
            │
            ▼
   KHÔNG dịch — đó là dữ liệu thật, không phải giao diện
```

**Nguồn ② là chỗ dễ quên nhất.** Phần lớn thông báo dạng "bong bóng" (toast) mà
người dùng thấy đều do máy chủ quyết định câu chữ. Dịch xong 100% giao diện mà
quên phần này thì giao diện tiếng Nhật vẫn hiện toast tiếng Việt.

---

## 9.3. Các file liên quan

```
client/
├── vite-plugin-i18n-resources.js   gom 36 file dịch thành 1 module
├── vite.config.js                  bật plugin trên
├── scripts/check-i18n.mjs          kiểm 3 ngôn ngữ có khớp nhau không
└── src/
    ├── i18n/
    │   ├── config.js               khởi tạo, ngôn ngữ mặc định, bộ định dạng
    │   ├── resources.js            nạp toàn bộ bản dịch
    │   ├── dateLocale.js           chọn locale cho ngày tháng
    │   └── locales/
    │       ├── ja/  (12 file .json)
    │       ├── vi/  (12 file .json)
    │       └── en/  (12 file .json)
    ├── components/common/LanguageSwitcher.jsx   ba nút JA / VI / EN
    ├── hooks/useMutationToast.jsx               dịch toast của server
    ├── services/utils/serverMessage.js          mã → câu, dùng chung 4 nơi
    ├── services/utils/jobFormat.js              lương, trình độ tiếng Nhật
    └── services/utils/matchText.js              phần "còn thiếu gì"

server_python/
├── app/messages.py                 danh mục 70 mã thông báo
└── tests/test_message_codes.py     ràng buộc mã ↔ bản dịch
```

---

## 9.4. Thêm một câu chữ mới — hướng dẫn từng bước

Giả sử bạn thêm nút **"Xuất file Excel"** vào trang việc làm.

### Bước 1 — Chọn khoá và namespace

Nút nằm ở trang việc làm → namespace `job`. Đặt tên khoá theo *ý nghĩa*, không
theo *chữ hiển thị*:

```
job:actions.exportExcel          ✅ đúng
job:xuatFileExcel                ❌ sai — đổi chữ là khoá thành vô nghĩa
```

### Bước 2 — Thêm vào **cả ba** file

`client/src/i18n/locales/ja/job.json`:

```json
{
  "actions": { "exportExcel": "Excelで出力" }
}
```

`client/src/i18n/locales/vi/job.json`:

```json
{
  "actions": { "exportExcel": "Xuất file Excel" }
}
```

`client/src/i18n/locales/en/job.json`:

```json
{
  "actions": { "exportExcel": "Export to Excel" }
}
```

> ⚠️ Thiếu một ngôn ngữ **không làm hỏng gì cả** — chỗ đó sẽ lặng lẽ hiện tiếng
> Nhật. Đó chính là lý do có `scripts/check-i18n.mjs` ở bước 4.

### Bước 3 — Dùng trong component

```jsx
import { useTranslation } from 'react-i18next';

function ExportButton() {
  const { t } = useTranslation('job');       // ← chọn chương của từ điển
  return <button>{t('actions.exportExcel')}</button>;
}
```

Cần nhiều chương cùng lúc thì truyền mảng, và ghi rõ chương ở trước dấu `:`:

```jsx
const { t } = useTranslation(['job', 'common']);
// t('actions.exportExcel')      -> chương 'job' (chương đầu là mặc định)
// t('common:actions.cancel')    -> chương 'common'
```

### Bước 4 — Kiểm tra

```bash
cd client && npm run lint
```

Lệnh này chạy hai thứ:

```
✖ 37 problems (0 errors, 37 warnings)
✓ 3 ngôn ngữ (en, ja, vi) · 12 namespace · 459 khoá — khớp nhau hoàn toàn
```

Nếu bạn quên tiếng Anh, nó nói thẳng:

```
✗ 1 vấn đề trong file dịch:
  [en] job: thiếu khoá "actions.exportExcel"
```

---

## 9.5. Thông báo từ máy chủ: cơ chế "mã + câu dự phòng"

### Vấn đề

Backend viết bằng Python, có 55 chỗ báo lỗi và 27 chỗ báo thành công, tất cả
bằng tiếng Việt. Client hiển thị thẳng câu đó lên toast.

Nếu để backend tự dịch, backend phải giữ ba bản dịch trong Python và phải biết
người dùng đang xem ngôn ngữ nào — tức là **hai nơi cùng giữ bản dịch**, chắc
chắn sẽ lệch nhau.

### Cách làm

Backend **không dịch**. Nó gửi kèm một **mã ổn định**:

```python
# server_python/app/controllers/auth.py
raise ApiError(409, code="auth.emailExists")
```

Response trả về:

```json
{
  "error": true,
  "success": false,
  "message": "Địa chỉ email đã tồn tại!",
  "code": "auth.emailExists"
}
```

Client dịch theo `code` (`client/src/hooks/useMutationToast.jsx`), theo đúng
thứ tự ưu tiên này:

| Ưu tiên | Nguồn | Khi nào dùng |
|---|---|---|
| 1 | bản dịch của `code` | bình thường — đúng ngôn ngữ người dùng chọn |
| 2 | `message` của server | mã chưa có bản dịch |
| 3 | câu dự phòng cố định | mất mạng, không có phản hồi nào để đọc |

Thứ tự này quan trọng:

- Bỏ bước 2 → thêm một mã mới mà quên dịch, người dùng thấy khoá thô
  `server.post.xyz`. Xấu và khó hiểu.
- Bỏ bước 3 → mất mạng thì toast rỗng, người dùng bấm nút mà không thấy gì.

### Có tham số thì sao

```python
raise ApiError(413, code="upload.tooLarge", params={"max": 5})
```

```json
{ "message": "File vượt quá 5MB.", "code": "upload.tooLarge", "params": {"max": 5} }
```

Client ghép `params` vào bản dịch của mình:

```
ja:  ファイルサイズが5MBを超えています。
en:  File exceeds 5MB.
```

> ⚠️ **Đừng bao giờ ghép sẵn giá trị vào chuỗi rồi mới gửi đi.** Gửi
> `"File vượt quá 5MB."` mà không kèm `params` thì client hết đường dịch.

### Danh mục mã ở đâu

`server_python/app/messages.py` — 70 mã, mỗi mã một câu tiếng Việt:

```python
MESSAGES = {
    "auth.emailExists": "Địa chỉ email đã tồn tại!",
    "upload.tooLarge": "File vượt quá {max}MB.",
    ...
}
```

Gõ nhầm mã thì `message_for()` **ném lỗi ngay**, không lặng lẽ trả chuỗi rỗng.
Đây là lựa chọn có chủ đích: lỗi lập trình phải nổ lúc chạy test, không được
biến thành một toast trống lúc demo.

---

## 9.6. Phần "tôi còn thiếu gì" — dữ liệu thô, không phải chữ

Đây là phần tinh tế nhất. Xem thêm [tài liệu 7](07-embedding-va-goi-y.md).

Khi so CV với tin tuyển dụng, backend sinh ra những câu như:

> *Cần Tiếng Nhật mức Nghiệp vụ (N2), CV đang ở mức Giao tiếp (N3)*

Câu này có **ba phần thay đổi được**: tên ngôn ngữ, trình độ yêu cầu, trình độ
hiện có. Nếu backend gửi đi câu đã ghép sẵn thì giao diện tiếng Nhật hết cách.

Nên backend gửi **dữ liệu thô**:

```json
{
  "kind": "japanese_level",
  "code": "gap.language.below",
  "params": { "language": "japanese",
              "requiredLevel": "business",
              "currentLevel": "conversational" },
  "message": "Cần Tiếng Nhật mức Nghiệp vụ (N2), CV đang ở mức Giao tiếp (N3)",
  "blocking": true
}
```

`"business"` là **mã**, không phải chữ hiển thị. Client mới đổi mã thành nhãn:

| mã | 日本語 | Tiếng Việt | English |
|---|---|---|---|
| `business` | ビジネス（N2） | Nghiệp vụ (N2) | Business (N2) |

Việc đổi mã → nhãn do một **bộ định dạng** (formatter) trong
`client/src/i18n/config.js` lo, viết trong câu dịch là `{{requiredLevel, level}}`:

```
ja: {{language, lang}}が{{requiredLevel, level}}レベル必要ですが、履歴書は{{currentLevel, level}}です
vi: Cần {{language, lang}} mức {{requiredLevel, level}}, CV đang ở mức {{currentLevel, level}}
```

Dự án có ba bộ định dạng:

| Viết trong câu dịch | Làm gì | Ví dụ kết quả |
|---|---|---|
| `{{language, lang}}` | mã ngôn ngữ → tên ngôn ngữ | `japanese` → 日本語 |
| `{{requiredLevel, level}}` | mã trình độ → nhãn trình độ | `business` → ビジネス（N2） |
| `{{missing, list}}` | mảng → chuỗi có dấu ngăn đúng chuẩn | `["Go","AWS"]` → Go、AWS |

> 💡 Bộ định dạng `list` dùng `Intl.ListFormat` của trình duyệt vì **dấu ngăn
> cách khác nhau giữa các ngôn ngữ**: tiếng Nhật dùng `、`, tiếng Việt và tiếng
> Anh dùng `,`. Nối bằng dấu phẩy cứng thì câu tiếng Nhật sai quy ước.

---

## 9.7. Số nhiều — cái bẫy của tiếng Anh

Tiếng Nhật và tiếng Việt không đổi từ theo số lượng:

```
1 kết quả · 5 kết quả          (tiếng Việt: giống nhau)
1件 · 5件                       (tiếng Nhật: giống nhau)
```

Tiếng Anh thì có:

```
1 result   ← số ít
5 results  ← số nhiều
```

Thư viện i18next xử lý việc này bằng **hậu tố**. Khi bạn truyền một tham số tên
là `count`, nó tự chọn bản phù hợp:

`en/common.json`:
```json
{ "status": {
    "foundResults_one":   "Found {{count}} result",
    "foundResults_other": "Found {{count}} results" } }
```

`ja/common.json` và `vi/common.json` chỉ cần `_other`:
```json
{ "status": { "foundResults_other": "{{count}}件見つかりました" } }
```

Dùng:
```jsx
{t('common:status.foundResults', { count: 5 })}
```

> ⚠️ **Chỉ đặt tên tham số là `count` khi thật sự muốn đổi từ theo số lượng.**
> Có một câu trong dự án bị vướng đúng chỗ này: *"Khớp 3/5 kỹ năng"* — chữ
> "kỹ năng" ăn theo **tổng số** (5), không ăn theo số khớp (3). Để tên `count`
> cho số khớp thì tiếng Anh sẽ ra *"Matched 1/5 skill"*. Đã đổi tên tham số
> thành `matchedCount` để i18next không kích hoạt cơ chế số nhiều.
>
> `scripts/check-i18n.mjs` bắt lỗi này: khoá nào dùng `{{count}}` mà thiếu hậu
> tố `_one`/`_other` đều bị báo.

---

## 9.8. Ngày tháng và tiền

Ba ngôn ngữ viết ngày khác nhau — và **cùng một chuỗi số có thể đọc ra hai ngày
khác nhau**:

```
09/06/2026   người Việt đọc: 9 tháng 6      người Mỹ đọc: 6 tháng 9
```

Nên khuôn ngày không được đặt cứng. `client/src/services/utils/format.js` dùng
`Intl` để trình duyệt tự chọn khuôn theo ngôn ngữ:

| Hàm | Dùng cho | ja | vi | en |
|---|---|---|---|---|
| `formatShortDate` | ngày sinh, ngày tạo | 2026/09/06 | 06/09/2026 | 09/06/2026 |
| `formatDate` | ngày dạng dài | 2026年9月6日 | 6 tháng 9, 2026 | September 6, 2026 |

Thời gian tương đối ("3 giờ trước") do thư viện `date-fns` lo;
`client/src/i18n/dateLocale.js` truyền cho nó đúng locale.

**Tiền lương** còn khác hơn nữa. Backend lưu **yên/năm**, nhưng ba nhóm người
đọc theo ba đơn vị:

| | Cách viết quen thuộc |
|---|---|
| Người Nhật | `500万円 / 年` — đơn vị 万 (1 man = 10.000 yên) |
| Người Việt ở Nhật | `500 man / năm` — mượn nguyên đơn vị 万 |
| Người đọc tiếng Anh | `¥5.0M / year` — không có khái niệm "man" |

`client/src/services/utils/jobFormat.js` tính sẵn **cả hai bộ số** rồi truyền
vào câu dịch; mỗi ngôn ngữ tự chọn con số hợp với quy ước của mình:

```
ja: {{minMan}}万円 〜 {{maxMan}}万円 / 年
vi: {{minMan}} ~ {{maxMan}} man / năm
en: ¥{{minM}}M ~ ¥{{maxM}}M / year
```

---

## 9.9. Ba lớp bảo vệ

Lỗi i18n có một đặc điểm nguy hiểm: **nó không làm hỏng gì cả**. Build vẫn
chạy, API vẫn trả 200, trang vẫn hiện. Chỉ là giữa giao diện tiếng Nhật bỗng có
một dòng tiếng Việt — và thường chỉ lộ ra đúng lúc demo.

Nên phải để máy canh, không thể trông vào việc "nhớ kiểm tra".

### Lớp 1 — ESLint chặn chuỗi mới lọt vào

`client/.eslintrc.cjs` bật luật `i18next/no-literal-string`. Viết chữ thẳng
vào JSX là bị cảnh báo ngay:

```jsx
<button>Lưu</button>                    ❌ ESLint kêu
<button>{t('common:actions.save')}</button>   ✅
```

CI chốt ngưỡng `--max-warnings 37` — đúng bằng số cảnh báo hiện tại (toàn bộ là
`react-hooks/exhaustive-deps`, không liên quan i18n). Thêm một chuỗi cứng là
vượt ngưỡng, CI đỏ.

> 💡 Không có lớp này, 459 khoá vừa dịch xong sẽ có khoá thứ 460 lọt vào ở PR
> sau mà không ai thấy. Đó là cách i18n chết dần ở mọi dự án.

### Lớp 2 — `check-i18n.mjs` đối chiếu ba ngôn ngữ

Chạy trong `npm run lint`. Bắt ba loại lỗi:

| Lỗi | Hậu quả nếu lọt |
|---|---|
| Thiếu khoá ở một ngôn ngữ | Câu đó lặng lẽ hiện tiếng Nhật |
| Lệch tham số `{{...}}` | Câu hiện ra thiếu số liệu: *"còn thiếu  năm"* |
| Thiếu dạng số nhiều | Tiếng Anh viết *"Found 1 results"* |

### Lớp 3 — Test ràng buộc backend với client

`server_python/tests/test_message_codes.py` đọc thẳng mã nguồn Python và
khẳng định:

- mọi `raise ApiError(...)` đều có `code=` (không thì client không dịch được);
- mọi mã dùng trong app đều tồn tại trong `app/messages.py`;
- mọi mã trong danh mục đều có bản dịch ở **cả ba** ngôn ngữ;
- tham số hai bên khớp nhau: `{max}` phía Python ↔ `{{max}}` phía client.

Và trong E2E (`e2e/test_e2e.py`) có một kịch bản đi hết một vòng: đổi sang tiếng
Việt → menu đổi theo → F5 vẫn giữ → nhập sai mật khẩu → **thông báo lỗi do máy
chủ sinh ra cũng ra tiếng Việt**. Vế cuối mới là vế quan trọng: nó kiểm đúng
đường đi từ `raise ApiError(code=...)` tới câu chữ trên màn hình.

> 💡 Các test E2E **không chép tay** câu tiếng Nhật vào file test. Chúng đọc
> thẳng từ file dịch qua hàm `tr('auth', 'login.submit')`. Chép tay thì sửa một
> câu trong file dịch sẽ làm đỏ test mà chẳng có lỗi thật nào — và tệ hơn: một
> component quên gọi `t()` vẫn qua được test nếu chuỗi cứng của nó trùng câu đã
> chép.

---

## 9.10. Vì sao gom file dịch thành một module

`client/vite-plugin-i18n-resources.js` đọc 36 file JSON ở phía Node rồi trả về
**một module duy nhất**.

Cách hiển nhiên hơn là để Vite tự nạp từng file (`import.meta.glob`). Nó chạy
đúng, nhưng ở chế độ phát triển Vite phục vụ **mỗi file JSON như một request
riêng**. Số đo thật trên dự án này:

| | Số request khi tải trang đăng nhập |
|---|---|
| Trước khi có i18n | 82 |
| Dùng `import.meta.glob` | **118** (36 request chỉ để lấy chữ) |
| Dùng module ảo | 82 |

36 request thêm nghe có vẻ nhỏ, nhưng nó đã làm hỏng thật: khi bộ test E2E mở
**hai tab cùng lúc** (kịch bản hai người dùng nhắn tin cho nhau), Chromium
trong container hết hạn mức tài nguyên mạng và tab chết với lỗi
`net::ERR_INSUFFICIENT_RESOURCES` — **không kèm bất kỳ lỗi JavaScript nào**.
Test báo "Target crashed", chạy riêng thì lại qua, rất dễ đọc nhầm thành lỗi
chập chờn của môi trường.

Cách truy ra: đếm request của từng trang, so hai phiên bản client, thấy đúng 36
request chênh lệch. Sau khi gom lại thành một module, cả 12 test E2E xanh.

> 💡 Bài học đáng nhớ hơn cả cách sửa: **một thay đổi "chỉ là chữ nghĩa" vẫn có
> thể làm sập trình duyệt**, và triệu chứng không hề chỉ về phía nguyên nhân.

---

## 9.11. Những gì cố ý KHÔNG dịch

| Thứ | Vì sao |
|---|---|
| Tiêu đề và mô tả tin tuyển dụng | Dữ liệu thật crawl từ 4 trang nguồn, tiếng Nhật hoặc tiếng Anh. Dịch máy sẽ làm sai nghĩa yêu cầu tuyển dụng. |
| Bài viết, bình luận, tin nhắn, CV | Nội dung do người dùng viết. |
| Tên website và câu trích (`webInfo`) | Admin tự đặt, lưu trong database. Muốn đa ngôn ngữ phải đổi schema thành `{ja, vi, en}`. |
| Tên ngôn ngữ trên nút chuyển (`日本語`, `Tiếng Việt`) | **Cố ý giữ nguyên bản.** Người chỉ đọc được tiếng Việt phải nhận ra dòng "Tiếng Việt" khi giao diện đang là tiếng Nhật — dịch nó đi là họ mất đường về. |
| Thông báo trong `console.error` và `throw` | Dành cho lập trình viên, không phải người dùng. |

---

## 9.12. Thêm ngôn ngữ thứ tư

Giả sử thêm tiếng Trung (`zh`):

1. `mkdir client/src/i18n/locales/zh`
2. Chép 12 file JSON từ `ja/` sang rồi dịch nội dung.
3. Thêm vào `SUPPORTED_LANGUAGES` trong `client/src/i18n/config.js`:
   ```js
   { code: 'zh', label: '中文', short: 'ZH' },
   ```
4. Thêm locale ngày tháng vào `client/src/i18n/dateLocale.js`:
   ```js
   import { zhCN } from 'date-fns/locale';
   const LOCALES = { ja, vi, en: enUS, zh: zhCN };
   ```
5. Thêm dạng số nhiều vào `PLURAL_FORMS` trong `client/scripts/check-i18n.mjs`
   (tiếng Trung chỉ có `other`).
6. Thêm `"zh"` vào danh sách `@pytest.mark.parametrize` trong
   `server_python/tests/test_message_codes.py`.
7. `npm run lint` — nó sẽ liệt kê đúng những khoá bạn còn thiếu.

Không phải sửa `resources.js`, không phải sửa danh sách namespace: plugin tự
quét thư mục.

---

## 9.13. Tra lỗi nhanh

| Triệu chứng | Nguyên nhân thường gặp |
|---|---|
| Màn hình hiện `job.actions.exportExcel` | Khoá không tồn tại ở **cả ba** ngôn ngữ. Chạy `npm run lint`. |
| Một dòng ra tiếng Nhật giữa giao diện tiếng Việt | Thiếu khoá ở `vi` → rơi về ngôn ngữ mặc định. |
| Toast ra tiếng Việt giữa giao diện tiếng Nhật | Backend thiếu `code=`, hoặc mã chưa có trong `error.json`. Chạy test `test_message_codes.py`. |
| Câu hiện ra thiếu số: *"còn thiếu  năm"* | Sai tên tham số. `check-i18n.mjs` sẽ chỉ đúng khoá. |
| Tiếng Anh viết *"Found 1 results"* | Thiếu `key_one` trong `en`. |
| Đổi ngôn ngữ nhưng một danh sách không đổi theo | Danh sách đó dùng `useMemo` mà **quên `t` trong mảng phụ thuộc**. Đổi ngôn ngữ làm `t` thành hàm mới; thiếu nó thì bản đã ghi nhớ giữ nguyên chữ cũ. ESLint có báo. |
| Ngày tháng vẫn theo khuôn tiếng Việt | Gọi thẳng `format()` của date-fns thay vì `formatShortDate`. |

---

## Đọc tiếp

- [8. Lỗi, log và kiểm thử](08-loi-log-va-kiem-thu.md) — cơ chế xử lý lỗi tập trung mà phần mã thông báo dựa lên
- [7. Embedding và gợi ý công ty](07-embedding-va-goi-y.md) — vì sao phần "còn thiếu gì" phải gửi dữ liệu thô
- [3. Tạo một màn hình mới](03-tao-mot-man-hinh-moi.md) — nơi bạn sẽ dùng `useTranslation` nhiều nhất
