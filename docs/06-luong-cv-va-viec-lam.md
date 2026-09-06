# 6. Luồng CV và việc làm

Đây là phần nền cho hai chức năng AI. Muốn máy so khớp CV với việc làm, trước
hết phải có **CV có cấu trúc** và **kho việc làm sạch**.

## 6.1. CV người dùng

### Người dùng nhập gì

Trang `/resume` (`client/src/layouts/home/Resume/ResumeLayout.jsx`) gồm 8 mục:

| Mục | Ví dụ |
|---|---|
| Thông tin cá nhân | tên, ngày sinh, email, SĐT, địa chỉ, GitHub |
| Mục tiêu | "Kỹ sư Backend 4 năm kinh nghiệm với Python, FastAPI…" |
| Học vấn | trường, chuyên ngành, năm tốt nghiệp, GPA |
| Kinh nghiệm | công ty, thời gian, vị trí, mô tả |
| Dự án | tên, công nghệ, mô tả |
| Kỹ năng | Python, Docker, PostgreSQL… |
| Ngôn ngữ | "Japanese N3 (JLPT)", "English business level" |
| Chứng chỉ | file PDF đính kèm |
| **Mục tiêu nghề nghiệp** | trình độ tiếng Nhật, tiếng Anh, số năm KN, lương mong muốn, nơi muốn làm |

Mục cuối cùng là phần **thêm mới** cho chức năng gợi ý. Lý do rất cụ thể: CV cũ
chỉ lưu `languages: ["JP", "EN"]` — biết là *có* tiếng Nhật nhưng không biết
**trình độ nào**. Mà đây là thị trường việc làm Nhật, nơi JLPT là tiêu chí lọc
số một.

### Chuyện gì xảy ra khi bấm Lưu

```
Bấm "Save"
   │
   └─▶ POST /api/resume  (dạng multipart vì có file chứng chỉ)
             │
             ├─ ① Lưu nguyên văn những gì người dùng nhập
             │
             ├─ ② apply_profile() — SUY RA những gì còn thiếu
             │      • "Japanese N3 (JLPT)"  → japanese_level = "conversational"
             │      • cộng các mốc thời gian → years_of_experience = 4
             │      • dò kỹ năng theo từ điển → skills_normalized = [Python, FastAPI…]
             │
             ├─ ③ resume_text() — gom thành một đoạn văn để máy đọc
             │
             └─ ④ Gửi đoạn văn đó sang embedder → nhận về một dãy 384 số
```

Bước ② nằm ở `server_python/app/services/resume_profile.py`. Nguyên tắc: **điều
người dùng tự khai luôn thắng**, máy chỉ điền vào chỗ trống.

Bước ③ có một chi tiết về quyền riêng tư:

```python
def resume_text(resume):
    """Cố ý BỎ tên, email, số điện thoại, địa chỉ: chúng không giúp gì cho việc
    so khớp năng lực, mà lại là dữ liệu cá nhân đi ra khỏi backend."""
```

Chỉ phần **năng lực** (chức danh, kỹ năng, mục tiêu, kinh nghiệm, dự án, học
vấn) được gửi đi. Tên và số điện thoại ở lại.

Bước ④ chỉ chạy khi nội dung **thật sự đổi** — so bằng một mã băm lưu kèm. Sửa
số điện thoại thì không cần tính lại vector.

Và toàn bộ bước ②③④ được bọc trong `try/except`:

```python
# Lỗi ở đây KHÔNG được làm hỏng việc lưu CV: người dùng đã bấm lưu và dữ liệu
# của họ đã nằm trong DB, cùng lắm là chạy `scripts.backfill_resumes` bù sau.
```

Dịch vụ embedder chết cũng không được làm mất CV của người dùng.

## 6.2. Kho việc làm — 430 tin từ đâu ra

### Cách cũ và vì sao phải bỏ

Bản đầu của dự án crawl **trực tiếp mỗi lần người dùng mở trang**: mở trình
duyệt ẩn, tải trang nguồn, cắt lấy HTML rồi nhúng thẳng vào giao diện.

Ba vấn đề:

1. **Chậm** — mỗi lần mở trang phải chờ crawl xong (vài giây).
2. **Không tìm kiếm được** — dữ liệu là HTML, không phải thông tin có cấu trúc.
   Không lọc theo lương, tỉnh, trình độ tiếng Nhật được.
