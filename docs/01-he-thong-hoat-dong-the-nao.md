# 1. Hệ thống hoạt động thế nào

## 1.1. Ví von cho dễ hình dung

Hãy tưởng tượng dự án này là một **nhà hàng**:

| Trong nhà hàng | Trong dự án | Tên kỹ thuật |
|---|---|---|
| Phòng ăn, thực đơn, bàn ghế — nơi khách ngồi | Giao diện web bạn nhìn thấy trên trình duyệt | **Frontend** (thư mục `client/`) |
| Nhà bếp — nhận yêu cầu, nấu, trả món ra | Máy chủ xử lý yêu cầu | **Backend** (thư mục `server_python/`) |
| Nhân viên chạy bàn ghi order rồi mang vào bếp | Cầu nối giữa giao diện và máy chủ | **API** |
| Kho thực phẩm — nơi cất mọi nguyên liệu | Nơi lưu tài khoản, bài viết, CV, tin tuyển dụng | **Database** (MongoDB) |
| Tủ mát để sẵn đồ hay dùng, lấy cho nhanh | Bộ nhớ tạm giúp không phải hỏi kho mỗi lần | **Cache** (Redis) |
| Một đầu bếp chuyên món khó, làm riêng một góc | Dịch vụ chuyên tính "độ giống nhau về ý nghĩa" | **Embedder** |

Khách (người dùng) không bao giờ tự vào bếp. Muốn gì cũng phải qua nhân viên
chạy bàn. Đó chính là lý do có API: giao diện **không được** đụng thẳng vào kho
dữ liệu, mọi thứ phải đi qua máy chủ để còn kiểm tra quyền và tính đúng đắn.

> 💡 **API là gì?** Là danh sách những "món" mà máy chủ nhận làm, kèm quy định
> phải gọi thế nào. Ví dụ: *"Muốn lấy danh sách việc làm thì gửi yêu cầu tới
> địa chỉ `/api/jobs`"*. Mỗi món như vậy gọi là một **endpoint**. Dự án này có
> 60 endpoint.

## 1.2. Năm phần chạy song song

Khi bạn gõ `docker compose up -d`, có **5 chương trình** cùng khởi động:

```
                     ┌──────────────────────────────────┐
   Trình duyệt  ───▶ │ client   cổng 5173  (giao diện)  │
   của bạn           └───────────────┬──────────────────┘
                                     │ gọi API
                                     ▼
                     ┌──────────────────────────────────┐
                     │ server   cổng 3000  (bộ não)     │
                     └──┬──────────┬──────────┬─────────┘
                        │          │          │
             ┌──────────▼──┐  ┌────▼─────┐  ┌─▼──────────────┐
             │ mongo 27017 │  │redis 6379│  │ embedder 8001  │
             │ (kho chính) │  │(bộ nhớ   │  │ (tính độ giống │
             │             │  │ tạm)     │  │  nhau)         │
             └─────────────┘  └──────────┘  └────────────────┘
```

> 💡 **Container là gì?** Là một cái hộp đóng gói sẵn chương trình cùng mọi thứ
> nó cần để chạy. Nhờ vậy máy ai cũng chạy ra kết quả giống nhau, không còn
> cảnh "máy tôi chạy được mà máy bạn thì không". `docker compose` là công cụ
> bật cả 5 hộp cùng lúc.

**Chỉ có `client` và `server` là mở ra ngoài.** `mongo`, `redis`, `embedder`
chỉ nói chuyện được với nhau bên trong mạng nội bộ của Docker — người ngoài
không gọi thẳng vào được.

Kiểm tra 5 phần có đang sống hay không:

```bash
docker compose ps
```

Cột `STATUS` phải hiện `healthy` ở cả 5 dòng.

## 1.3. Bấm một nút thì chuyện gì xảy ra

Lấy ví dụ thật: bạn vào trang **Công ty phù hợp**.

```
①  Bạn bấm "Công ty phù hợp" ở menu bên trái
        │
        ▼
②  Trình duyệt đổi địa chỉ thành /match
    → React Router tìm xem trang nào phụ trách đường dẫn này
    → file:  client/src/services/router/router.jsx
        │
        ▼
③  Trang MatchLayout.jsx được hiển thị
    → file:  client/src/layouts/home/Match/MatchLayout.jsx
    → nó gọi useGetMatchedCompaniesQuery()
        │
        ▼
④  Yêu cầu HTTP bay sang máy chủ:   GET http://localhost:3000/api/match/companies
    → kèm theo "vé vào cửa" (access token) trong tiêu đề Authorization
        │
        ▼
⑤  Máy chủ nhận, kiểm tra vé
    → file:  server_python/app/routes/match.py       (nhận yêu cầu)
    → file:  server_python/app/middleware/auth.py    (kiểm tra vé)
        │
        ▼
⑥  Phần xử lý nghiệp vụ chạy
    → file:  server_python/app/controllers/match.py
    → lấy CV trong MongoDB, lấy 430 tin tuyển dụng, chấm điểm từng tin
        │
        ▼
⑦  Máy chủ trả về dữ liệu dạng JSON
        │
        ▼
⑧  Giao diện nhận được, vẽ ra danh sách công ty kèm điểm
```

