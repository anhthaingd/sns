# 15. Deploy miễn phí — nhật ký bản live hiện tại

> **Ngày hoàn thành:** 18/09/2026
> **Mục đích:** ghi lại *đúng những gì đã làm* để Fuurin chạy trên internet,
> từng nền tảng, từng nút bấm, từng biến môi trường. Bản rút gọn nằm ở
> [README mục 12](../README.md#12-deploy-miễn-phí-để-test). Bài này viết cho
> báo cáo: cần chi tiết hơn, kể cả chỗ đi lệch và chỗ đã sửa.

Không ghi mật khẩu, connection string đầy đủ, hay API key. Những chỗ đó chỉ
mô tả *dạng chuỗi* và *điền vào ô nào*.

---

## 15.1. Bản đang chạy (kết quả)

| Phần | URL / tên | Gói |
|---|---|---|
| Giao diện | https://fuurin-client.vercel.app | Vercel Hobby (free) |
| API + Socket.IO | https://fuurin-api-idhh.onrender.com | Render Web Service Free |
| MongoDB | Atlas cluster M0, region **Tokyo**, database **`fuurin`** | Atlas M0 (512 MB) |
| Redis | Upstash, region **ap-northeast** (Tokyo), URL dạng `rediss://…` | Upstash Free |
| Mã nguồn deploy | GitHub [`anhthaingd/sns`](https://github.com/anhthaingd/sns) nhánh `main`, commit cấu hình `0535d1f` | — |

Embedder **không** deploy. Crawl Playwright **không** chạy trên Render free.
Matching trên live đang chấm **thuần luật** (vẫn ra danh sách công ty).

Tài khoản demo đã nạp sẵn:

| Email | Mật khẩu | Dùng để |
|---|---|---|
| `demo@fuurin.local` | `Demo@12345` | Trần Minh Quân — Backend, N3, 4 năm, Tokyo |
| `demo-nojp@fuurin.local` | `Demo@12345` | Tài khoản đối chứng (không tiếng Nhật) + chat 2 người |
| `seed-000@seed.fuurin.local` … `seed-099@…` | `SeedPassw0rd!` | 100 CV mẫu để thử tìm người / follow |

---

## 15.2. Vì sao tách bốn nền tảng, không nhét hết vào một máy

Local (`docker compose up`) chạy **năm hộp** trên một máy: `client`, `server`,
`mongo`, `redis`, `embedder`. Gói miễn phí không cho một máy đủ RAM cho cả năm,
và mỗi hộp cần thứ khác nhau:

```
Trình duyệt
    │  HTTPS
    ▼
Vercel  (chỉ file tĩnh React sau khi build)
    │  REST + Socket.IO  (cross-origin)
    ▼
Render  uvicorn app.main:socket_app
    ├── MongoDB Atlas   (dữ liệu bền)
    └── Upstash Redis   (TLS)  — blacklist token + Socket.IO Redis manager
```

| Hộp local | Đưa lên đâu | Lý do chọn |
|---|---|---|
| `client` | Vercel | HTTPS sẵn, SPA, rebuild khi push GitHub, 0đ |
| `server` | Render | Web Service Python, **WebSocket thật** (không chỉ HTTP) |
| `mongo` | Atlas M0 | Có GUI xem collection — yêu cầu “xem được DB” |
| `redis` | Upstash | Redis TLS miễn phí, có dashboard |
| `embedder` | **Bỏ** | Image ~800MB+, Render free ~512MB RAM → OOM. Để trống `EMBEDDER_URL` thì app tự hạ cấp, không báo lỗi |

> 💡 **WebSocket là gì?** HTTP hỏi–đáp một lần rồi cắt. Chat realtime cần đường
> nối **giữ mở**. Socket.IO chạy trên đường đó. Host chỉ phục vụ file tĩnh
> (Vercel) không giữ nổi Socket.IO của Fuurin, nên phần realtime phải nằm ở
> Render.

Hai quyết định kỹ thuật bắt buộc, không được đổi:

1. Lệnh start backend phải là `app.main:socket_app`, **không** phải `app.main:app`.
   `app` chỉ có HTTP. `socket_app` mới bọc FastAPI **và** Socket.IO
   (`server_python/app/main.py`).
2. Frontend và backend khác domain nên cookie refresh token phải
   `COOKIE_SECURE=true` + `COOKIE_SAMESITE=none`, và CORS phải khớp đúng origin
   Vercel qua `CLIENT_URL`.

---

## 15.3. File trong repo phục vụ deploy

Các file này được thêm/sửa trước khi bấm nút trên dashboard (commit `0535d1f`
trên `sns`):

| File | Việc nó làm |
|---|---|
| [`render.yaml`](../render.yaml) | Blueprint Render: tên service, region Singapore, root `server_python`, start `socket_app`, health `/health`, danh sách biến |
| [`client/vercel.json`](../client/vercel.json) | Rewrite SPA: mọi đường (`/resume`, `/match`, …) trả về `index.html` |
| [`server_python/.python-version`](../server_python/.python-version) | Ép Python **3.12.8** lúc build trên Render |
| [`server_python/scripts/seed_required.py`](../server_python/scripts/seed_required.py) | Nạp `roles` + `webs` vào Atlas (bắt buộc trước khi đăng ký) |
| [`.env.example`](../.env.example) / [`server_python/.env.example`](../server_python/.env.example) | Ghi nhớ biến production, **không** chứa secret thật |
| [`.gitignore`](../.gitignore) | Có dòng `.deploy-secrets` — file local chứa connection string, không commit |

Nội dung `client/vercel.json` (cả file):

```json
{
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
```

Nội dung then chốt của `render.yaml`:

| Trường Blueprint | Giá trị đã đặt |
|---|---|
| `type` | `web` |
| `name` | `fuurin-api` (Render tự thêm hậu tố, service thật là `fuurin-api-idhh`) |
| `runtime` | `python` |
| `plan` | `free` |
| `region` | `singapore` |
| `rootDir` | `server_python` |
| `buildCommand` | `pip install -r requirements.txt` |
| `startCommand` | `uvicorn app.main:socket_app --host 0.0.0.0 --port $PORT` |
| `healthCheckPath` | `/health` |

Render **tự sinh** (không điền tay): `ACCESS_TOKEN_SECRET`,
`REFRESH_TOKEN_SECRET`, `MESSAGE_ENCRYPTION_KEY`.

Render **điền tay** (`sync: false`): `DATABASE_URL`, `REDIS_URL`, `CLIENT_URL`,
và tuỳ chọn `GEMINI_API_KEY`, `GROQ_API_KEY`.

---

## 15.4. Thứ tự bắt buộc

Làm ngược thứ tự này thì bước sau không có giá trị để dán:

```
1. GitHub sns đã push (Render/Vercel đọc code từ đây)
2. Atlas  → có DATABASE_URL
3. Upstash → có REDIS_URL
4. Render  → có URL API  (CLIENT_URL tạm để placeholder cũng được)
5. Vercel  → có URL frontend; biến VITE_BACKEND_URL = URL bước 4
6. Quay lại Render, sửa CLIENT_URL = URL bước 5, restart
7. Seed Atlas (roles, jobs, demo user)
8. Test trên trình duyệt
```

---

## 15.5. GitHub — nguồn duy nhất sau khi gắn lại

Máy local: thư mục `FinalProject_Fuurin`, remote `origin` =
`git@github.com:anhthaingd/sns.git`.

Lúc làm frontend, dashboard Vercel **đã có sẵn** project tên `fuurin-client`
gắn repo GitHub **khác**: `anhthaingd/fuurin-client` (bản copy “Initial commit”).
Hệ quả: sửa `sns` rồi push thì **frontend live không đổi**. Đã gắn lại (mục
15.9.6). Từ đó chỉ làm việc với `sns`.

Repo `anhthaingd/fuurin-client` trên GitHub **không còn dùng để deploy**. Có
thể để đó hoặc xoá/archive sau, không ảnh hưởng bản live.

---

## 15.6. MongoDB Atlas — từng nút

Mở https://cloud.mongodb.com và đăng nhập.

### 15.6.1. Cluster (lần này đã có sẵn)

Trên tài khoản này **cluster M0 Tokyo đã tồn tại** (tên trên UI: Cluster0 /
Fuurin). Không tạo cluster thứ hai (M0 chỉ một cluster/project).

Nếu làm từ số không, đường đi chuẩn:

1. Góc trên trái: chọn Organization → **Project** (hoặc **New Project**, đặt
   tên ví dụ `Fuurin`).
2. Màn Overview: nút **Create** / **Build a Database**.
3. Chọn gói **M0 Sandbox / Free**.
4. Provider: **AWS**.
5. Region: **Tokyo (`ap-northeast-1`)** — gần người dùng JP/VN hơn US.
6. Tên cluster: để `Cluster0` cũng được.
7. **Create Deployment** / **Create**. Chờ vài phút đến khi status **Idle**.

Project ID thực tế: `6aac9f201a669692ca14dd74` (nằm trên URL
`cloud.mongodb.com/v2/<projectId>`).

### 15.6.2. Database user (đã tạo user riêng cho app)

Menu trái: **Security → Database Access**.

Đã có user `anhthaingd_db_user`. **Tạo thêm** user app:

1. Nút **Add New Database User**.
2. Tab **Password** (Password Authentication).
3. Username: `fuurin`.
4. Password: bấm **Autogenerate Secure Password**, **copy ra chỗ an toàn**
   (Atlas không hiện lại mật khẩu sau này).
5. Database User Privileges: **Atlas admin** (hoặc Built-in Role
   `readWriteAnyDatabase` cũng đủ cho demo).
6. **Add User**.

### 15.6.3. Network Access — mở cho Render

Menu trái: **Security → Network Access**.

Render free **không có IP cố định**, nên:

1. **Add IP Address**.
2. Chọn **Allow Access From Anywhere** → CIDR `0.0.0.0/0`.
3. Comment tuỳ ý: `render-and-seed`.
4. **Confirm**.

> Đây là nới lỏng cho demo. User DB + mật khẩu vẫn bắt buộc. Không đưa
> connection string lên GitHub.

### 15.6.4. Connection string

1. Menu trái: **Database → Clusters**.
2. Trên thẻ cluster: nút **Connect**.
3. Chọn **Drivers** (không chọn Compass / Shell trừ khi cần).
4. Driver: Python, version 3.12 trở lên.
5. Copy chuỗi dạng:

```
mongodb+srv://fuurin:<PASSWORD>@cluster0.<xxxxx>.mongodb.net/?appName=Cluster0
```

6. **Sửa trước khi dùng:**
   - Thay `<PASSWORD>` bằng mật khẩu vừa copy (ký tự đặc biệt phải URL-encode:
     `@` → `%40`, `/` → `%2F`, …).
   - **Thêm tên database** `/fuurin` trước dấu `?`. App đọc tên DB từ path.
     Thiếu thì dễ rơi vào DB khác (`test` / `social_app`) — Explorer sẽ thấy
     collection trống dù đã seed.

Chuỗi đúng dạng:

```
mongodb+srv://fuurin:<PASSWORD>@cluster0.<xxxxx>.mongodb.net/fuurin?retryWrites=true&w=majority
```

Lưu local vào file **không commit** (repo đã ignore `.deploy-secrets`).

### 15.6.5. Xem dữ liệu (GUI)

1. Cluster → **Browse Collections** (hoặc menu **Data Explorer**).
2. Cột trái chọn database **`fuurin`** (không nhầm `admin` / `local`).
3. Sau khi seed (mục 15.11) sẽ thấy `roles`, `webs`, `jobs`, `companies`,
   `users`, `resumes`, `chats`, …

---

## 15.7. Upstash Redis — từng nút

Mở https://console.upstash.com → đăng nhập → mục **Redis**.

### 15.7.1. Tạo database

1. **Create Database**.
2. Name: `fuurin` (hoặc `fuurin-redis`).
3. Type: **Regional** (đủ cho demo; Global là trả phí hơn).
4. Region: **`ap-northeast-1` (Tokyo)** — cùng khu vực Atlas.
5. Eviction: bật (free tier đầy key thì xoá key cũ, Redis không sập).
6. **Create**.

### 15.7.2. Lấy URL TLS

Vào thẻ database vừa tạo. Tab **Details** / **Connect**:

- Copy **Redis URL**, protocol **`rediss://`** (hai chữ `s` = TLS).
- Dạng: `rediss://default:<TOKEN>@<host>.upstash.io:6379`.
- **Không** dùng `redis://` (không TLS) — Render kết nối ra internet, Upstash
  yêu cầu TLS.

Kiểm tra từ máy local (không in URL ra log công khai):

```bash
# redis-cli --tls -u 'rediss://default:...@....upstash.io:6379' PING
# Kỳ vọng: PONG
```

Redis trên live dùng cho: blacklist refresh token, rate limit, và
`AsyncRedisManager` của Socket.IO (`server_python/app/main.py`) để chat vẫn
tới đúng người khi process restart.

---

## 15.8. Backend trên Render — từng nút

Mở https://dashboard.render.com, đăng nhập bằng GitHub (cần quyền đọc repo
`anhthaingd/sns`).

### 15.8.1. Tạo service bằng Blueprint (cách đã dùng)

1. Góc trên: nút **New**.
2. Chọn **Blueprint** (không chọn Static Site).
3. Danh sách repo: tìm **`anhthaingd/sns`** → **Connect**.
   Nếu repo không hiện: **Configure account** / GitHub App → Grant access repo
   `sns` → quay lại.
4. Render đọc `render.yaml` ở **root repo**.
5. Ô **Blueprint Name** (bắt buộc, khác tên service): điền `fuurin-test`.
   Lần deploy thật đã kẹt ở đây vì nút Deploy bị disable khi ô này trống.
6. Bảng Environment: các biến `generateValue` để Render tự sinh. Các biến
   `sync: false` **phải gõ tay** trước khi Deploy:

| Key | Điền gì lúc tạo Blueprint |
|---|---|
| `DATABASE_URL` | Connection string Atlas đã sửa `/fuurin` |
| `REDIS_URL` | `rediss://…` từ Upstash |
| `CLIENT_URL` | Tạm `https://fuurin-client.vercel.app` nếu đã biết URL; chưa có Vercel thì điền placeholder rồi sửa sau |
| `GEMINI_API_KEY` | Tuỳ chọn — để trống thì thẻ “Gợi ý từ AI” tự ẩn |
| `GROQ_API_KEY` | Tuỳ chọn, fallback LLM |

Các biến Blueprint **đã ghi cứng trong yaml**, không cần gõ lại:

| Key | Giá trị |
|---|---|
| `PYTHON_VERSION` | `3.12.8` |
| `COOKIE_SECURE` | `true` |
| `COOKIE_SAMESITE` | `none` |
| `TRUST_PROXY_HEADERS` | `true` |
| `REGISTER_RATE_LIMIT_MAX` | `60` |

7. Instance type giữ **Free**.
8. Cảnh báo “1 warning” trên form (nếu có) không chặn deploy.
9. **Deploy Blueprint**.

Service tạo ra có slug `fuurin-api-idhh` vì tên `fuurin-api` đã bị service cũ
chiếm. **Chỉ dùng URL có `idhh`.** Service cũ `https://fuurin-api.onrender.com`
là HTTP-only: REST có thể 200, Socket.IO **404** — đã làm hỏng test chat lần
đầu (mục 15.13).

URL đúng:

```
https://fuurin-api-idhh.onrender.com
```

### 15.8.2. Cách tay nếu không dùng Blueprint

**New → Web Service →** Connect `anhthaingd/sns`:

| Ô trên form | Giá trị |
|---|---|
| Name | `fuurin-api` (hoặc để Render thêm hậu tố) |
| Region | **Singapore** |
| Branch | `main` |
| Root Directory | `server_python` |
| Runtime | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn app.main:socket_app --host 0.0.0.0 --port $PORT` |
| Instance type | **Free** |

Rồi **Environment → Add Environment Variable** từng dòng như bảng 15.8.1.
**Settings → Health Check Path** = `/health`.

### 15.8.3. Chờ build xong và kiểm tra

1. Vào service `fuurin-api-idhh` → tab **Logs** / **Events**.
2. Build pip xong, uvicorn lên, health check xanh.
3. Lần đầu trên free có thể 1–3 phút. Request đầu sau khi service **ngủ**
   (khoảng 15 phút không traffic) cũng mất ~30–60 giây.
4. Trình duyệt hoặc:

```bash
curl -sS https://fuurin-api-idhh.onrender.com/health
# {"status":"ok"}
```

5. Socket.IO (không phải REST):

```
GET https://fuurin-api-idhh.onrender.com/socket.io/?EIO=4&transport=polling
```

Phải **200**, không phải 404.

### 15.8.4. Sửa biến sau khi có URL Vercel

1. Service → **Environment**.
2. `CLIENT_URL` = `https://fuurin-client.vercel.app` — **không** slash cuối,
   **không** thêm preview URL trừ khi chủ đích nới CORS.
3. **Save Changes**. Free tier thường **tự deploy lại**. Nếu không: **Manual
   Deploy → Deploy latest commit**.

Kiểm tra CORS (từ máy):

```bash
curl -sI -X OPTIONS https://fuurin-api-idhh.onrender.com/api/jobs \
  -H 'Origin: https://fuurin-client.vercel.app' \
  -H 'Access-Control-Request-Method: GET'
```

Header phải có:

```
access-control-allow-origin: https://fuurin-client.vercel.app
access-control-allow-credentials: true
```

`CLIENT_URL` còn được Socket.IO dùng làm `cors_allowed_origins`. Sai origin
thì REST có thể chạy mà chat bị chặn.

---

## 15.9. Frontend trên Vercel — từng nút

Mở https://vercel.com → team `anhthaingd-1503`.

Project **tên** `fuurin-client`. URL production **không đổi theo tên repo**:

```
https://fuurin-client.vercel.app
```

### 15.9.1. Vì sao không import `sns` lần đầu

**Add New… → Project** → chọn `sns` → Project Name mặc định `fuurin-client`
→ lỗi:

> A project with the same name already exists

Nghĩa là **trùng tên project trên Vercel**, không phải `sns` không deploy
được. Đã dùng project sẵn có rồi gắn Git lại cho đúng.

### 15.9.2. Cấu hình Build (Settings → General / Build and Deployment)

| Ô | Giá trị bắt buộc |
|---|---|
| **Root Directory** | `client`  (nút Edit, gõ `client`, Save) |
| Framework Preset | Vite (thường tự nhận) |
| Build Command | `npm run build` |
| Output Directory | `dist` |
| Install Command | `npm install` (mặc định) |
| Node.js Version | 20.x hoặc 22.x (LTS) |
| Production Branch | `main` |

Thiếu Root Directory = `client` thì Vercel build nhầm thư mục gốc, không ra
app React.

### 15.9.3. Biến môi trường (Settings → Environment Variables)

Vite nhúng `VITE_*` **lúc build**, không lúc chạy. Sửa biến mà không Redeploy
thì file JS cũ vẫn gọi backend cũ.

1. **Add New**.
2. Key: `VITE_BACKEND_URL`
3. Value: `https://fuurin-api-idhh.onrender.com` — **không** slash cuối.
4. Environment: tick **Production** (và Preview nếu muốn preview cùng API;
   preview khác origin thì Render `CLIENT_URL` phải chứa origin đó, nếu không
   CORS chặn — đã xảy ra với URL `fuurin-client-….vercel.app`).
5. **Save**.
6. **Deployments →** bản Production mới nhất → **Redeploy** (không dùng cache
   nếu vừa đổi biến).

Sai URL từng gặp: `https://fuurin-api.onrender.com` (thiếu `idhh`) → REST tạm
ổn, Socket.IO 404, chat không lưu.

### 15.9.4. Rewrite SPA (`vercel.json`)

React Router dùng đường `/resume`, `/match`, `/recruitment`, … Chỉ có **một**
file `index.html` trên Vercel.

- Bấm menu trong app: React đổi URL, **không** hỏi Vercel file `/resume`.
- Gõ `https://fuurin-client.vercel.app/resume` hoặc F5: Vercel bị hỏi file
  `/resume`. Không có rewrite → **404**. Có `client/vercel.json` như mục 15.3
  → 200, title `Fuurin`.

File này phải nằm **trong thư mục Root Directory** (`client/`), không phải
root repo.

### 15.9.5. Lần đầu rewrite chạy trên repo nhầm

Khi Vercel còn gắn `anhthaingd/fuurin-client`, file `vercel.json` chỉ có trên
`sns` nên `/resume` vẫn 404. Đã commit `client/vercel.json` **thẳng vào main
của repo `fuurin-client`** (commit `ec60b38`) để bản live hết 404. Cách làm đó
không khớp quy trình “sửa local `sns` rồi push”. Đã sửa nguồn Git (bước dưới)
để không lặp lại.

### 15.9.6. Gắn lại Git về `sns` (cấu hình đúng hiện tại)

1. Project `fuurin-client` → **Settings → Git**.
2. **Disconnect** repo `anhthaingd/fuurin-client` → confirm **Remove Git
   Connection**.
3. **Connect Git Repository → GitHub** → chọn **`anhthaingd/sns`** → Connect.
4. **Settings → Build and Deployment**: kiểm tra **Root Directory** vẫn là
   `client`.
5. **Deployments → Create Deployment**:
   - Branch `main` (hoặc commit `0535d1f`).
   - **Deploy to Production** (không chỉ Preview).
6. Chờ status **Ready**.

Từ đây: sửa trong Cursor → `git push origin main` trên `sns` → Vercel tự
build `client/`. Không đụng repo GitHub `fuurin-client` nữa.

### 15.9.7. Kiểm tra frontend

| Thử | Kỳ vọng |
|---|---|
| https://fuurin-client.vercel.app | Trang login Fuurin |
| https://fuurin-client.vercel.app/resume (gõ thẳng / F5) | 200, không 404 |
| DevTools → Network | API gọi `fuurin-api-idhh.onrender.com`, không gọi `fuurin-api.onrender.com` |
| Socket.IO handshake | 200 |

---

## 15.10. Hai chiều cấu hình — dễ quên nhất

```
Vercel  VITE_BACKEND_URL  ──trình duyệt gọi──▶  Render
Render  CLIENT_URL        ──CORS + cookie────▶  đúng origin Vercel
```

| Chiều | Biến | Nền tảng | Khi nào có hiệu lực |
|---|---|---|---|
| Browser → API | `VITE_BACKEND_URL` | Vercel | **Lúc build** frontend → phải Redeploy |
| API → Browser | `CLIENT_URL` | Render | Lúc process backend start → Save env / restart |

Cookie đăng nhập (refresh token `httpOnly`):

| Biến Render | Giá trị | Vì sao |
|---|---|---|
| `COOKIE_SECURE` | `true` | Chỉ gửi cookie trên HTTPS |
| `COOKIE_SAMESITE` | `none` | Frontend `*.vercel.app` khác site backend `*.onrender.com`. `lax` mặc định **không** gửi cookie cross-site |
| `TRUST_PROXY_HEADERS` | `true` | Render đứng sau proxy; rate limit theo IP cần `X-Forwarded-For` thật |

`SameSite=None` **bắt buộc** đi với `Secure`. Thiếu một trong hai: đăng nhập
xong F5 bị văng, hoặc refresh token không tới.

`EMBEDDER_URL` **không đặt** trên Render. Cố tình.

---

## 15.11. Seed dữ liệu vào Atlas

Chạy **trên máy local**, trỏ `DATABASE_URL` lên Atlas. Không chạy ETL crawl
trên Render free (không cài Chromium, instance sẽ chết RAM).

Cần Python + dependency backend (local dùng `.venv311`):

```bash
cd server_python
# DATABASE_URL và REDIS_URL lấy từ file local không commit
export DATABASE_URL='mongodb+srv://fuurin:...@...mongodb.net/fuurin'
export REDIS_URL='rediss://default:...@...upstash.io:6379'
export ACCESS_TOKEN_SECRET='dev_placeholder_for_seed_scripts'
export EMBEDDER_URL=   # để trống

.venv311/bin/python -m scripts.seed_required
.venv311/bin/python -m scripts.seed_jobs_from_fixtures --no-embed
.venv311/bin/python -m scripts.seed_demo_user --contrast
.venv311/bin/python -m scripts.seed_resumes --count 100
```

`--no-embed` vì không có service embedder trên mạng. Script vẫn ghi job; vector
để `null`; matching dùng luật.

`seed_required` **upsert**, chạy lại không xoá user. Bắt buộc vì đăng ký đọc
collection `roles`. Thiếu role → đăng ký lỗi dù UI vẫn mở.

Số lượng sau seed (Atlas Explorer, DB `fuurin`):

| Collection | Số | Script |
|---|---|---|
| `roles` | 2 (`user`, `admin`) | `seed_required` |
| `webs` | 1 (tên Fuurin + câu quote login) | `seed_required` |
| `jobs` | 100 | `seed_jobs_from_fixtures --no-embed` |
| `companies` | 61 | cùng script jobs |
| `users` | 102 | 2 demo + 100 seed |
| `resumes` | 102 | cùng các script user |

**Không seed:** channel / bài viết. Tạo channel chỉ admin, nên feed live trống
là đúng dữ liệu, không phải API hỏng.

---

## 15.12. Việc đã kiểm trên bản live

Ngày 18/09/2026, origin production (không dùng preview):

| Hạng mục | Kết quả |
|---|---|
| Login `demo@fuurin.local` | OK |
| `/resume` gõ thẳng URL | 200 |
| CV demo Backend / N3 / 4 năm / Tokyo | Hiện đủ |
| Việc làm | 100 tin |
| Công ty phù hợp | 61 công ty, chấm luật |
| What-if (lên N2) | 44 → 47 việc |
| Lọc Tokyo | Phân trang giảm 9 → 5 |
| Tìm người + follow | OK |
| Chat 2 account (`demo` ↔ `demo-nojp`) | Hai chiều, Socket.IO 200 |
| Feed / channel | Trống — chưa có channel |
| Xếp hạng ngữ nghĩa | Tắt — `EMBEDDER_URL` trống |
| Preview Vercel khác subdomain | CORS chặn — `CLIENT_URL` chỉ origin production |

Chat: không mở được hai phiên đăng nhập khác nhau trên **cùng**
`fuurin-client.vercel.app` vì cookie dùng chung. Cách test: một người trên UI
production, người kia login account thứ hai (cửa sổ ẩn danh, hoặc client
Socket.IO). Cả hai chiều `ui-chat-from-quan` / `ui-reply-from-nojp` đều hiện.

---

## 15.13. Sự cố đã gặp (và đã xử lý)

### A. Chat realtime 404

Frontend từng gọi `https://fuurin-api.onrender.com`. Service đó không chạy
`socket_app`. Sửa `VITE_BACKEND_URL` → `https://fuurin-api-idhh.onrender.com`
rồi **Redeploy Vercel**. Handshake Socket.IO 200, tin nhắn lưu và bắn realtime.

### B. Gõ `/resume` ra 404

Thiếu rewrite SPA trên **đúng repo Vercel đang build**. Sau khi `vercel.json`
có mặt trên nguồn Git của project, `/resume` 200.

### C. Import Vercel báo trùng tên

Project `fuurin-client` đã tồn tại. Không tạo project thứ hai cùng tên. Dùng
lại rồi đổi Git source sang `sns`.

### D. Push `sns` mà frontend không đổi

Vercel đang build repo `fuurin-client`. Đã Disconnect + Connect `sns`, Root
Directory `client`, Deploy Production từ `0535d1f`.

### E. Preview `*.vercel.app` khác hash bị CORS

`CLIENT_URL` chỉ một origin production. Đúng cho demo. Muốn test preview: thêm
origin, phân tách bằng dấu phẩy (app hỗ trợ `CLIENT_URL` list).

### F. Atlas `jobs` trống sau `seed_required`

Đúng. `seed_required` không nạp việc. Phải chạy `seed_jobs_from_fixtures`.
Explorer phải chọn database **`fuurin`**.

---

## 15.14. Giới hạn gói miễn phí — ghi vào báo cáo

| Hiện tượng | Nguyên nhân | Chấp nhận? |
|---|---|---|
| Request đầu sau ~15 phút chờ 30–60s | Render free sleep | Có, ghi rõ khi demo |
| Upload ảnh mất sau restart | Đĩa Render không bền | Có — demo không dựa upload |
| Không crawl 4 nguồn thật trên live | Không cài Playwright/Chromium trên free | Có — dùng fixture 100 tin |
| Matching không có điểm cosine | Không host embedder | Có — luật vẫn chạy; xem tài liệu 7 |
| Feed trống | Không seed channel | Có |
| Một tài khoản Vercel Preview CORS fail | `CLIENT_URL` một origin | Có |

**Không commit:** mật khẩu Atlas, URL Redis, JWT secret, `MESSAGE_ENCRYPTION_KEY`,
Gemini/Groq key. Đổi `MESSAGE_ENCRYPTION_KEY` = không đọc lại chat cũ trong DB.

---

## 15.15. Checklist tái hiện (báo cáo / máy khác)

- [ ] Repo `anhthaingd/sns` đã push `render.yaml`, `client/vercel.json`, `seed_required.py`
- [ ] Atlas M0 Tokyo, user DB, Network `0.0.0.0/0`, connection string có `/fuurin`
- [ ] Upstash Redis Tokyo, copy `rediss://…`
- [ ] Render Blueprint `sns`, Blueprint Name khác rỗng, start `socket_app`, Free, Singapore
- [ ] `curl /health` → `ok`; `GET /socket.io/` → 200
- [ ] Vercel project Root Directory `client`, Git = `sns`
- [ ] `VITE_BACKEND_URL=https://fuurin-api-idhh.onrender.com` rồi Redeploy
- [ ] Render `CLIENT_URL=https://fuurin-client.vercel.app`, cookie `secure` + `samesite=none`
- [ ] Seed 4 script (mục 15.11)
- [ ] Login demo, F5 không văng, `/resume` 200, chat 2 account, jobs = 100

Xong checklist này thì bản live trùng với cấu hình ngày 18/09/2026.