3. **Không so khớp được** — không có gì để đem đi chấm điểm với CV.

### Cách hiện tại: ETL

**ETL** = Extract (lấy về) → Transform (chuẩn hoá) → Load (nạp vào kho). Chạy
tách rời khỏi lúc người dùng truy cập.

```
   4 trang việc làm Nhật
   ┌──────────────────────────────────────────┐
   │ GaijinPot 171 tin   nihongo-engineer 100 │
   │ DaiJob    100 tin   LinkedIn          59 │
   └────────────────┬─────────────────────────┘
                    │  ① EXTRACT — mở trình duyệt thật, lấy HTML
                    ▼
   ┌──────────────────────────────────────────┐
   │ Parser riêng cho từng trang               │
   │ app/services/etl/parsers/*.py             │
   └────────────────┬─────────────────────────┘
                    │  ② TRANSFORM — biến chữ thành dữ liệu
                    ▼
   ┌──────────────────────────────────────────┐
   │ "¥250,000/Month"     →  3.000.000 yên/năm │
   │ "日常会話レベル"        →  "conversational"   │
   │ "3+ years"           →  3                 │
   │ "東京都"              →  "Tokyo"            │
   │ "株式会社メルカリ"      →  "メルカリ"           │
   └────────────────┬─────────────────────────┘
                    │  ③ LOAD — ghi vào MongoDB, rồi tính vector
                    ▼
              430 tin · 245 công ty
```

### Chạy ETL

```bash
# Crawl thật từ 4 nguồn (cần mạng, mất vài phút)
docker compose run --rm server python -m scripts.run_etl --pages 5 --detail 120

# Hoặc nạp nhanh từ HTML đã lưu sẵn trong repo (KHÔNG cần mạng, ~3 giây)
docker compose run --rm server python -m scripts.seed_jobs_from_fixtures
```

### Vì sao cần `--detail`

**Trang danh sách của các trang việc làm không ghi yêu cầu tiếng Nhật.** Muốn
biết thì phải mở từng trang chi tiết. Số đo trước và sau khi thêm bước này:

| | Chỉ trang danh sách | Có tải trang chi tiết |
|---|---|---|
| Tin ghi rõ yêu cầu tiếng Nhật | 87 | **216** |
| Tin có danh sách kỹ năng | 231 | **346** |
| Tin ghi số năm kinh nghiệm | 28 | **140** |

Nếu không có bước này, hơn ba phần tư số tin sẽ không có gì để so khớp với CV,
và chức năng gợi ý gần như vô dụng.

## 6.3. Chuẩn hoá — phần khó nhất, và những cái bẫy có thật

Máy phải đọc chữ do người viết tự do và biến thành con số. Mỗi lỗi dưới đây
đều **đã thật sự xảy ra** và được phát hiện bằng test:

| Chữ gốc | Máy từng hiểu sai thành | Đúng phải là |
|---|---|---|
| `Date August 21, 2026` | lương 2.026 yên | không phải lương |
| `7.8万リンギット` (Ringgit Malaysia) | 78.000 yên | không phải yên → bỏ qua |
| `¥5,000 ~ ¥15,000 / Project` | 60.000 yên/năm | trả theo dự án → không quy đổi |
| `/ Month … 30,000 yen 交通費` | lương tối thiểu 360.000 | cắt tại mốc "/Month", trợ cấp không tính |
| `直接採用` (tuyển trực tiếp) | kỹ năng "Recruiting" — gắn nhầm 90/420 tin | không phải kỹ năng |
| `😍HOT JOB😍` | cắt mất chữ "HOT" trong chính tiêu đề | chỉ bỏ khi đứng riêng |

Toàn bộ nằm ở `server_python/app/services/etl/extract.py`, và mỗi dòng trong
bảng trên tương ứng một test ở `server_python/tests/test_etl_extract.py`.

> 💡 **Vì sao test được mà không cần mạng?** Các hàm chuẩn hoá là **hàm thuần**
> — đưa vào một chuỗi, trả ra một con số, không đụng mạng, không đụng kho dữ
> liệu. Nhờ vậy test chạy trong vài mili-giây và không phụ thuộc trang nguồn có
> sống hay không.

