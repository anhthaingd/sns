# 11. Sổ tay giao diện

Tài liệu này chụp lại **toàn bộ giao diện Fuurin** ở trạng thái hiện tại và
giải thích mỗi màn hình làm gì.

Ảnh trong đây **không chụp tay**. Chúng do `e2e/capture_docs.py` sinh ra: một
kịch bản Playwright tự đăng ký tài khoản, tạo CV, lập channel, đăng bài, bình
luận, theo dõi người khác, nhắn tin — rồi đi hết 20 đường dẫn của ứng dụng và
bấm nút chụp. Chạy lại một câu lệnh là có bộ ảnh mới khớp với code mới.

> 💡 **Vì sao phải tự dựng dữ liệu?** Cơ sở dữ liệu lúc phát triển đầy bản ghi
> do bộ test sinh ra: người dùng tên `e2e user`, channel tên `e2e-a3f9c1`. Chụp
> những thứ đó thì người đọc không hiểu màn hình đang làm gì, nên kịch bản tạo
> riêng một bộ dữ liệu đọc được.

## 11.1. Chạy lại bộ ảnh này

```bash
# 1. Dựng cả hệ thống
docker compose up -d

# 2. Chụp lại toàn bộ (khoảng 6 phút)
docker compose -f docker-compose.yml -f docker-compose.test.yml \
    run --rm -e E2E_LANG=vi e2e-tests python -m e2e.capture_docs
```

Ảnh ghi đè vào `docs/screenshots/`, kèm `manifest.json` liệt kê từng ảnh. Đổi
`E2E_LANG=vi` thành `ja` hoặc `en` là có bộ ảnh ngôn ngữ khác.

Kịch bản dọn dữ liệu demo của lần chạy trước rồi mới dựng lại, nên chạy bao
nhiêu lần cũng không tích rác.

> ⚠️ Sửa code backend hay frontend xong phải **dựng lại image** trước khi chụp:
> hai service `server` và `client` nướng mã nguồn vào trong image chứ không
> mount từ máy. Quên bước này thì ảnh chụp ra vẫn là giao diện cũ.
>
> ```bash
> docker compose build server client && docker compose up -d server client
> ```

## 11.2. Kết quả kiểm thử tự động

Chụp xong chỉ chứng minh màn hình *vẽ ra được*. Chuyện màn hình *làm đúng việc*
do hai bộ test dưới đây trả lời, và cả hai đều chạy trước khi bộ ảnh này được
tạo:

| Bộ test | Số lượng | Kết quả | Câu lệnh |
|---|---|---|---|
| API (pytest, gọi thẳng FastAPI) | 384 | **378 chạy qua, 6 bỏ qua** | `docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm api-tests` |
| Giao diện (Playwright, trình duyệt thật) | 18 | **18 chạy qua** | `docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm e2e-tests` |

6 test bị bỏ qua là nhóm thu thập tin tuyển dụng từ trang ngoài — chúng chỉ
chạy khi đặt `RUN_CRAWL_TESTS=1`, vì phụ thuộc vào mạng và vào việc trang nguồn
có đổi cấu trúc hay không.

Bộ 18 test giao diện đi qua những việc sau, mỗi việc trên một trình duyệt thật:

