# Fuurin — Mạng xã hội tuyển dụng cho thị trường Nhật Bản

[![CI](https://github.com/anhthaingd/sns/actions/workflows/ci.yml/badge.svg)](https://github.com/anhthaingd/sns/actions/workflows/ci.yml)
[![Crawl health](https://github.com/anhthaingd/sns/actions/workflows/crawl-health.yml/badge.svg)](https://github.com/anhthaingd/sns/actions/workflows/crawl-health.yml)

Ứng dụng full-stack gồm ba mảng ghép lại: **mạng xã hội** (đăng bài, channel,
follow) + **nhắn tin & gọi video thời gian thực** + **sàn việc làm Nhật Bản có
gợi ý theo CV**. Giao diện nói được **ba thứ tiếng: Nhật · Việt · Anh**.

**Đọc README này từ trên xuống là chạy được dự án từ con số không.** Nếu chỉ
muốn chạy nhanh, làm đúng [mục 3](#3-chạy-dự-án-bằng-docker-khuyên-dùng) là đủ.

---

## Mục lục

| | |
|---|---|
| [1. Web này làm được gì](#1-web-này-làm-được-gì) | Danh sách chức năng chính |
| [2. Cần cài gì trước](#2-cần-cài-gì-trước) | Yêu cầu môi trường |
| [3. Chạy bằng Docker](#3-chạy-dự-án-bằng-docker-khuyên-dùng) | **Cách khuyên dùng — 5 bước** |
| [4. Chạy thủ công](#4-chạy-thủ-công-không-dùng-docker) | Khi không muốn dùng Docker |
| [5. Hướng dẫn sử dụng lần đầu](#5-hướng-dẫn-sử-dụng-lần-đầu) | Bấm vào đâu để thấy chức năng nào |
| [6. Lệnh Docker hữu ích](#6-các-lệnh-docker-hữu-ích) | Xem log, restart, xoá dữ liệu |
| [7. Biến môi trường](#7-biến-môi-trường) | Cấu hình secret, TTL token, CORS |
| [8. Xử lý sự cố](#8-xử-lý-sự-cố) | Bảng triệu chứng → cách sửa |
| [9. Chạy test](#9-chạy-test) | Test API, E2E, lint, kiểm tra bản dịch |
| [10. Cấu trúc thư mục](#10-cấu-trúc-thư-mục) | File nào nằm ở đâu |
| [11. Tài liệu chi tiết](#11-tài-liệu-chi-tiết) | Muốn hiểu sâu / tự thêm chức năng |

---

## 1. Web này làm được gì

### 1.1. Tài khoản & bảo mật

- Đăng ký, đăng nhập, đăng xuất, trang cá nhân, đổi ảnh đại diện/ảnh bìa.
- **Access token 15 phút + refresh token trong cookie `httpOnly`** — JavaScript
  không đọc được refresh token. Hết hạn access token thì client tự gia hạn ngầm,
  người dùng không bị văng ra.
- **Xoay vòng refresh token**: mỗi lần gia hạn là phát token mới và thu hồi token
  cũ, nên token bị đánh cắp chỉ dùng được đúng một lần.
- **Chống dò mật khẩu**: giới hạn số lần đăng nhập sai theo email và theo IP.
- **Không lộ email nào đã tồn tại**: sai email hay sai mật khẩu đều trả về cùng
  một thông báo, và thời gian phản hồi được làm cho bằng nhau.
- Phân quyền `user` / `admin`.

### 1.2. Mạng xã hội

| Chức năng | Mô tả |
|---|---|
| **Bảng tin** | Bài viết từ các channel bạn đã tham gia |
| **Channel (nhóm)** | Tham gia channel, đăng bài trong channel, xem danh sách thành viên |
| **Bài viết** | Soạn thảo có định dạng (rich text), đính kèm ảnh, sửa, xoá |
| **Tương tác** | Thích, bình luận, **lưu bài** (Bookmark) |
| **Theo dõi** | Follow / unfollow người khác, xem danh sách follower & following |
| **Thông báo** | Có người thích, bình luận, follow → hiện trong chuông thông báo |
| **Tìm kiếm** | Tìm bài viết và tìm người dùng |
| **Lối tắt** | Channel hay vào được ghim lên menu bên trái |
| **Giao diện sáng/tối** | Nút đổi theme trên thanh trên cùng |

### 1.3. Nhắn tin & gọi video (thời gian thực)

- Nhắn tin 1-1 qua **Socket.io**, có phân trang lịch sử tin nhắn.
- **Gọi video 1-1 qua WebRTC** (`simple-peer`) dùng STUN server công cộng của
  Google — **không cần API key trả phí nào**.

### 1.4. Việc làm & CV — phần trọng tâm của đồ án

| Chức năng | Mô tả |
|---|---|
| **Tạo CV** | Thông tin cá nhân, học vấn, kinh nghiệm, kỹ năng, chứng chỉ, ngôn ngữ, mục tiêu nghề nghiệp. In hoặc lưu ra PDF theo mẫu có sẵn |
| **Tin tuyển dụng** | Tin từ **4 nguồn** (DaiJob, GaijinPot, Nihongo Engineer, LinkedIn JP) đã được chuẩn hoá về cùng một dạng: tìm theo từ khoá, lọc theo **trình độ tiếng Nhật**, mức lương, tỉnh/thành, việc remote |
| **Công ty phù hợp** | Xếp hạng công ty theo mức khớp với CV của bạn, kèm **lý do** cho từng công ty |
| **"Tôi còn thiếu gì?"** | Với một công ty hoặc một vị trí cụ thể: liệt kê rõ **bắt buộc phải bù** / **nên có thêm** / **bạn đã đáp ứng** |
| **"Nếu tôi học thêm thì sao?"** | Tick những thứ bạn định bù → hệ thống chấm lại cả 430 tin và cho biết mở ra thêm bao nhiêu cơ hội, kèm trung vị lương của nhóm tin đó |
| **Bản đồ thị trường** | Kỹ năng nào đang được săn, lương theo kỹ năng / trình độ tiếng Nhật / tỉnh thành — mọi trung vị đều kèm cỡ mẫu |

Điểm phù hợp gồm **hai phần tách bạch** để kiểm chứng được:

| Thành phần | Trọng số | Cách tính |
|---|---|---|
| Độ liên quan ngành nghề | 55% | So sánh vector ngữ nghĩa giữa CV và tin tuyển dụng |
| Mức đáp ứng yêu cầu | 45% | Đối chiếu **bằng luật**: tiếng Nhật, tiếng Anh, số năm kinh nghiệm, kỹ năng, lương, địa điểm |

> **Vì sao phải có phần thứ hai.** Đo trên chính dữ liệu của dự án: hai CV chỉ
> khác nhau đúng một dòng `Japanese: none` / `Japanese: N1` có độ tương đồng
> vector **0.9871** — tức là nếu chỉ dùng vector, hai người có trình độ tiếng
> Nhật hoàn toàn khác nhau sẽ nhận **cùng một danh sách gợi ý**. Mà tại thị
> trường Nhật, JLPT lại chính là tiêu chí lọc số một.

**Toàn bộ phần này chạy offline, 0đ chi phí API** — không gọi ChatGPT hay bất kỳ
LLM trả phí nào. Vector do service `embedder` tự tính trên CPU, model 220MB được
nướng sẵn vào image nên **không cần mạng lúc demo**.

### 1.5. Đa ngôn ngữ (Nhật · Việt · Anh)

- **Mặc định là tiếng Nhật.** Đổi bằng ba nút `JA / VI / EN` ở thanh trên cùng
  (và ở cả trang đăng nhập / đăng ký, khi chưa có tài khoản).
- Lựa chọn được nhớ trong trình duyệt, mở lại vẫn đúng ngôn ngữ đó.
- Dịch **cả thông báo lỗi do máy chủ sinh ra**, không chỉ chữ trên giao diện.
- Ngày tháng, số nhiều, danh sách liệt kê đều theo đúng quy tắc từng ngôn ngữ.
- **460 khoá × 3 ngôn ngữ = 1.380 bản dịch**, có công cụ tự kiểm tra khớp nhau.

### 1.6. Trang quản trị (admin)

Quản lý người dùng, quản lý bài viết, **tạo channel**, và tuỳ biến website (tên
web, logo, ảnh bìa).

---

## 2. Cần cài gì trước

Chỉ cần **một trong hai**:

| | Cần cài | Ưu / nhược |
|---|---|---|
| **Cách A — Docker** ⭐ | [Docker Desktop](https://www.docker.com/products/docker-desktop/) hoặc [OrbStack](https://orbstack.dev/) | Không phải cài Python, Node, MongoDB, Redis. **Khuyên dùng** |
| **Cách B — Thủ công** | [Python](https://www.python.org/downloads/) 3.12+, [Node.js](https://nodejs.org/) 18+, [MongoDB](https://www.mongodb.com/try/download/community) 6+ | Nhiều bước hơn, dễ lệch phiên bản |

Dung lượng đĩa cần cho image Docker (đo trên máy thật):

| | |
|---|---|
| Stack chính (5 container) | **~3,4GB** — server 1,13GB (kèm Chromium cho crawl) · embedder 886MB (kèm model) · mongo 828MB · client 509MB · redis 40MB |
| Thêm nếu chạy test E2E | ~2,2GB |

---

## 3. Chạy dự án bằng Docker (khuyên dùng)

### Bước 1 — Lấy mã nguồn

```bash
git clone https://github.com/anhthaingd/sns.git
cd sns
```

### Bước 2 — Chạy toàn bộ bằng MỘT lệnh

```bash
docker compose up -d --build
```

Lệnh này tự động dựng **5 container**:

| Container | Việc của nó |
|---|---|
| `mongo` | Cơ sở dữ liệu, **tự nạp sẵn** roles + cấu hình website |
| `redis` | Giữ danh sách token đã thu hồi + bộ đếm chống dò mật khẩu |
| `embedder` | Tính vector ngữ nghĩa (model 220MB nướng sẵn trong image) |
| `server` | Backend FastAPI, kèm sẵn Chromium của Playwright |
| `client` | Frontend React + Vite |

> Lần đầu hơi lâu (vài phút) vì phải tải image và cài dependency. Các lần sau
> rất nhanh. Chờ tới khi `docker compose ps` báo tất cả **healthy**.

### Bước 3 — Mở ứng dụng

| Thành phần | Địa chỉ |
|---|---|
| **Ứng dụng — mở cái này** | **http://localhost:5173** |
| Backend API | http://localhost:3000 |
| API docs (Swagger, thử API trực tiếp) | http://localhost:3000/docs |
| Health check | http://localhost:3000/health |
| MongoDB | mongodb://localhost:27017/fuurin |
| Redis | redis://localhost:6379 (không mở ra ngoài) |
| Embedder | http://embedder:8001 (chỉ trong mạng docker) |

### Bước 4 — Nạp dữ liệu việc làm

Lần đầu chạy, kho việc làm còn trống. Chọn **một** trong hai cách:

```bash
# A. NHANH, KHÔNG CẦN MẠNG — nạp 100 tin từ HTML đã lưu sẵn trong repo.
#    Dùng đúng parser mà hệ thống dùng thật, chỉ khác nguồn là file thay vì web.
docker compose run --rm server python -m scripts.seed_jobs_from_fixtures

# B. DỮ LIỆU MỚI — crawl thật từ 4 trang nguồn (cần internet, vài phút).
#    --detail nạp thêm trang chi tiết để lấy yêu cầu tiếng Nhật, kỹ năng, số năm
#    kinh nghiệm; không có nó thì ~79% tin thiếu các trường này.
docker compose run --rm server python -m scripts.run_etl --pages 5 --detail 120
```

### Bước 5 — Tạo tài khoản demo (khuyến nghị)

Chức năng gợi ý công ty chỉ chạy khi tài khoản **đã có CV**. Lệnh dưới tạo sẵn
một tài khoản kèm CV đầy đủ mọi mục, đăng nhập được ngay:

```bash
docker compose run --rm server python -m scripts.seed_demo_user --contrast
```

| | |
|---|---|
| Email | `demo@fuurin.local` |
| Mật khẩu | `Demo@12345` |
| Hồ sơ | Backend Engineer · 4 năm KN · tiếng Nhật N3 · 15 kỹ năng |

CV này **cố ý chưa hoàn hảo** (N3 chứ không phải N2, không biết Kubernetes/Go)
để chức năng "còn thiếu gì để vào công ty A" có nội dung thật để hiển thị — CV
hoàn hảo thì trang đó trống trơn. Chạy xong, script in ra sẵn đường dẫn của một
tin **đã đủ điều kiện** và một tin **còn rào cản** để mở lên xem.

`--contrast` tạo thêm `demo-nojp@fuurin.local` — cùng kỹ năng, cùng kinh nghiệm,
**chỉ khác là không biết tiếng Nhật**. Mở hai tài khoản cạnh nhau sẽ thấy danh
sách gợi ý khác hẳn (đo được: top 10 chỉ trùng 2 tin). Xoá cả hai bằng `--clean`.

Muốn có thêm nhiều CV đa dạng để thử:

```bash
docker compose run --rm server python -m scripts.seed_resumes --count 100
docker compose run --rm server python -m scripts.seed_resumes --clean   # xoá đi
```

**Xong!** Chuyển sang [mục 5 — Hướng dẫn sử dụng lần đầu](#5-hướng-dẫn-sử-dụng-lần-đầu).

---

## 4. Chạy thủ công (không dùng Docker)

<details>
<summary>Bấm để xem hướng dẫn chi tiết</summary>

### 4.1. Chuẩn bị MongoDB

Đảm bảo MongoDB đang chạy ở `mongodb://127.0.0.1:27017`. Sau đó nạp dữ liệu khởi tạo:

```bash
mongoimport --db fuurin --collection roles --jsonArray --drop --file server_python/data/roles.json
mongoimport --db fuurin --collection webs  --jsonArray --drop --file server_python/data/social_app.webs.json
```

### 4.2. Backend (Python / FastAPI)

```bash
cd server_python
cp .env.example .env          # xem muc 7 de dien cac bien
# Sua .env: DATABASE_URL=mongodb://127.0.0.1:27017/fuurin
# Tuy chon: REDIS_URL=redis://127.0.0.1:6379/0
#   Khong dat REDIS_URL thi app van chay, nhung blacklist token va bo dem
#   rate limit nam trong RAM tien trinh -> mat sach khi restart backend.

python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
playwright install chromium   # trinh duyet cho chuc nang crawl

uvicorn app.main:socket_app --reload --port 3000
```

### 4.3. Frontend

Mở terminal khác:

```bash
cd client
npm install
npm run dev               # chay tai http://localhost:5173
```

### 4.4. Embedder (tuỳ chọn)

Bỏ qua bước này cũng chạy được: không có embedder thì hệ thống **tự chuyển sang
chấm điểm thuần luật**, trang gợi ý vẫn hoạt động và hiện dòng "Đang xếp hạng
bằng luật".

```bash
cd embedder
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --port 8001
# roi dat EMBEDDER_URL=http://127.0.0.1:8001 trong server_python/.env
```

> **Lưu ý:** biến kết nối DB tên là `DATABASE_URL`. Client đọc địa chỉ backend
> qua `client/.env` (`VITE_BACKEND_URL`).
</details>

---

## 5. Hướng dẫn sử dụng lần đầu

### 5.1. Chọn ngôn ngữ

Mở http://localhost:5173 — giao diện **mặc định là tiếng Nhật**. Đổi bằng ba nút
`JA / VI / EN`:

- **Chưa đăng nhập:** góc trên bên phải của trang đăng nhập / đăng ký.
- **Đã đăng nhập:** trên thanh header, cạnh nút đổi giao diện sáng/tối.

Lựa chọn được nhớ lại, mở trình duyệt lần sau vẫn đúng ngôn ngữ đó.

### 5.2. Tạo tài khoản

**Đăng ký** một tài khoản rồi đăng nhập để dùng đăng bài, follow, nhắn tin...

> Muốn xem ngay chức năng gợi ý công ty mà không phải tự nhập CV: dùng tài khoản
> `demo@fuurin.local` / `Demo@12345` tạo ở [Bước 5](#bước-5--tạo-tài-khoản-demo-khuyến-nghị).

### 5.3. Tạo tài khoản Admin

Dự án **không có sẵn** admin — mọi tài khoản đăng ký đều là `user` thường. Để có
quyền admin (quản lý user/bài viết, tuỳ biến website, **tạo channel**), nâng
quyền một tài khoản trong DB:

```bash
docker exec fuurin-mongo mongosh fuurin --quiet --eval '
  var adminRole = db.roles.findOne({value:1})._id;
  db.users.updateOne({email:"EMAIL_CUA_BAN"}, {$set:{role: adminRole}});
'
```

Thay `EMAIL_CUA_BAN` bằng email đã đăng ký. Sau đó **đăng xuất & đăng nhập lại**
để token nhận quyền mới → menu bên trái sẽ hiện mục **Quản trị**.

### 5.4. Tạo channel (kênh/nhóm)

Chỉ **admin** mới tạo được. Vào **Quản trị → Management → tab Channels → Add
Channel**. Điền tên (không trùng) và **nhớ upload ảnh Background** (bắt buộc,
thiếu sẽ lỗi).

### 5.5. Đăng bài, thích, bình luận

Vào **Channel** → tham gia một channel → đăng bài (có định dạng chữ và đính kèm
ảnh). Bài viết hiện trên bảng tin của những người cùng tham gia channel đó. Thích
và bình luận sẽ tạo **thông báo** cho tác giả.

### 5.6. Nhắn tin & gọi video

- Cần **2 tài khoản** để thử: mở thêm một **cửa sổ ẩn danh** rồi đăng ký/đăng
  nhập tài khoản thứ hai.
- Từ tài khoản này tìm tài khoản kia → nhắn tin hoặc bấm gọi video.
- Trình duyệt sẽ xin quyền **camera + micro** → bấm **Allow** (chạy ở localhost
  nên hợp lệ).

### 5.7. Tìm việc làm

Vào **Tin tuyển dụng** — tin từ DaiJob, GaijinPot, Nihongo Engineer và LinkedIn
JP đã được chuẩn hoá về cùng một dạng: tìm theo từ khoá, lọc theo **trình độ
tiếng Nhật**, mức lương, tỉnh/thành, việc remote.

### 5.8. Gợi ý công ty phù hợp với CV

1. Điền CV ở trang **Hồ sơ CV**. Nhớ mục **Mục tiêu nghề nghiệp** (trình độ tiếng
   Nhật, số năm kinh nghiệm, lương và địa điểm mong muốn) — để trống thì hệ thống
   tự suy ra từ phần Languages, Experiences và Certificates.
2. Vào **Công ty phù hợp** → danh sách công ty kèm điểm và lý do.

### 5.9. Xem mình còn thiếu gì

Ở mỗi công ty bấm **"Tôi còn thiếu gì để vào công ty này"**. Kết quả chia ba nhóm:
**bắt buộc phải bù** (ví dụ tiếng Nhật chưa đủ mức), **nên có thêm** (kỹ năng,
lương, địa điểm), và **bạn đã đáp ứng**.

### 5.10. Xem học thêm cái gì thì lợi nhất

Vào **Nếu tôi học thêm**. Màn hình liệt kê các phương án đã xếp theo lợi ích —
mỗi dòng cho biết **mở thêm bao nhiêu tin** và **trung vị lương của nhóm tin
đó**. Tick vài ô để xem kết quả khi làm đồng thời.

> Con số kết hợp **không bằng** tổng của từng mục lẻ, và có thể lớn hơn *hoặc*
> nhỏ hơn. Màn hình tự giải thích chiều đang xảy ra. Xem
> [docs/10](docs/10-mo-phong-doi-chung.md) nếu muốn hiểu vì sao.

### 5.11. Xem toàn cảnh thị trường

Vào **Bản đồ thị trường**: kỹ năng được săn nhiều nhất, phân bố yêu cầu tiếng
Nhật, nơi làm việc — kèm mức lương của từng nhóm. Mọi trung vị đều hiện cỡ mẫu
`n`, và nhóm dưới 10 tin ghi lương thì không hiện trung vị.

---

## 6. Các lệnh Docker hữu ích

```bash
docker compose up -d --build    # build & chay (lan dau / sau khi sua Dockerfile)
docker compose up -d            # chay lai (khong build lai)
docker compose ps               # xem trang thai cac container
docker compose logs -f          # xem log tat ca service
docker compose logs -f server   # xem log rieng backend
docker compose logs -f embedder # xem log service tinh vector
docker compose restart server   # khoi dong lai backend
docker compose down             # dung tat ca (GIU LAI du lieu DB)
docker compose down -v          # dung + XOA SACH du lieu DB
```

---

## 7. Biến môi trường

**Chạy dev bình thường thì không cần đặt gì** — `docker-compose.yml` đã có sẵn
giá trị mặc định.

Chỉ khi muốn dùng **secret riêng** (ví dụ deploy production), tạo file `.env` ở
thư mục gốc:

```bash
cp .env.example .env
```

| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `ACCESS_TOKEN_SECRET` | `secret` | Chuỗi bí mật ký JWT access token |
| `REFRESH_TOKEN_SECRET` | = access secret | Chuỗi bí mật ký JWT refresh token |
| `REDIS_URL` | trống | Nơi lưu blacklist token + bộ đếm rate limit. Trống = dùng RAM tiến trình (mất khi restart) |
| `ACCESS_TOKEN_TTL_SECONDS` | `900` (15 phút) | Hạn access token |
| `REFRESH_TOKEN_TTL_SECONDS` | `604800` (7 ngày) | Hạn refresh token |
| `COOKIE_SECURE` | `false` | Đặt `true` khi chạy sau HTTPS |
| `COOKIE_SAMESITE` | `lax` | Xem lưu ý bên dưới nếu deploy hai domain khác nhau |
| `LOGIN_FAIL_LIMIT_PER_EMAIL` | `10` | Số lần đăng nhập SAI cho một email trong 15 phút |
| `LOGIN_FAIL_LIMIT_PER_IP` | `30` | Số lần đăng nhập SAI từ một IP trong 15 phút |
| `REGISTER_RATE_LIMIT_MAX` | `60` | Số lần đăng ký / giờ / IP |
| `EMBEDDER_URL` | `http://embedder:8001` | Service tính vector. **Để trống thì hệ thống tự chuyển sang chấm điểm thuần luật**, không báo lỗi |
| `CRAWL_CACHE_TTL_SECONDS` | `600` | Hạn cache kết quả crawl |
| `CRAWL_MAX_CONCURRENT_PAGES` | `2` | Số trang mở đồng thời khi crawl |
| `TRUST_PROXY_HEADERS` | `false` | Chỉ bật khi thật sự có reverse proxy. Bật mà không có proxy thì ai cũng giả được `X-Forwarded-For` để qua mặt giới hạn theo IP |
| `CLIENT_URL` | `http://localhost:5173` | Danh sách origin được phép gọi API, phân tách bằng dấu phẩy |

Phía frontend, `client/.env`:

| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `VITE_BACKEND_URL` | `http://localhost:3000` | Địa chỉ backend mà trình duyệt gọi tới |

> **Lưu ý khi deploy frontend và backend trên hai domain khác nhau:** refresh
> token nằm trong cookie, và cookie `SameSite=lax` **không** được trình duyệt gửi
> kèm request cross-site. Khi đó phải đặt `COOKIE_SAMESITE=none` **và**
> `COOKIE_SECURE=true` — mà `SameSite=None` chỉ hợp lệ trên HTTPS. Chạy ở
> localhost (`:5173` gọi `:3000`) là cùng site nên mặc định `lax` hoạt động bình thường.

Tạo secret mạnh:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

> File `.env` đã được `.gitignore` — **không bao giờ commit** secret lên git.

---

## 8. Xử lý sự cố

| Triệu chứng | Nguyên nhân & cách khắc phục |
|---|---|
| `port is already allocated` / cổng bị chiếm | Có tiến trình khác đang dùng cổng 3000/5173/27017. Dừng nó, hoặc `docker compose down` các dự án khác. |
| Đăng ký lỗi `Cannot read properties of null` | DB chưa có dữ liệu roles. Chạy lại `docker compose up` (seed tự động), hoặc nạp thủ công như mục 4.1. |
| Không thấy mục Quản trị | Chưa nâng quyền, hoặc chưa đăng nhập lại sau khi nâng. Xem mục 5.3. |
| Tạo channel bị lỗi 500 | Chưa upload ảnh Background. Xem mục 5.4. |
| Crawl trả về rỗng | Trang nguồn có thể đã đổi giao diện (cần cập nhật selector), hoặc mạng chậm/timeout. |
| Đăng nhập báo *"Bạn thao tác quá nhiều lần"* (429) | Đã sai mật khẩu quá 10 lần cho cùng một email. Chờ 15 phút, hoặc `docker exec fuurin-redis redis-cli FLUSHDB` khi đang dev. |
| Đăng nhập báo *"Email hoặc mật khẩu không đúng!"* dù email chưa đăng ký | Cố ý: một thông báo duy nhất cho mọi trường hợp để không lộ email nào đã tồn tại. |
| Trang Tin tuyển dụng trống | Chưa nạp dữ liệu việc làm. Xem [Bước 4](#bước-4--nạp-dữ-liệu-việc-làm). |
| Vào **Công ty phù hợp** báo *"Bạn cần tạo CV trước"* | Đúng như thiết kế — điền CV ở trang Hồ sơ CV rồi quay lại. |
| Có dòng *"Đang xếp hạng bằng luật"* ở trang gợi ý | Service `embedder` chưa sẵn sàng hoặc CV chưa có vector. Kết quả vẫn dùng được. Chạy `docker compose ps` xem embedder đã healthy chưa, rồi `docker compose run --rm server python -m scripts.backfill_resumes`. |
| Bị đăng xuất sau ~15 phút | Client phải gọi được `POST /api/users/refresh`. Kiểm tra `CLIENT_URL` có đúng origin đang dùng và xem lưu ý SameSite ở mục 7. |
| Giao diện hiện chữ lạ kiểu `actions.search` | Một khoá dịch bị thiếu. Chạy `cd client && npm run check:i18n` để biết thiếu khoá nào ở ngôn ngữ nào. |
| Đổi ngôn ngữ mà một vài chỗ không đổi theo | Component đó nhớ kết quả cũ. Tải lại trang (F5); nếu vẫn còn thì đó là lỗi, xem [docs/09](docs/09-da-ngon-ngu.md). |

---

## 9. Chạy test

### 9.1. Test backend & giao diện (chạy trong Docker)

Không cần cài gì trên máy. Stack phải đang chạy (`docker compose up -d`).

```bash
# Test API (329 test: auth/refresh token, rate limit, phan quyen, post, channel,
# chat + phan trang, upload, socket, ETL/parser (chay offline tren HTML da luu),
# loi cham diem CV, API viec lam & goi y, dem so query chong N+1, hop dong
# response, va doi chieu ma thong bao cua backend voi ban dich cua client)
docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm api-tests

# Test E2E qua giao dien that bang Playwright (15 test, gom ca test doi ngon ngu)
docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm e2e-tests

# Chay xong E2E, tra client ve cau hinh thuong de dung tu trinh duyet:
docker compose up -d client

# Canh selector cua 4 trang nguon (can internet, mo browser Playwright).
# Do o day = trang nguon doi giao dien, KHONG phai code hong.
docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm \
  -e RUN_CRAWL_TESTS=1 api-tests python -m pytest tests/test_crawl_live.py
```

> Lệnh E2E dựng lại container `client` để frontend gọi `http://server:3000`
> (trình duyệt chạy bên trong docker network, `localhost` ở đó là chính container
> trình duyệt). Vì vậy sau khi test xong cần `docker compose up -d client` để
> quay lại `http://localhost:3000`.

Ảnh chụp màn hình của mỗi test E2E được lưu ở `e2e/artifacts/`.

Test E2E **không chép tay** câu chữ tiếng Nhật — nó đọc thẳng từ file dịch, nên
một màn hình quên gọi hàm dịch sẽ không lọt qua được.

### 9.2. Kiểm tra chất lượng mã nguồn

```bash
# Frontend: ESLint + doi chieu ban dich 3 ngon ngu
cd client && npm run lint

# Chi doi chieu ban dich (nhanh hon)
cd client && npm run check:i18n

# Backend: ruff — chay o THU MUC GOC du an, dung lenh y het CI
pip install ruff==0.15.1
ruff check        server_python/app server_python/scripts server_python/tests embedder e2e --config server_python/pyproject.toml
ruff format --check server_python/app server_python/scripts server_python/tests embedder e2e --config server_python/pyproject.toml
```

> **Phải chạy ruff từ thư mục gốc dự án.** Chạy từ trong `server_python/` sẽ báo
> 11 lỗi sắp xếp import không có thật, vì ruff nhận diện đâu là thư viện nội bộ
> dựa trên thư mục đang đứng.

`npm run check:i18n` kiểm **4 việc**: ba ngôn ngữ có đủ khoá như nhau; các tham
số trong câu (`{{count}}`, `{{name}}`) khớp nhau; khoá có số đếm phải có đủ dạng
số ít / số nhiều; và **mọi khoá được gọi trong mã nguồn đều phải tồn tại thật**.

ESLint có rule chặn **viết chữ hiển thị thẳng vào giao diện** — bắt buộc phải đi
qua hàm dịch, để i18n không mục dần theo từng lần sửa code.

### 9.3. CI

`.github/workflows/ci.yml` chạy tự động khi push/PR vào `main`:

- **lint** — `ruff check` + `ruff format --check`
- **test** — dựng stack bằng Docker rồi chạy test API và E2E; fail thì upload
  ảnh chụp màn hình + log backend

Trong bước **test**, CI nạp dữ liệu việc làm từ HTML đã lưu ở
`server_python/tests/fixtures/` (không cần mạng) trước khi chạy E2E — nếu không
thì các test về trang việc làm và gợi ý công ty sẽ bị bỏ qua và CI không thật sự
kiểm được hai chức năng đó.

Test crawl nằm ở workflow **riêng** (`crawl-health.yml`), chạy tự động 03:00 UTC
thứ Hai hàng tuần. Tách riêng vì nó gọi ra trang thật — LinkedIn hay chặn tạm
thời khi bị gọi liên tục, và nếu để chung với CI thì một lần bị chặn sẽ làm badge
CI đỏ trong khi code không sao. Badge *Crawl health* đỏ nghĩa là **selector có
thể đã mục rữa**, không phải code hỏng.

CI cũng có bước **smoke test browser** chạy mọi lần: nó gọi đúng hàm crawl dùng
thật với một trang `data:` (không cần mạng), để bảo vệ quyết định chỉ tải
`chromium-headless-shell` trong image.

---

## 10. Cấu trúc thư mục

```
.
├── client/                   # Frontend React + Vite
│   ├── src/
│   │   ├── i18n/             # Da ngon ngu
│   │   │   ├── config.js     #   khoi tao i18next, ngon ngu mac dinh = ja
│   │   │   └── locales/      #   ja/ vi/ en/ x 12 nhom chu (460 khoa moi ngon ngu)
│   │   ├── layouts/home/Recruitment/  # Tim viec lam (doc tu DB da ETL)
│   │   ├── layouts/home/Match/        # Goi y cong ty + thieu sot + mo phong doi chung
│   │   ├── layouts/home/Market/       # Ban do thi truong viec lam
│   │   ├── components/common/LanguageSwitcher.jsx  # nut JA / VI / EN
│   │   └── services/redux/query/baseQuery.js  # tu gia han access token khi 401
│   ├── scripts/check-i18n.mjs # Doi chieu ban dich 3 ngon ngu (chay trong npm run lint)
│   └── vite-plugin-i18n-resources.js # Gom 36 file dich thanh 1 module
├── server_python/            # Backend FastAPI (dang dung)
│   ├── app/
│   │   ├── config/           # settings, ket noi MongoDB, ket noi Redis
│   │   ├── controllers/      # Xu ly logic nghiep vu (raise ApiError, khong tu bat Exception)
│   │   ├── errors.py         # Bat loi tap trung -> {error, success, message, code}
│   │   ├── messages.py       # Danh muc ma thong bao (client dich theo `code`)
│   │   ├── middleware/       # auth (JWT), upload file
│   │   ├── models/           # Beanie Document (schema MongoDB)
│   │   ├── routes/           # Dinh nghia API + response_model
│   │   ├── schemas/          # Pydantic cho request & response (sinh /docs)
│   │   ├── services/         # browser dung chung, rate limit, blacklist token,
│   │   │   ├── etl/          #   crawl -> parse -> chuan hoa (4 parser + tu dien ky nang)
│   │   │   ├── matching.py   #   cham diem CV <-> tin tuyen dung, liet ke thieu sot
│   │   │   ├── whatif.py     #   mo phong "neu CV co them X" tren toan kho tin
│   │   │   ├── market.py     #   thong ke nhu cau ky nang / luong, co nguong co mau
│   │   │   ├── embedding.py  #   goi service embedder (suy giam em khi no chet)
│   │   │   └── job_index.py  #   chi muc vector trong bo nho (numpy, khong can vector DB)
│   │   ├── sockets/          # Socket.io handler (chat, video call)
│   │   ├── utils/            # loaders (chong N+1), token, cookie, serialize, quyen
│   │   └── main.py           # Khoi tao FastAPI + Socket.io
│   ├── data/skills.json      # Tu dien ~135 ky nang + alias (thay cho LLM khi trich ky nang)
│   ├── tests/                # Test API + test ETL chay offline
│   │   └── fixtures/         #   HTML that da luu -> test parser khong can mang
│   ├── scripts/              # run_etl, seed_jobs_from_fixtures, seed_resumes,
│   │                         # seed_demo_user, backfill_resumes, browser_smoke
│   ├── data/                 # Du lieu seed (roles, website)
│   ├── public/               # File tinh + file upload
│   └── Dockerfile
├── embedder/                 # Service tinh vector ngu nghia (fastembed/ONNX)
├── server/                   # Backend Express cu (tham chieu, khong con build)
├── e2e/                      # Test E2E Playwright
├── docs/                     # Tai lieu chi tiet (9 bai, viet cho nguoi moi)
├── docker/mongo-init/        # Script tu seed DB
├── docker-compose.yml        # Chay toan bo du an
├── docker-compose.test.yml   # Chay test
└── .env.example              # Mau bien moi truong (tuy chon)
```

**Công nghệ dùng trong dự án:**

| Phần | Công nghệ |
|---|---|
| `client` | React 18 + Vite + Redux Toolkit + Tailwind + Socket.io + WebRTC (simple-peer) + **react-i18next** |
| `server_python` | Python 3.12 + FastAPI + MongoDB (Beanie) + Redis + Socket.io + Playwright ← **backend đang dùng** |
| `embedder` | fastembed / ONNX Runtime (chạy CPU, không cần GPU, **không tốn phí API**) |
| `server` | Node.js + Express (bản cũ, giữ lại tham chiếu, không còn được compose build) |
| Hạ tầng | Docker Compose — MongoDB + Redis + embedder + backend + frontend |

---

## 11. Tài liệu chi tiết

README này chỉ hướng dẫn **cài đặt và chạy**. Muốn hiểu hệ thống hoạt động thế
nào, hoặc muốn tự thêm chức năng, đọc thư mục **[`docs/`](docs/README.md)** —
viết cho người chưa quen lập trình web, giải thích từng khái niệm trước khi dùng:

| | |
|---|---|
| [1. Hệ thống hoạt động thế nào](docs/01-he-thong-hoat-dong-the-nao.md) | Bấm một nút thì chuyện gì xảy ra |
| [2. Tạo một API mới](docs/02-tao-mot-api-moi.md) | 5 file cần viết, theo thứ tự nào |
| [3. Tạo một màn hình mới](docs/03-tao-mot-man-hinh-moi.md) | Từ khai báo API tới component và menu |
| [4. Luồng đăng nhập](docs/04-luong-dang-nhap.md) | Token, cookie, gia hạn tự động |
| [5. Luồng bài viết](docs/05-luong-bai-viet.md) | Đăng bài, thích, bình luận, chat thời gian thực |
| [6. Luồng CV và việc làm](docs/06-luong-cv-va-viec-lam.md) | ETL: crawl → chuẩn hoá → 430 tin |
| [7. Embedding và gợi ý công ty](docs/07-embedding-va-goi-y.md) | Phần AI: máy "hiểu" CV kiểu gì |
| [8. Lỗi, log và kiểm thử](docs/08-loi-log-va-kiem-thu.md) | Có sự cố thì tra ở đâu |
| [9. Đa ngôn ngữ](docs/09-da-ngon-ngu.md) | Giao diện Nhật · Việt · Anh: thêm chữ mới ở đâu |
| [10. Mô phỏng đối chứng](docs/10-mo-phong-doi-chung.md) | "Học thêm X thì mở ra bao nhiêu cơ hội" tính thế nào |
