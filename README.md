# Fuurin — Mạng xã hội tuyển dụng

[![CI](https://github.com/anhthaingd/sns/actions/workflows/ci.yml/badge.svg)](https://github.com/anhthaingd/sns/actions/workflows/ci.yml)

Ứng dụng full-stack kết hợp mạng xã hội + nhắn tin/gọi video thời gian thực + sàn tổng hợp việc làm tại Nhật Bản.

**Công nghệ:**
- **client** — React + Vite + Redux Toolkit + Socket.io + WebRTC (simple-peer)
- **server_python** — Python + FastAPI + MongoDB (Beanie/pymongo) + Socket.io + Playwright  ← **backend đang dùng**
- **server** — Node.js + Express (bản cũ, giữ lại để tham chiếu, không còn được compose build)
- **hạ tầng** — Docker Compose (MongoDB + backend + frontend)

**Tính năng chính:** đăng ký/đăng nhập (JWT), đăng bài, kênh/nhóm, follow, thông báo, nhắn tin & gọi video 1-1, tạo CV, tổng hợp tin tuyển dụng (crawl), trang quản trị.

---

## 1. Yêu cầu cài đặt

Chỉ cần **một trong hai**:

- **Cách A (khuyên dùng): Docker** — cài [Docker Desktop](https://www.docker.com/products/docker-desktop/) hoặc [OrbStack](https://orbstack.dev/). Không cần cài Python, Node hay MongoDB.
- **Cách B: Thủ công** — cài [Python](https://www.python.org/downloads/) 3.12+, [Node.js](https://nodejs.org/) 18+ và [MongoDB](https://www.mongodb.com/try/download/community) 6+.

---

## 2. Chạy dự án bằng Docker (khuyên dùng)

### Bước 1 — Lấy mã nguồn

```bash
git clone https://github.com/anhthaingd/sns.git
cd sns
```

### Bước 2 — Chạy toàn bộ bằng MỘT lệnh

```bash
docker compose up -d --build
```

Lệnh này tự động:
- Khởi động **MongoDB** và **nạp sẵn** dữ liệu roles + cấu hình website
- Build & chạy **backend FastAPI** (kèm sẵn Chromium của Playwright cho chức năng crawl)
- Build & chạy **frontend**

> Lần đầu sẽ hơi lâu (vài phút) vì phải tải image và cài dependencies. Các lần sau rất nhanh.

### Bước 3 — Mở ứng dụng

| Thành phần | Địa chỉ |
|---|---|
| **Ứng dụng (mở cái này)** | http://localhost:5173 |
| Backend API | http://localhost:3000 |
| API docs (Swagger) | http://localhost:3000/docs |
| Health check | http://localhost:3000/health |
| MongoDB | mongodb://localhost:27017/fuurin |

Xong! Chuyển sang [mục 4 — Hướng dẫn sử dụng](#4-hướng-dẫn-sử-dụng-lần-đầu).

---

## 3. Chạy thủ công (không dùng Docker)

<details>
<summary>Bấm để xem hướng dẫn chi tiết</summary>

### 3.1. Chuẩn bị MongoDB

Đảm bảo MongoDB đang chạy ở `mongodb://127.0.0.1:27017`. Sau đó nạp dữ liệu khởi tạo:

```bash
mongoimport --db fuurin --collection roles --jsonArray --drop --file server_python/data/roles.json
mongoimport --db fuurin --collection webs  --jsonArray --drop --file server_python/data/social_app.webs.json
```

### 3.2. Backend (Python / FastAPI)

```bash
cd server_python
cp .env.example .env          # xem muc 6 de dien cac bien
# Sua .env: DATABASE_URL=mongodb://127.0.0.1:27017/fuurin

python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
playwright install chromium   # trinh duyet cho chuc nang crawl

uvicorn app.main:socket_app --reload --port 3000
```

### 3.3. Frontend

Mở terminal khác:

```bash
cd client
npm install
npm run dev               # chay tai http://localhost:5173
```

> **Lưu ý:** biến kết nối DB tên là `DATABASE_URL`. Client đọc backend qua `client/.env` (`VITE_BACKEND_URL`).
</details>

---

## 4. Hướng dẫn sử dụng lần đầu

### 4.1. Tạo tài khoản
Mở http://localhost:5173 → **Đăng ký** một tài khoản. Đăng nhập để dùng đăng bài, follow, nhắn tin...

### 4.2. Tạo tài khoản Admin
Dự án **không có sẵn** admin — mọi tài khoản đăng ký đều là `user` thường. Để có quyền admin (quản lý user/bài viết, tùy biến website, **tạo channel**), nâng quyền một tài khoản trong DB:

```bash
docker exec fuurin-mongo mongosh fuurin --quiet --eval '
  var adminRole = db.roles.findOne({value:1})._id;
  db.users.updateOne({email:"EMAIL_CUA_BAN"}, {$set:{role: adminRole}});
'
```

Thay `EMAIL_CUA_BAN` bằng email đã đăng ký. Sau đó **đăng xuất & đăng nhập lại** để token nhận quyền mới → menu bên trái sẽ hiện mục **Admin**.

### 4.3. Tạo channel (kênh/nhóm)
Chỉ **admin** mới tạo được. Vào **Admin → Management → tab Channels → Add Channel**. Điền tên (không trùng) và **nhớ upload ảnh Background** (bắt buộc, nếu thiếu sẽ lỗi).

### 4.4. Nhắn tin & gọi video
- Cần **2 tài khoản** để thử: mở thêm một **cửa sổ ẩn danh** và đăng ký/đăng nhập tài khoản thứ hai.
- Từ tài khoản này tìm tài khoản kia → nhắn tin hoặc bấm gọi video.
- Trình duyệt sẽ xin quyền **camera + micro** → bấm **Allow** (chạy ở localhost nên hợp lệ).
- Gọi video dùng WebRTC + STUN công cộng của Google — **không cần API key trả phí**.

### 4.5. Xem tin tuyển dụng (crawl)
Vào trang **Recruitment** — hệ thống tự tổng hợp tin từ DaiJob, GaijinPot, Nihongo Engineer, LinkedIn JP.

---

## 5. Các lệnh Docker hữu ích

```bash
docker compose up -d --build    # build & chay (lan dau / sau khi sua Dockerfile)
docker compose up -d            # chay lai (khong build lai)
docker compose ps               # xem trang thai cac container
docker compose logs -f          # xem log tat ca service
docker compose logs -f server   # xem log rieng backend
docker compose restart server   # khoi dong lai backend
docker compose down             # dung tat ca (GIU LAI du lieu DB)
docker compose down -v          # dung + XOA SACH du lieu DB
```

---

## 6. Biến môi trường

**Chạy dev bình thường thì không cần đặt gì** — `docker-compose.yml` đã có sẵn giá trị mặc định.

Chỉ khi muốn dùng **secret riêng** (ví dụ deploy production), tạo file `.env` ở thư mục gốc:

```bash
cp .env.example .env
```

| Biến | Ý nghĩa |
|---|---|
| `ACCESS_TOKEN_SECRET` | Chuỗi bí mật ký JWT access token |
| `REFRESH_TOKEN_SECRET` | Chuỗi bí mật ký JWT refresh token |

Tạo secret mạnh:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

> File `.env` đã được `.gitignore` — **không bao giờ commit** secret lên git.

---

## 7. Xử lý sự cố

| Triệu chứng | Nguyên nhân & cách khắc phục |
|---|---|
| `port is already allocated` / cổng bị chiếm | Có tiến trình khác đang dùng cổng 3000/5173/27017. Dừng nó, hoặc `docker compose down` các dự án khác. |
| Đăng ký lỗi `Cannot read properties of null` | DB chưa có dữ liệu roles. Chạy lại `docker compose up` (seed tự động), hoặc nạp thủ công như mục 3.1. |
| Không thấy mục Admin | Chưa nâng quyền, hoặc chưa đăng nhập lại sau khi nâng. Xem mục 4.2. |
| Tạo channel bị lỗi 500 | Chưa upload ảnh Background. Xem mục 4.3. |
| Crawl trả về rỗng | Trang nguồn có thể đã đổi giao diện (cần cập nhật selector), hoặc mạng chậm/timeout. |

---

## 8. Chạy test

Test chạy trong Docker, không cần cài gì trên máy. Stack phải đang chạy (`docker compose up -d`).

```bash
# Test API (61 test: auth, phan quyen, post, channel, chat, upload, socket)
docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm api-tests

# Test crawl that (can internet, mo browser Playwright)
docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm -e RUN_CRAWL_TESTS=1 api-tests python -m pytest tests/test_crawl.py

# Test E2E qua giao dien that bang Playwright (8 test)
docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm e2e-tests

# Chay xong E2E, tra client ve cau hinh thuong de dung tu trinh duyet:
docker compose up -d client
```

> Lệnh E2E dựng lại container `client` để frontend gọi `http://server:3000` (trình duyệt
> chạy bên trong docker network, `localhost` ở đó là chính container trình duyệt).
> Vì vậy sau khi test xong cần `docker compose up -d client` để quay lại `http://localhost:3000`.

Ảnh chụp màn hình của mỗi test E2E được lưu ở `e2e/artifacts/`.

### CI

`.github/workflows/ci.yml` chạy tự động khi push/PR vào `main`:

- **lint** — `ruff check` + `ruff format --check`
- **test** — dựng stack bằng Docker rồi chạy test API và E2E; fail thì upload ảnh chụp màn hình + log backend

Test crawl **không** chạy trong CI vì phụ thuộc trang web bên ngoài (LinkedIn hay chặn tạm thời
khi bị gọi liên tục). Muốn chạy thì vào tab Actions → *CI* → **Run workflow** và bật
*Chay ca test crawl*.

---

## 9. Cấu trúc thư mục

```
.
├── client/                   # Frontend React + Vite
├── server_python/            # Backend FastAPI (dang dung)
│   ├── app/
│   │   ├── config/           # settings, ket noi MongoDB
│   │   ├── controllers/      # Xu ly logic nghiep vu
│   │   ├── middleware/       # auth (JWT), upload file
│   │   ├── models/           # Beanie Document (schema MongoDB)
│   │   ├── routes/           # Dinh nghia API
│   │   ├── sockets/          # Socket.io handler (chat, video call)
│   │   ├── utils/            # token, serialize, xoa file
│   │   └── main.py           # Khoi tao FastAPI + Socket.io
│   ├── tests/                # Test API (pytest + httpx)
│   ├── data/                 # Du lieu seed (roles, website)
│   ├── public/               # File tinh + file upload
│   └── Dockerfile
├── server/                   # Backend Express cu (tham chieu)
├── e2e/                      # Test E2E Playwright
├── docker/mongo-init/        # Script tu seed DB
├── docker-compose.yml        # Chay toan bo du an
├── docker-compose.test.yml   # Chay test
└── .env.example              # Mau bien moi truong (tuy chon)
```