| # | Test | Kiểm điều gì |
|---|---|---|
| 1 | `login_page_loads_website_config_from_api` | Tên website lấy từ API chứ không viết cứng — tức backend + CORS sống |
| 2 | `unauthenticated_user_is_redirected_to_login` | Chưa đăng nhập thì không vào được trang trong |
| 3 | `register_then_login` | Đăng ký ghi vào DB, đăng nhập lấy được token |
| 4 | `wrong_password_shows_backend_error_message` | Sai mật khẩu hiện đúng câu chữ của backend, đã dịch |
| 5 | `plain_user_has_no_admin_menu` | Người thường không thấy menu quản trị |
| 6 | `admin_sees_admin_menu` | Quản trị viên thì thấy |
| 7 | `channel_join_and_post_flow` | Tạo channel → tham gia → đăng bài → bài hiện trên feed |
| 8 | `client_connects_to_socketio_and_receives_new_message` | Tin nhắn đẩy thời gian thực, huy hiệu chưa đọc hiện lên |
| 9 | `refresh_token_is_never_exposed_to_javascript` | Refresh token nằm trong cookie httpOnly, JavaScript không đọc được |
| 10 | `recruitment_page_shows_structured_jobs_with_filters` | Tin tuyển dụng đọc từ DB đã chuẩn hoá; bỏ một bộ lọc không làm mất bộ lọc còn lại |
| 11 | `match_page_requires_a_resume_then_shows_companies` | Chưa có CV thì chỉ đường tạo CV; có CV thì ra gợi ý |
| 12 | `whatif_recalculates_when_an_option_is_picked` | Tick một phương án thì con số kết hợp tính lại |
| 13 | `whatif_needs_a_resume_first` | Chưa có CV thì nói rõ, bằng câu chữ của backend |
| 14 | `market_page_shows_the_sample_size_next_to_every_median` | Không trung vị nào đứng một mình — luôn kèm cỡ mẫu |
| 15 | `switching_language_changes_the_whole_interface` | Đổi ngôn ngữ đổi cả chữ tĩnh lẫn câu do backend sinh, và nhớ qua F5 |
| 16 | `advice_card_shows_exactly_what_the_api_returned` | Thẻ gợi ý AI hiện đúng chữ API trả về, không phải chữ viết cứng ở client |
| 17 | `every_page_survives_a_dead_advice_endpoint` | **Chặn thẳng endpoint gợi ý ở tầng mạng**: mọi trang vẫn nguyên vẹn, không toast lỗi, khung chờ biến mất |
| 18 | `advice_is_requested_in_the_interface_language` | Request mang đúng `?lang` của giao diện đang dùng |

Chín test API trong số trên là **mới**, viết cùng lúc với năm bản vá ở mục 11.9 —
mỗi lỗi được vá đều kèm một test canh cho nó không quay lại.

## 11.3. Xác thực và lối vào

Ba màn hình người dùng gặp trước khi có tài khoản.

### Đăng nhập

![Đăng nhập](screenshots/01-dang-nhap.png)

Tên và mô tả website lấy từ API `GET /api/website`, không viết cứng ở frontend.

### Đăng ký

![Đăng ký](screenshots/02-dang-ky.png)

Cùng khung nền với trang đăng nhập; ba luận điểm giá trị nằm ở cột trái.

### Trang không tồn tại

![Trang không tồn tại](screenshots/03-khong-tim-thay.png)

Đường dẫn lạ rơi vào màn hình 404 có lối quay lại, không phải màn hình trắng.

## 11.4. Mạng xã hội

Nhóm chức năng cộng đồng: bảng tin, channel, bài viết, bình luận, tìm kiếm, thông báo và nhắn tin.

### Bảng tin

![Bảng tin](screenshots/10-bang-tin.png)

Ba cột: điều hướng trái, dòng bài giữa, gợi ý phải. Cột phải ẩn dưới 1280px.

### Soạn bài viết

![Soạn bài viết](screenshots/11-soan-bai.png)

Ô soạn bài mặc định thu gọn một dòng; bấm mới mở trình soạn thảo Quill và ô chọn channel.

### Danh sách channel

![Danh sách channel](screenshots/12-danh-sach-channel.png)

Mỗi thẻ có ảnh bìa, số thành viên và nút tham gia; trạng thái đang xử lý bám theo từng thẻ.

### Chi tiết channel

![Chi tiết channel](screenshots/13-chi-tiet-channel.png)

Ảnh bìa seigaiha, phần giới thiệu, danh sách thành viên và dòng bài của riêng channel.

### Chi tiết bài viết & bình luận

![Chi tiết bài viết & bình luận](screenshots/14-chi-tiet-bai-viet.png)

Bình luận hiển thị 2 dòng đầu rồi gập lại; ô nhập là `<input>` thật chứ không phải contentEditable.

### Bài đã lưu

![Bài đã lưu](screenshots/15-da-luu.png)

Danh sách bài người dùng đã đánh dấu, dùng lại đúng component bài viết của bảng tin.

### Trang cá nhân

![Trang cá nhân](screenshots/16-trang-ca-nhan.png)

Ảnh bìa, thông tin, số người theo dõi và các bài đã đăng.

### Tìm kiếm — người dùng

![Tìm kiếm — người dùng](screenshots/17-tim-nguoi-dung.png)

