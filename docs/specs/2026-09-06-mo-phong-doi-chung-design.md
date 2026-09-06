# Thiết kế — "Nếu tôi học X thì sao?" (mô phỏng đối chứng)

**Ngày:** 2026-09-06 · **Trạng thái:** chờ duyệt · **Ước lượng:** ~1 tuần

---

## 1. Vấn đề đang giải

Chức năng *"tôi còn thiếu gì để vào công ty A"* hiện **dừng ở chỗ liệt kê**. Nó
nói bạn thiếu N2 và thiếu Kubernetes, rồi hết. Người tìm việc đọc xong vẫn không
biết điều quan trọng nhất:

> Tôi chỉ có thời gian học **một** thứ. Học cái nào thì mở ra nhiều cơ hội nhất?

Đó là câu hỏi có đáp án **tính được** — dự án đã có sẵn 430 tin tuyển dụng và một
bộ luật chấm điểm tất định. Chỉ cần chấm lại toàn bộ kho tin với một bản CV
*giả định*, rồi so số lượng tin đủ điều kiện trước và sau.

### Vì sao đây là chức năng đáng làm cho đồ án

Điểm khác biệt của dự án đang nằm ở chỗ **chấm điểm bằng luật, tất định, giải
thích được** — thứ mà một lớp bọc quanh LLM không làm được. Mô phỏng đối chứng
là phần mở rộng tự nhiên và *độc quyền* của kiến trúc đó: hỏi một mô hình ngôn
ngữ "học Kubernetes có ích không" thì nhận về một đoạn văn nghe hợp lý; hỏi hệ
thống này thì nhận về **con số kiểm chứng được**, và người hỏi tự bấm lại được.

---

## 2. Bằng chứng — đã đo trước khi thiết kế

Nguyên mẫu chạy trong container `server`, trên dữ liệu thật:

```
jobs=430   CV mẫu: JLPT=conversational, 2 kỹ năng
BASE: 66/430 tin đủ điều kiện          (1 lượt quét toàn kho = 2ms)

15 phương án × 430 tin = 6.450 lần chấm điểm trong 22ms

  +35 tin   skill    -> Teaching
  +33 tin   japanese -> fluent
  +30 tin   japanese -> business
  +21 tin   skill    -> Sales
  ...
```

**Kết luận về tính khả thi:** một lượt quét là 2ms. Người dùng tick một ô là tính
lại được ngay trong request, **không cần cache, không cần hàng đợi, không cần
tính trước**. Đây là điều kiện để giao diện phản hồi tức thì.

### 2.1. Hai phát hiện làm đổi thiết kế

**① Lương không tăng theo trình độ tiếng Nhật.** Trung vị lương (万円/năm) theo
mức tiếng Nhật mà tin yêu cầu:

| Mức yêu cầu | Số tin có ghi lương | Trung vị |
|---|---|---|
| none | 12 | 300 |
| basic | 13 | 264 |
| **conversational** | 39 | **450** |
| business | 101 | 400 |
| fluent | 12 | 350 |
| native | 14 | 400 |

Không hề đơn điệu tăng. Nhìn sang bảng kỹ năng thì thấy nguyên nhân:

| Kỹ năng | Số tin | Trung vị lương |
|---|---|---|
| Teaching | 109 | 300 |
| AWS | 52 | **500** |
| JavaScript | 45 | **500** |
| Python | 37 | **500** |
| Google Cloud | 29 | **500** |
| Customer Support | 46 | 300 |
| Hospitality | 34 | 312 |

Nhóm tin đòi tiếng Nhật cao phần lớn là giảng dạy và dịch vụ, không phải kỹ thuật.

> **Vì vậy KHÔNG làm biểu đồ "JLPT càng cao lương càng cao".** Dữ liệu không đỡ
> được kết luận đó, và một câu hỏi phản biện là đủ để lật. Thay vào đó tách hai
> trục và nói đúng thứ đo được:
>
> **Tiếng Nhật mở ra *số lượng* cơ hội — kỹ năng quyết định *mức lương*.**

