# Tài liệu dự án Fuurin

Bộ tài liệu này viết cho **người chưa quen với lập trình web**. Mỗi khái niệm
đều được giải thích trước khi dùng, mọi đường dẫn file đều là file có thật
trong dự án, và mọi câu lệnh đều copy dán chạy được.

## Đọc theo thứ tự nào

Nếu bạn mới tiếp cận dự án, đọc lần lượt từ trên xuống:

| # | Tài liệu | Trả lời câu hỏi |
|---|---|---|
| 1 | [Hệ thống hoạt động thế nào](01-he-thong-hoat-dong-the-nao.md) | Web này gồm những phần nào? Bấm một nút thì chuyện gì xảy ra? |
| 2 | [Tạo một API mới](02-tao-mot-api-moi.md) | Muốn thêm một chức năng ở phía máy chủ thì viết những file nào, theo thứ tự nào? |
| 3 | [Tạo một màn hình mới](03-tao-mot-man-hinh-moi.md) | Muốn thêm một trang mới cho người dùng thì làm gì? |
| 4 | [Luồng đăng nhập](04-luong-dang-nhap.md) | Đăng nhập xong thì hệ thống nhớ mình bằng cách nào? |
| 5 | [Luồng bài viết và channel](05-luong-bai-viet.md) | Đăng bài, thích, bình luận đi qua những đâu? |
| 6 | [Luồng CV và việc làm](06-luong-cv-va-viec-lam.md) | CV lưu ở đâu? 430 tin tuyển dụng từ đâu ra? |
| 7 | [Embedding và gợi ý công ty](07-embedding-va-goi-y.md) | Máy "hiểu" CV kiểu gì? Điểm phù hợp tính ra sao? |
| 8 | [Lỗi, log và kiểm thử](08-loi-log-va-kiem-thu.md) | Có lỗi thì tra ở đâu? Làm sao biết code không hỏng? |
| 9 | [Đa ngôn ngữ](09-da-ngon-ngu.md) | Giao diện nói ba thứ tiếng bằng cách nào? Thêm một câu chữ mới thì sửa ở đâu? |
| 10 | [Mô phỏng đối chứng](10-mo-phong-doi-chung.md) | "Nếu tôi học thêm X thì mở ra bao nhiêu cơ hội?" tính bằng cách nào? |
| 11 | [Sổ tay giao diện](11-so-tay-giao-dien.md) | Mỗi màn hình trông thế nào và làm gì? Bộ test nào đang bảo vệ nó? |

## Dự án này là gì

Fuurin là mạng xã hội cho người tìm việc tại Nhật Bản. Có hai nhóm chức năng:

**Nhóm mạng xã hội** — đăng ký, đăng nhập, đăng bài trong các channel (nhóm),
thích, bình luận, lưu bài, theo dõi người khác, nhắn tin và gọi video.

**Nhóm việc làm** — hệ thống tự thu thập tin tuyển dụng từ 4 trang việc làm
Nhật, chuẩn hoá lại, rồi so khớp với CV của người dùng để trả lời hai câu hỏi:

- *"CV của tôi hợp với công ty nào?"*
- *"Tôi còn thiếu gì để vào được công ty A?"*

## Con số của dự án (tính đến lần cập nhật tài liệu này)

| | |
|---|---|
| Endpoint API | 63 |
| Bảng dữ liệu (collection) | 14 |
| Trang phía người dùng | 20 |
| File giao diện | 106 |
| Test tự động | 345 test API + 15 test giao diện |
| Tin tuyển dụng trong kho | 430 tin từ 4 nguồn |
| Ngôn ngữ giao diện | 3 (Nhật · Việt · Anh) — 572 khoá mỗi ngôn ngữ |

## Quy ước trong tài liệu

- `Chữ trong ô xám` là tên file, tên lệnh, hoặc đoạn code.
- Đường dẫn file luôn tính từ thư mục gốc dự án, ví dụ
  `server_python/app/routes/jobs.py`.
- Các câu lệnh đều chạy ở thư mục gốc dự án, trong Terminal.
- Phần đóng khung 💡 là giải thích thêm cho người chưa quen thuật ngữ.