Kết quả người dùng kèm nút theo dõi và nhắn tin ngay trên từng dòng.

### Tìm kiếm — bài viết

![Tìm kiếm — bài viết](screenshots/18-tim-bai-viet.png)

Cùng ô tìm kiếm, đổi tab sang bài viết; từ khoá nằm ở tham số `s` trên URL nên chia sẻ được.

### Cài đặt tài khoản

![Cài đặt tài khoản](screenshots/19-cai-dat-tai-khoan.png)

Ba tab: bài viết của tôi, người theo dõi, đang theo dõi.

### Thông báo

![Thông báo](screenshots/20-thong-bao.png)

Huy hiệu đếm số chưa đọc hiện ngay khi tải trang, không chờ tới lúc mở bảng.

### Hộp thư

![Hộp thư](screenshots/21-hop-thu.png)

Danh sách hội thoại lấy qua Socket.io; tin nhắn mới đẩy thẳng xuống client.

### Trò chuyện

![Trò chuyện](screenshots/22-tro-chuyen.png)

Hộp thoại chat thời gian thực, có cả nút gọi video (simple-peer).

## 11.5. Tin tuyển dụng và CV

Kho tin tuyển dụng đã chuẩn hoá, và biểu mẫu CV làm đầu vào cho phần so khớp.

### Tin tuyển dụng

![Tin tuyển dụng](screenshots/30-tin-tuyen-dung.png)

Dữ liệu đã qua ETL vào DB; cột lọc bên phải dính theo cuộn.

### Lọc tin tuyển dụng

![Lọc tin tuyển dụng](screenshots/31-loc-tin-tuyen-dung.png)

Mỗi bộ lọc đang bật thành một chip bỏ được; bộ lọc ghi vào URL nên F5 không mất.

### Hồ sơ CV

![Hồ sơ CV](screenshots/32-ho-so-cv.png)

Biểu mẫu CV chia khối: thông tin, kinh nghiệm, học vấn, kỹ năng, dự án.

### Xem trước CV — mẫu 1

![Xem trước CV — mẫu 1](screenshots/33-xem-truoc-cv-mau-1.png)

Bản xem trước luôn giữ nền trắng chữ đen kể cả ở chế độ tối: đây là bản sẽ in ra giấy.

### Xem trước CV — mẫu 2

![Xem trước CV — mẫu 2](screenshots/34-xem-truoc-cv-mau-2.png)

Mẫu thứ hai cùng dữ liệu, đổi bố cục sang hai cột.

## 11.6. So khớp và phân tích

Bốn màn hình trả lời: CV này hợp với ai, còn thiếu gì, bù chỗ nào thì lợi nhất, và thị trường đang trả bao nhiêu.

> ✨ **Thẻ "Gợi ý từ AI" ở cuối các màn hình này** là phần do mô hình ngôn ngữ
> viết, thêm vào sau — xem [tài liệu 12](12-loi-khuyen-bang-llm.md). Nó luôn
> nằm **dưới** phần tính bằng luật, vì thứ tự trên màn hình nói lên thứ tự đáng
> tin, và luôn kèm một dòng nhắc rằng điểm số không thay đổi theo đoạn văn đó.
> Không cấu hình API key thì thẻ này không xuất hiện và mọi thứ khác giữ nguyên.

### Công ty phù hợp

![Công ty phù hợp](screenshots/40-cong-ty-phu-hop.png)

Điểm phù hợp tính từ CV: vòng cung 270° kèm số, không chỉ một thanh màu.

### Phân tích thiếu sót — công ty

![Phân tích thiếu sót — công ty](screenshots/41-thieu-sot-cong-ty.png)

Điều kiện loại chỉ giữ mốc dễ nhất trong các vị trí đang tuyển; kỹ năng xếp theo số vị trí yêu cầu, nên dòng đầu là thứ đáng học nhất.

### Phân tích thiếu sót — tin tuyển dụng

![Phân tích thiếu sót — tin tuyển dụng](screenshots/42-thieu-sot-viec-lam.png)

Cùng cách trình bày, nhưng đối chiếu với một tin cụ thể.

### Mô phỏng “Nếu tôi học thêm”

![Mô phỏng “Nếu tôi học thêm”](screenshots/43-mo-phong.png)