**② Delta không cộng được — và đi được CẢ HAI chiều.** Đây chính là lý do phải
có **engine chấm lại**, không thể dùng một bảng tra sẵn.

> **Cập nhật sau khi triển khai.** Bản đầu của mục này đoán rằng kết hợp luôn
> *nhỏ hơn* tổng lẻ. Chạy trên dữ liệu thật thì thấy ngược lại:
>
> ```
> lên N2      →  +64 tin
> học Sales   →  +42 tin
> cộng lẻ     →  106
> làm cả hai  →  +116   ← NHIỀU hơn
> ```
>
> Vì có những tin đòi **cùng lúc** cả hai thứ: bù riêng từng cái thì cái còn lại
> vẫn chặn, nên chúng không được tính vào lợi ích lẻ nào cả.
>
> Chiều ngược lại cũng có thật: một tin yêu cầu `["Go", "Rust"]` mà CV chưa có
> gì thì học Go mở được tin đó, học Rust cũng mở được tin đó, học cả hai vẫn chỉ
> là **một** tin.
>
> Cả hai chiều giờ đều có test pin lại
> (`test_combining_can_open_MORE_...` và `..._FEWER_...`), và giao diện **so số
> thật với tổng lẻ rồi mới chọn câu giải thích** thay vì viết cứng một chiều.

---

## 3. Cách hoạt động

### 3.1. Thước đo chính: "số tin đủ điều kiện"