Còn phần parser (cắt HTML) được test bằng **HTML thật đã lưu lại** trong
`server_python/tests/fixtures/`. Trang nguồn có đổi giao diện thì test vẫn chạy
được, và khi cần cập nhật thì chỉ việc lưu lại HTML mới.

### Hai lỗi cắt HTML đáng nhớ

**DaiJob có hai thẻ `<dl>` trong mỗi thẻ tin.** Code cũ dùng `select_one("dl")`
— chỉ lấy cái đầu tiên, nên **mất toàn bộ mô tả công việc**.

**GaijinPot dùng bộ chọn `.card--premium`** — chỉ khớp tin trả phí, nên chỉ lấy
được **26 trong 51 tin** mỗi trang. Gần một nửa số tin bị bỏ sót âm thầm.

Bài học chung: parser phải **hỏng ồn ào**. Nay nếu một nguồn trả về 0 tin trong
khi lần trước có, ETL ghi log mức ERROR và báo trong kết quả — thay vì lặng lẽ
trả về danh sách rỗng.

## 6.4. Gộp công ty giữa các nguồn

Cùng một công ty xuất hiện ở nhiều trang với nhiều cách viết:

```
"株式会社メルカリ"  ─┐
"Mercari, Inc."   ─┼─▶  chuẩn hoá tên  ─▶  một bản ghi Company duy nhất
"メルカリ"         ─┘
```

Hàm `normalize_company_name()` bỏ các hậu tố pháp lý (`株式会社`, `Inc.`,
`K.K.`, `合同会社`) rồi lấy phần lõi làm khoá.

**Giới hạn đã biết và ghi rõ trong code:** cách này *không* gộp được các biến
thể khác hệ chữ viết — `メルカリ` (Katakana) và `Mercari` (Latin) vẫn thành hai
bản ghi. Muốn gộp thì cần bảng ánh xạ thủ công hoặc so khớp mờ, cả hai đều dễ
gộp nhầm hai công ty khác nhau. Chấp nhận trùng còn hơn gộp sai.

## 6.5. Trang Việc làm

Trang `/recruitment` (`client/src/layouts/home/Recruitment/RecruitmentLayout.jsx`)
đọc từ kho đã ETL, có tìm kiếm và 5 bộ lọc: tỉnh, trình độ tiếng Nhật, lương
tối thiểu, kỹ năng, làm từ xa.

Một chi tiết kỹ thuật đáng ghi lại. Bộ lọc dùng thẳng `useSearchParams`:

```jsx
const setFilter = (key, value) => {
  const next = new URLSearchParams(searchParams.toString());
  if (value) next.set(key, value); else next.delete(key);
  next.set('page', '1');       // đổi bộ lọc thì luôn về trang 1
  setSearchParams(next);
};
```

Trước đó trang này dùng hook chung `useQueryString`, và dính hai lỗi: hook đó
**tự động đặt `page=1`** nên gọi hai lần liên tiếp sẽ đọc phải trạng thái cũ và
ghi đè lẫn nhau; còn `deleteQueryString()` thì **xoá sạch mọi tham số** chứ
không chỉ một bộ lọc.

## 6.6. Bản đồ file

| File | Vai trò |
|---|---|
| `app/services/etl/extract.py` | Hàm chuẩn hoá: lương, trình độ, số năm, tỉnh |
| `app/services/etl/skills.py` | Từ điển ~135 kỹ năng và các cách viết khác nhau |
| `app/services/etl/parsers/*.py` | Cắt HTML, mỗi nguồn một file |
| `app/services/etl/detail.py` | Đọc trang chi tiết để lấy yêu cầu |
| `app/services/etl/pipeline.py` | Ghép cả dây chuyền, ghi vào kho |
| `app/services/browser.py` | Trình duyệt dùng chung (Chromium) |
| `scripts/run_etl.py` | Lệnh chạy ETL |
| `scripts/seed_jobs_from_fixtures.py` | Nạp nhanh, không cần mạng |
| `app/models/job.py`, `app/models/company.py` | Hình dạng dữ liệu |
| `app/services/resume_profile.py` | Suy ra hồ sơ so khớp từ CV |
| `scripts/backfill_resumes.py` | Bổ sung dữ liệu cho CV cũ |
| `scripts/seed_demo_user.py` | Tạo tài khoản demo kèm CV đầy đủ |

---

Tiếp theo: [7. Embedding và gợi ý công ty](07-embedding-va-goi-y.md)