Điểm gốc nằm trên cùng; mỗi phương án ghi rõ mức tăng nếu chọn.

### Mô phỏng — kết quả kết hợp

![Mô phỏng — kết quả kết hợp](screenshots/44-mo-phong-ket-qua.png)

Chọn nhiều phương án thì thẻ kết quả kết hợp dính ở mép dưới, không phải cuộn đi tìm.

### Bản đồ thị trường

![Bản đồ thị trường](screenshots/45-ban-do-thi-truong.png)

Biểu đồ thanh một sắc asagi, không chú giải thừa; mọi trung vị đều đi kèm cỡ mẫu n=.

## 11.7. Trang quản trị

Chỉ tài khoản có `role.value === 1` vào được; người thường mở đúng đường dẫn này cũng chỉ thấy trang 404.

### Quản trị — cấu hình website

![Quản trị — cấu hình website](screenshots/50-quan-tri-website.png)

Tên, mô tả và logo của website sửa tại đây rồi áp dụng cho mọi trang.

### Quản trị — người dùng

![Quản trị — người dùng](screenshots/51-quan-tri-nguoi-dung.png)

Mã người dùng đứng cột cuối, cỡ chữ nhỏ: thứ chỉ dùng khi tra sự cố không nên chiếm chỗ dễ đọc nhất.

### Quản trị — channel

![Quản trị — channel](screenshots/52-quan-tri-channel.png)

Danh sách channel kèm số thành viên và thao tác xoá.

### Quản trị — bài viết

![Quản trị — bài viết](screenshots/53-quan-tri-bai-viet.png)

Bài viết của toàn hệ thống, tìm theo từ khoá và phân trang phía máy chủ.

### Quản trị — trang cá nhân

![Quản trị — trang cá nhân](screenshots/54-quan-tri-ca-nhan.png)

Tab bài viết / người theo dõi / đang theo dõi của chính tài khoản quản trị.

## 11.8. Chế độ tối và màn hình hẹp

Cùng bộ mã nguồn, đổi theo thiết lập của người dùng và theo bề ngang màn hình.

### Chế độ tối — bảng tin

![Chế độ tối — bảng tin](screenshots/60-toi-bang-tin.png)

Nền sumi(墨) #0E1219; các token màu đổi giá trị chứ không phải lật ngược màu.

### Chế độ tối — tin tuyển dụng

![Chế độ tối — tin tuyển dụng](screenshots/61-toi-tin-tuyen-dung.png)

Sắc thương hiệu chuyển sang bậc nhạt hơn (ai-500) để giữ tương phản trên nền tối.

### Chế độ tối — biểu đồ

![Chế độ tối — biểu đồ](screenshots/62-toi-bieu-do.png)

Bảng màu biểu đồ được chọn riêng cho nền tối, không dùng lại bảng của nền sáng.

### Điện thoại — bảng tin

![Điện thoại — bảng tin](screenshots/70-dt-bang-tin.png)

Dưới 1024px hai cột bên thu lại, thanh điều hướng chuyển xuống mép dưới.

### Điện thoại — menu

![Điện thoại — menu](screenshots/71-dt-menu.png)

Thanh dưới chỉ chứa 4 mục hay dùng; phần còn lại nằm trong ngăn kéo “Thêm”.

### Điện thoại — tin tuyển dụng

![Điện thoại — tin tuyển dụng](screenshots/72-dt-tin-tuyen-dung.png)

Bộ lọc xếp dọc thành khối gập được thay vì cột dính bên phải.

### Điện thoại — công ty phù hợp

![Điện thoại — công ty phù hợp](screenshots/73-dt-cong-ty-phu-hop.png)

Thẻ điểm phù hợp giữ nguyên vòng cung, chỉ đổi cách xếp khối.

## 11.9. Năm lỗi tìm ra khi làm tài liệu, và cách đã sửa

Đi hết mọi màn hình bằng dữ liệu thật làm lộ ra năm thứ mà bộ test không bắt
được, vì test kiểm *hành vi*, không kiểm *nội dung trông ra sao*. Cả năm đều đã
sửa; mỗi bản vá kèm test canh cho nó không quay lại.

### a) `PUT /api/users/{id}` xoá trắng trường không gửi kèm