`MatchResult.is_qualified` hiện đã là `not any(g.blocking for g in self.gaps)`
([matching.py:131](../../server_python/app/services/matching.py#L131)) — **hoàn
toàn không phụ thuộc vào vector ngữ nghĩa**. Nghĩa là con số đưa lên màn hình là
số chính xác, không phải ước lượng, và **vẫn đúng nguyên vẹn khi service
`embedder` tắt**.

Điều kiện bị loại (`blocking=True`) hiện có ba nhóm:

| Nguồn | Điều kiện |
|---|---|
| Tiếng Nhật / Anh | CV chưa ghi trình độ, hoặc thấp hơn mức tin đòi |
| Kỹ năng | **không khớp một kỹ năng nào** (`ratio == 0`) |
| Kinh nghiệm | tin đòi số năm mà CV ghi 0 năm |

Luật kỹ năng giải thích vì sao đồ thị lợi ích không tuyến tính: kỹ năng **đầu
tiên** khớp được có giá trị rất lớn (gỡ hẳn điều kiện loại), kỹ năng thứ hai trở
đi chỉ tăng tỷ lệ đáp ứng.

### 3.2. Sinh danh sách phương án

Không hỏi người dùng "bạn định học gì" — hệ thống tự đề xuất, xếp theo lợi ích:

| Loại | Nguồn |
|---|---|
| Kỹ năng | Kỹ năng được nhiều tin yêu cầu nhất **mà CV chưa có**, lấy từ tầng thống kê (3.4) |
| Tiếng Nhật | Hai bậc kế tiếp trong `LANGUAGE_LEVELS` |
| Tiếng Anh | Bậc kế tiếp |
| Kinh nghiệm | Mốc +1 năm, +2 năm |

Với mỗi phương án: nhân bản CV, sửa đúng một trường, chấm lại toàn kho, lấy hiệu.

### 3.3. Kết hợp nhiều phương án

Người dùng tick nhiều ô → **chấm lại một lượt với CV đã áp dụng tất cả** (2ms),
chứ không cộng các delta. Giao diện nói rõ con số kết hợp khác tổng các con số
lẻ, và vì sao.

### 3.4. Tầng thống kê thị trường (nền dữ liệu cho 3.2, và là màn hình phụ)

Một endpoint tổng hợp trên 430 tin, dùng cho **cả hai** việc: sinh danh sách ứng
viên ở 3.2, và dựng màn hình "bản đồ thị trường".

| Số liệu | Cách tính |
|---|---|
| Nhu cầu kỹ năng | `$unwind: required_skills` → đếm |
| Trung vị lương theo kỹ năng | trên tập tin có `salary_min` |
| Phân bố yêu cầu JLPT | đếm theo `required_japanese` |
| Phân bố theo tỉnh | đếm theo `prefecture` |

**Bắt buộc hiện `n` kèm mọi trung vị.** Nhiều nhóm chỉ có 12–14 tin (bảng ở 2.1);
không hiện cỡ mẫu là trưng nhiễu như thể là quy luật. Nhóm có `n < 10` bị gộp vào
"khác" thay vì hiện riêng.

### 3.5. Điều cố ý KHÔNG làm: ước lượng số giờ học một kỹ năng

Không có nguồn đáng tin cho "học Kubernetes mất bao lâu", và con số bịa ra sẽ là
chỗ yếu nhất của cả chức năng. Thay vào đó hiển thị hai đại lượng **đo được từ
dữ liệu**: số tin mở thêm, và trung vị lương của nhóm tin đó.

Riêng JLPT có khoảng giờ học tham khảo được công bố rộng rãi — nếu hiển thị thì
phải ghi **dạng khoảng**, kèm nguồn, và ghi rõ là số tham khảo cho người không có
nền Hán tự. Nếu không tìm được nguồn trích dẫn được thì bỏ hẳn.

---

## 4. Phạm vi thay đổi

### 4.1. Backend

| File | Việc |
|---|---|
| `app/services/whatif.py` *(mới)* | Sinh phương án, chấm lại, xếp theo lợi ích |
| `app/services/market.py` *(mới)* | Tổng hợp thống kê thị trường (3.4) |
| `app/controllers/match.py` | Thêm controller cho 2 endpoint mới |
| `app/routes/match.py` | `GET /api/match/whatif` (gợi ý), `POST /api/match/whatif` (áp dụng tổ hợp) |
| `app/routes/jobs.py` | `GET /api/jobs/market` |
| `app/schemas/responses.py` | `response_model` cho cả ba |

Dùng lại nguyên `evaluate()` — **không sửa `matching.py`**. Đây là ràng buộc quan
trọng: mô phỏng phải chạy đúng bộ luật mà trang gợi ý đang dùng, nếu tách đôi thì
hai màn hình sẽ nói khác nhau về cùng một CV.

### 4.2. Frontend

| File | Việc |
|---|---|
| `layouts/home/Match/WhatIfLayout.jsx` *(mới)* | Danh sách phương án + ô tick + số liệu cập nhật tức thì |
| `layouts/home/Market/MarketLayout.jsx` *(mới)* | Bản đồ thị trường |
| `services/redux/query/...` | Khai báo 3 endpoint |
| `i18n/locales/{ja,vi,en}/` | Namespace `whatif` + `market` |
| `router.jsx`, `LeftAside.jsx` | Route + menu |

Biểu đồ: vẽ bằng SVG thuần, **không thêm thư viện chart**. Ba loại cần dùng (cột,
cột ngang, phân bố) đều đơn giản; thêm một dependency 200KB cho ba biểu đồ là
không đáng, và đây là chỗ dependency dễ mục nhất.

### 4.3. Hai lỗi sửa kèm

**① Thông báo chưa đa ngôn ngữ.** `Notification.notification` đang lưu **câu chữ
cứng vào DB**, lẫn cả hai ngôn ngữ:

```python
notification=f"{username} just liked your post!"        # posts.py:249   — tiếng Anh
notification=f"Admin đã xóa bạn ra khỏi channel {c}!"   # channels.py:155 — tiếng Việt
```

Client render thẳng `{n.notification}`. Giao diện tiếng Nhật đang có **221 thông
báo** không phải tiếng Nhật.

Sửa theo **đúng khuôn đã dùng cho thông báo lỗi**: thêm `code` + `params` vào
model, client dịch theo `code`. Giữ nguyên trường `notification` cũ làm dự phòng
để **221 bản ghi cũ vẫn đọc được** — không migrate, không xoá.

**② Lỗ trong bộ kiểm tra.** `test_no_api_error_raised_without_code` chỉ quét
`raise ApiError(...)`, không quét `ok(...)`. Quét lại bằng AST thấy một chỗ lọt:

```
controllers/channels.py:160   ok(message=f"Đã xóa người dùng id:{...} ra khỏi channel!")
```

Toast đó hiện tiếng Việt giữa giao diện Nhật, kèm cả ObjectId thô. Mở rộng phép
kiểm sang `ok()` và gán mã cho chỗ này. Thêm phép kiểm thứ ba: **mọi
`Notification(...)` phải có `code=`**.

---

## 5. Kiểm chứng

| Việc | Bằng chứng phải đạt |
|---|---|
| Engine đúng | Test với CV + tin dựng tay: bù đúng chỗ thiếu thì tin chuyển sang đủ điều kiện |
| **Delta không cộng được (cả hai chiều)** | Hai test riêng trên dữ liệu dựng tay: một pin chiều kết hợp > tổng lẻ, một pin chiều kết hợp < tổng lẻ |
| Không có embedder vẫn chạy | Tắt `embedder`, endpoint vẫn 200 và số tin đủ điều kiện **không đổi** |
| Cùng bộ luật | Test: số tin đủ điều kiện từ `/api/match/whatif` khớp số đếm từ `/api/match/jobs` |
| Hiệu năng | Test khẳng định một lượt quét < 50ms trên 430 tin |
| Thống kê trung thực | Test: mọi nhóm trả về đều kèm `n`, và nhóm `n < 10` không đứng riêng |
| Đa ngôn ngữ | `npm run check:i18n` xanh; thông báo mới hiện đúng 3 thứ tiếng |
| Bộ kiểm mở rộng | Test guard bắt được `ok()` và `Notification()` thiếu `code=` |
| E2E | Đăng nhập → `/match/whatif` → tick một ô → số đổi |

---

## 6. Rủi ro

| Rủi ro | Cách xử lý |
|---|---|
| CV mẫu quá nghèo làm số liệu vô nghĩa | CV demo đã có sẵn (`seed_demo_user --contrast`); màn hình nhắc bổ sung CV khi thiếu dữ liệu để mô phỏng |
| Trung vị trên cỡ mẫu nhỏ bị đọc thành quy luật | Luôn hiện `n`; gộp nhóm `n < 10` |
| Người dùng hiểu "mở thêm 35 tin" = "chắc chắn được nhận" | Câu chữ nói rõ: đây là số tin **qua được vòng lọc điều kiện**, không phải số tin sẽ trúng tuyển |
| Chức năng phình sang gợi ý khoá học / lộ trình | Ngoài phạm vi đợt này (mục 7) |
| Mô phỏng lệch khỏi trang gợi ý | Dùng chung `evaluate()`, có test đối chiếu số liệu giữa hai endpoint |

---

## 7. Ngoài phạm vi (cố ý không làm)

- **Không dùng LLM** ở chức năng này. Số liệu là tất định; chỗ dùng LLM đúng vai
  là *diễn đạt lại* số liệu thành đoạn văn tiếng Nhật, và đó là việc của đợt sau,
  làm theo kiểu suy giảm êm như `embedder` (tắt đi thì vẫn còn đủ số).
- Không gợi ý khoá học / tài liệu học cụ thể.
- Không lưu lịch sử mô phỏng, không đặt mục tiêu, không nhắc tiến độ.
- Không ước lượng số giờ học cho kỹ năng (lý do ở 3.5).
- Không thêm thư viện biểu đồ.