> 💡 **JSON là gì?** Là cách viết dữ liệu mà cả máy chủ lẫn trình duyệt đều đọc
> được, trông như thế này:
> ```json
> { "companyName": "JOBs Japan", "score": 89.0, "location": "Tokyo" }
> ```
> Đó là "ngôn ngữ chung" giữa bếp và phòng ăn.

Bạn tự nhìn thấy bước ⑦ được: mở trình duyệt vào
<http://localhost:3000/docs> — đây là trang tài liệu API tự sinh, liệt kê cả
60 endpoint và cho phép bấm thử ngay tại chỗ.

## 1.4. Bản đồ thư mục

```
FinalProject_Fuurin/
├── client/                  ← GIAO DIỆN (những gì người dùng nhìn thấy)
│   └── src/
│       ├── layouts/         ← các TRANG (mỗi thư mục là một màn hình)
│       ├── components/      ← các MẢNH GHÉP dùng lại nhiều nơi (nút, modal, thẻ bài viết)
│       ├── services/
│       │   ├── redux/query/api/  ← khai báo cách gọi từng API
│       │   ├── router/      ← bảng "đường dẫn nào mở trang nào"
│       │   └── logger.js    ← ghi lại lỗi phía trình duyệt
│       ├── i18n/            ← chữ nghĩa của 3 ngôn ngữ (Nhật, Việt, Anh)
│       ├── hooks/           ← đoạn logic dùng chung cho nhiều trang
│       └── context/         ← dữ liệu dùng chung toàn app (user đang đăng nhập...)
│
├── server_python/           ← MÁY CHỦ (bộ não)
│   └── app/
│       ├── routes/          ← "cửa" nhận yêu cầu, khai báo địa chỉ URL
│       ├── controllers/     ← xử lý nghiệp vụ (làm gì với yêu cầu đó)
│       ├── models/          ← mô tả hình dạng dữ liệu trong kho
│       ├── services/        ← việc chuyên môn: chấm điểm, crawl, gửi mail...
│       ├── schemas/         ← quy định dữ liệu gửi lên / trả về phải trông ra sao
│       ├── middleware/      ← chốt kiểm tra chạy TRƯỚC controller (vé vào cửa, upload file)
│       └── utils/           ← hàm tiện ích nhỏ dùng chung
│
├── embedder/                ← dịch vụ riêng, tính "độ giống nhau về ý nghĩa"
├── e2e/                     ← test mô phỏng người dùng thật bấm chuột
├── docs/                    ← chính là tài liệu bạn đang đọc
└── docker-compose.yml       ← khai báo 5 container nói trên
```

## 1.5. Vì sao chia nhiều tầng như vậy

Nhìn `routes` → `controllers` → `models` có vẻ rườm rà, nhưng mỗi tầng có đúng
một việc, nên khi hỏng thì biết ngay phải mở file nào:

| Tầng | Chịu trách nhiệm | Ví dụ câu hỏi thuộc tầng này |
|---|---|---|
| `routes` | Địa chỉ URL, phương thức (GET/POST), ai được vào | "Sao gọi `/api/jobs` lại báo 404?" |
| `controllers` | Nghiệp vụ: lấy gì, tính gì, trả gì | "Sao điểm phù hợp lại là 89 mà không phải 90?" |
| `models` | Hình dạng dữ liệu, chỉ mục tra cứu | "Tin tuyển dụng lưu những trường nào?" |
| `services` | Việc chuyên môn tách riêng | "Crawl trang GaijinPot chạy thế nào?" |

> 💡 **GET và POST khác gì nhau?** `GET` là *đọc* (lấy danh sách việc làm),
> `POST` là *tạo mới* (đăng một bài viết), `PUT` là *sửa*, `DELETE` là *xoá*.
> Quy ước này giúp nhìn tên là đoán được endpoint làm gì.

---

Tiếp theo: [2. Tạo một API mới](02-tao-mot-api-moi.md)