**Triệu chứng.** Gọi endpoint này chỉ để đổi ảnh đại diện là **mất tên tài
khoản**. Tôi gặp trực tiếp lúc dựng dữ liệu demo: sau khi tải ảnh lên, mọi bài
viết mất tên tác giả.

**Nguyên nhân.** `update_user` dựng cả khối rồi `$set` một lần:

```python
update_data = {"username": username, "address": address, "intro": intro, ...}
```

Request không đính `username` thì FastAPI đưa vào `None`, và `$set` ghi đè.
Chưa ai gặp vì `UpdateProfileModal.jsx` luôn gửi đủ ba trường — may mắn, không
phải thiết kế.

**Bẫy khi sửa.** Cách hiển nhiên là `if value is not None`. Nhưng đo thử thì
thấy FastAPI đưa một field **gửi lên rỗng** (`intro=`) tới controller cũng dưới
dạng `None`, không phân biệt được với field vắng mặt — nên bản vá hiển nhiên
kia sẽ khiến người dùng không xoá nổi phần giới thiệu của mình. Đổi một lỗi mất
dữ liệu lấy một lỗi mất chức năng.

**Cách sửa.** Thêm `app/utils/forms.py` đọc thẳng tên các field có trong form,
rồi chỉ ghi những trường thật sự được gửi:

```python
for field_name, value in (("username", username), ("address", address), ("intro", intro)):
    if field_name in submitted:
        update_data[field_name] = value if value is not None else ""
```

Test canh: `test_partial_update_keeps_fields_that_were_not_sent` và
`test_empty_string_still_clears_a_field` — hai đầu của cùng một sự phân biệt.

### b) Ảnh đại diện thay bằng chữ cái đầu tên là code chết

**Triệu chứng.** Trong mọi danh sách, mọi người là một vòng tròn xám giống hệt
nhau. Ảnh chụp tư liệu không đọc được ai đang nói gì.

**Nguyên nhân.** `client/src/components/ui/Avatar.jsx` có sẵn phần dựng ảnh
thay thế — chữ cái đầu của tên trên một trong sáu sắc chàm/asagi, chọn theo tên
nên mỗi người một màu cố định. Nhưng `app/models/user.py` khai báo:

```python
avatar: dict | None = Field(default_factory=lambda: {"name": "avatar_trang.jpg", ...})
```

Mọi tài khoản mới vì thế đều *có* ảnh — cùng một file hình bóng người xám — nên
`Avatar.jsx` thấy có URL và không bao giờ chạy tới nhánh chữ cái đầu.

**Cách sửa.** Bỏ mặc định đi (`avatar: dict | None = None`). Tài khoản cũ trong
DB vẫn trỏ vào file đó, nên kèm `scripts/clear_default_avatars.py` để gỡ — script
chỉ đụng đúng file mặc định, ai đã tự tải ảnh lên thì giữ nguyên:

```bash
docker compose run --rm server python -m scripts.clear_default_avatars --dry-run
docker compose run --rm server python -m scripts.clear_default_avatars
```

Test canh: `test_new_account_has_no_default_avatar`.

### c) Seed website mang logo cờ Mỹ và chữ Lorem ipsum

**Triệu chứng.** Cài mới hệ thống ra một sản phẩm tuyển dụng thị trường Nhật
treo cờ Mỹ, với hai câu giới thiệu bằng Lorem ipsum.

**Nguyên nhân.** `server_python/data/social_app.webs.json` là di sản từ template
gốc, chưa ai thay.

**Cách sửa.** Bỏ hẳn trường `logo`: cả `Header.jsx` lẫn `AuthShell.jsx` đều đã
có sẵn nhánh lùi về `/fuurin.svg` — ảnh phong linh của chính ứng dụng — khi cấu
hình không có logo. Hai câu quote thay bằng câu thật, `color_title` đổi về sắc
chàm thương hiệu `#274A78`.

### d) Bộ test API làm bẩn cơ sở dữ liệu phát triển

**Triệu chứng.** Ảnh chụp đầu tiên mang tiêu đề "Fuurin-bdd43".

**Nguyên nhân.** Cấu hình website là bản ghi **dùng chung**, chỉ có đúng một bản
trong DB. `test_admin_updates_website` đổi tên thành `Fuurin-<hex>` rồi bỏ đó.

