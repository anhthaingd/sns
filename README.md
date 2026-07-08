# Fuurin — Mạng xã hội tuyển dụng

Ứng dụng full-stack (MERN) kết hợp mạng xã hội + nhắn tin/gọi video thời gian thực + sàn tổng hợp việc làm tại Nhật Bản.

**Công nghệ:**
- **client** — React + Vite + Redux Toolkit + Socket.io + WebRTC (simple-peer)
- **server** — Node.js + Express + MongoDB (Mongoose) + Socket.io + Puppeteer
- **hạ tầng** — Docker Compose (MongoDB + backend + frontend)

**Tính năng chính:** đăng ký/đăng nhập (JWT), đăng bài, kênh/nhóm, follow, thông báo, nhắn tin & gọi video 1-1, tạo CV, tổng hợp tin tuyển dụng (crawl), trang quản trị.

---

## 1. Yêu cầu cài đặt

Chỉ cần **một trong hai**:

- **Cách A (khuyên dùng): Docker** — cài [Docker Desktop](https://www.docker.com/products/docker-desktop/) hoặc [OrbStack](https://orbstack.dev/). Không cần cài Node hay MongoDB.
- **Cách B: Thủ công** — cài [Node.js](https://nodejs.org/) 18+ và [MongoDB](https://www.mongodb.com/try/download/community) 6+.

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
- Build & chạy **backend** (kèm sẵn trình duyệt Chrome cho chức năng crawl)
- Build & chạy **frontend**

> Lần đầu sẽ hơi lâu (vài phút) vì phải tải image và cài dependencies. Các lần sau rất nhanh.

### Bước 3 — Mở ứng dụng

| Thành phần | Địa chỉ |
|---|---|
| **Ứng dụng (mở cái này)** | http://localhost:5173 |
| Backend API | http://localhost:3000 |
| MongoDB | mongodb://localhost:27017/fuurin |

Xong! Chuyển sang [mục 4 — Hướng dẫn sử dụng](#4-hướng-dẫn-sử-dụng-lần-đầu).

---

## 3. Chạy thủ công (không dùng Docker)

<details>
<summary>Bấm để xem hướng dẫn chi tiết</summary>

### 3.1. Chuẩn bị MongoDB

Đảm bảo MongoDB đang chạy ở `mongodb://127.0.0.1:27017`. Sau đó nạp dữ liệu khởi tạo:

```bash
mongoimport --db fuurin --collection roles --jsonArray --drop --file server/data/roles.json
mongoimport --db fuurin --collection webs  --jsonArray --drop --file server/data/social_app.webs.json
```

### 3.2. Backend

```bash
cd server
cp .env.example .env      # xem mục 6 de dien cac bien
# Sua .env: dien DATABASE_URL=mongodb://127.0.0.1:27017/fuurin
npm install
npm run dev               # chay tai http://localhost:3000
```

### 3.3. Frontend

Mở terminal khác:

```bash
cd client
npm install
npm run dev               # chay tai http://localhost:5173
```

> **Lưu ý:** biến kết nối DB trong code tên là `DATABASE_URL` (không phải `DATABASE_NAME`). Client đọc backend qua `client/.env` (`VITE_BACKEND_URL`).
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
node -e "console.log(require('crypto').randomBytes(48).toString('base64url'))"
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

## 8. Cấu trúc thư mục

```
.
├── client/              # Frontend React + Vite
├── server/              # Backend Express
│   ├── controllers/     # Xu ly logic
│   ├── models/          # Schema MongoDB
│   ├── routes/          # Dinh nghia API
│   ├── data/            # Du lieu seed (roles, website)
│   └── Dockerfile
├── docker/mongo-init/   # Script tu seed DB
├── docker-compose.yml   # Chay toan bo du an
└── .env.example         # Mau bien moi truong (tuy chon)
```