**Cách sửa.** Test chụp lại nguyên trạng trước khi đổi và trả về trong `finally`.
Kịch bản chụp ảnh cũng tự đặt lại cấu hình website từ file seed trước khi chạy,
để một DB đã bẩn sẵn không kéo theo tài liệu.

### e) Trang "thiếu sót của công ty" dài hơn 5.000 pixel

**Triệu chứng.** Với CV mẫu, `/match/companies/:id` của một công ty lớn liệt kê
**22 điều kiện bắt buộc và 54 điểm nên có** — cuộn hơn năm màn hình, mỗi dòng là
một khối chữ dài. Người dùng không rút ra được "tôi cần học gì", đúng thứ mà cả
trang này sinh ra để trả lời.

**Nguyên nhân.** Phần gộp thiếu sót cấp công ty loại trùng bằng cách so **nguyên
câu**: `if gap.message not in seen`. Mà `matching._check_skills` gói toàn bộ kỹ
năng thiếu của một tin vào **một** mục, câu chữ là
`"Thiếu kỹ năng: " + ", ".join(missing)`. Hai tin cùng thiếu Java mà khác nhau
đúng một kỹ năng thứ hai cho hai câu khác nhau, nên phép loại trùng gần như
không loại được gì.

**Cách sửa.** Viết lại `_combine_gaps` thành ba cách gộp cho ba loại câu hỏi
khác nhau:

- **Ngôn ngữ, số năm kinh nghiệm, lương** — mọi thứ đo được thành thang thì giữ
  **mốc dễ nhất** trong số các vị trí CV chưa với tới. Thứ người dùng cần biết
  là "cửa thấp nhất vẫn còn cao hơn mình bao nhiêu", chứ không phải chín dòng
  "cần 4 / 5 / 8 / 30 năm" và bốn dòng "lương tối đa 380 / 400 / 450 / 500 man
  thấp hơn mong muốn 550" chồng lên nhau.
- **Kỹ năng** — bung ra từng kỹ năng rồi **đếm số vị trí** đang đòi nó, xếp giảm
  dần. "41/98 vị trí yêu cầu AWS" trả lời được "học cái nào mở ra nhiều cửa
  nhất".
- **Lương, địa điểm** — loại trùng theo `code` + `params` thay vì theo câu chữ.

Thêm một quyết định nữa: ở mức công ty, kỹ năng **không bao giờ** mang nhãn
"bắt buộc phải bù". Nhãn đó sinh ra ở mức từng tin ("CV khớp 0 kỹ năng của tin
này"), đưa lên mức công ty thì mất nghĩa — chỗ nào có cả trăm vị trí, gần như kỹ
năng nào cũng thuộc về một tin mà CV khớp 0. Đo được: 75 trong 91 dòng bị gắn
"bắt buộc", tức nhãn đó không còn phân loại được gì nữa.

Cuối cùng, `GapList.jsx` chỉ hiện 12 mục đầu mỗi nhóm kèm nút "Xem thêm" — danh
sách đã xếp theo mức độ đáng học nên mười hai dòng đầu là phần đáng đọc nhất.

**Kết quả đo trên cùng công ty, cùng CV:**

| | Trước | Sau |
|---|---|---|
| Nhóm "bắt buộc phải bù" | 22 dòng | **2 dòng** (N2 và 4 năm — mốc dễ nhất) |
| Nhóm "nên có thêm" | 54 dòng | 83 dòng, xếp theo số vị trí yêu cầu |
| Dòng hiện ra khi mở trang | 76 khối chữ dài | **14 dòng một dòng một** |
| Chiều cao trang | hơn 5.000 px | vừa một màn hình rưỡi |

Riêng phần gộp theo thang này phải làm hai lượt: lượt đầu chỉ gộp ngôn ngữ và số
năm, chụp ảnh lại mới thấy bốn dòng lương gần trùng nhau vẫn chiếm đầu nhóm "nên
có thêm" và đẩy phần kỹ năng — thứ đáng đọc — xuống dưới nếp gấp.

Test canh: sáu test trong `tests/test_matching.py`, từ
`test_company_gaps_count_positions_per_missing_skill` tới
`test_company_keeps_only_the_best_paying_position`.
