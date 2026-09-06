# 10. Mô phỏng đối chứng — "nếu tôi học thêm thì sao?"

> Bài này viết cho người chưa quen lập trình. Mọi con số trong bài đều đo được
> từ chính dữ liệu của dự án, và bạn tự chạy lại được bằng các lệnh ở cuối bài.

## 10.1. Chức năng này trả lời câu hỏi gì

Trang **"Công ty phù hợp"** trả lời *"CV của tôi hợp với công ty nào"*. Trang
**"Còn thiếu gì"** trả lời *"tôi chưa đạt những gì"*. Nhưng cả hai đều dừng ở
chỗ **liệt kê**. Người tìm việc đọc xong vẫn còn một câu hỏi nữa, và thường là
câu quan trọng nhất:

> Tôi chỉ có thời gian học **một** thứ. Học cái nào thì mở ra nhiều cơ hội nhất?

Màn hình **"Nếu tôi học thêm"** (`/match/whatif`) trả lời đúng câu đó. Bạn tick
những thứ định bù, hệ thống chấm lại **toàn bộ 430 tin tuyển dụng** với một bản
CV *giả định*, rồi cho biết số cơ hội thay đổi thế nào.

Ví dụ thật với tài khoản demo:

```
Hiện tại:              94/430 tin đủ điều kiện, thuộc 65 công ty
  + lên N1        →  +68 tin
  + lên N2        →  +64 tin
  + học Sales     →  +42 tin
  + học Teaching  →  +37 tin
```

## 10.2. "Đủ điều kiện" nghĩa là gì — và KHÔNG nghĩa là gì

**Nghĩa là:** CV của bạn **qua được vòng lọc điều kiện** của tin đó — không còn
rào cản nào bị đánh dấu "chắc chắn bị loại".

**KHÔNG nghĩa là:** bạn sẽ được nhận. Nhà tuyển dụng còn xét rất nhiều thứ mà
một tin đăng không viết ra. Câu nhắc này nằm ngay dưới màn hình, cố ý không giấu.

Hệ thống coi bốn thứ là **rào cản chắc chắn loại**:

| Rào cản | Khi nào |
|---|---|
| Tiếng Nhật | CV chưa ghi trình độ, hoặc thấp hơn mức tin đòi |
| Tiếng Anh | như trên |
| Kỹ năng | **không khớp một kỹ năng nào** trong danh sách tin yêu cầu |
| Kinh nghiệm | tin đòi số năm mà CV ghi 0 năm |

> 💡 **Vì sao chỉ "không khớp gì cả" mới bị loại.** Tin tuyển dụng thường liệt
> kê cả những thứ "có thì tốt". Thiếu một hai kỹ năng là bình thường và học
> được. Nhưng không khớp *một thứ nào* thì gần như chắc trượt.

## 10.3. Vì sao lợi ích KHÔNG cộng được

Đây là điểm cốt lõi, và cũng là lý do chức năng này phải là một **cỗ máy tính
lại** chứ không phải một bảng tra sẵn.

**Chiều thứ nhất — kết hợp cho NHIỀU hơn tổng lẻ.** Đo trên dữ liệu thật:

```
lên N2      →  +64 tin
học Sales   →  +42 tin
cộng lẻ     →  106 tin
làm cả hai  →  +116 tin   ← nhiều hơn 10 tin
```

Vì có những tin đòi **cùng lúc** cả tiếng Nhật lẫn Sales. Bù riêng tiếng Nhật
thì Sales vẫn chặn; bù riêng Sales thì tiếng Nhật vẫn chặn. Những tin đó không
được tính vào lợi ích của mục nào cả — chỉ khi làm **cả hai** chúng mới mở ra.

**Chiều thứ hai — kết hợp cho ÍT hơn tổng lẻ.** Một tin yêu cầu `["Go", "Rust"]`
mà CV chưa có kỹ năng nào: học Go mở được tin đó (+1), học Rust cũng mở được tin
đó (+1), nhưng học cả hai vẫn chỉ là **một tin** chứ không phải hai.

> **Bản thiết kế ban đầu đoán sai chiều** — tưởng kết hợp luôn nhỏ hơn tổng lẻ.
> Chạy thật mới lộ ra chiều ngược lại. Hai test
> `test_combining_can_open_MORE_than_the_sum_of_the_parts` và
> `..._FEWER_...` giờ pin lại **cả hai** chiều bằng dữ liệu dựng tay, để câu chữ
> trên màn hình không bao giờ nói sai nữa.

Vì cả hai chiều đều xảy ra được, giao diện **so con số thật với tổng lẻ rồi mới
chọn câu giải thích**, chứ không viết cứng một chiều.

## 10.4. Vì sao không có "số giờ học"

Câu hỏi tự nhiên tiếp theo là *"học Kubernetes mất bao lâu?"*. Hệ thống **cố ý
không trả lời**, vì không có nguồn nào đáng tin cho con số đó — và một con số
bịa ra sẽ là chỗ yếu nhất của cả chức năng.

Thay vào đó màn hình hiện hai đại lượng **đo được từ dữ liệu thật**:

| | |
|---|---|
| **Số tin mở thêm** | đếm chính xác, không phải ước lượng |
| **Trung vị lương của nhóm tin mở thêm** | lấy từ chính những tin vừa mở ra, kèm cỡ mẫu |

Đại lượng thứ hai mới là thứ giúp so sánh: hai kỹ năng cùng mở ra 20 tin, nhưng
một bên trung vị 300万 còn bên kia 500万, thì lựa chọn đã rõ.

## 10.5. Vì sao mọi trung vị đều kèm `n`

Trang **"Bản đồ thị trường"** (`/market`) tổng hợp 430 tin. Ở đây có một cái bẫy:

| Yêu cầu tiếng Nhật | Số tin ghi lương | Trung vị |
|---|---|---|
| none | 12 | 300万 |
| basic | 13 | 264万 |
| **conversational** | 39 | **450万** |
| business | 101 | 400万 |
| fluent | 12 | 350万 |
| native | 14 | 400万 |

Trình độ càng cao **không** đồng nghĩa lương càng cao — mức `conversational` còn
cao hơn cả `fluent`. Nhìn sang bảng kỹ năng thì rõ nguyên nhân:

| Kỹ năng | Số tin | Trung vị |
|---|---|---|
| Teaching | 109 | 300万 |
| Customer Support | 46 | 300万 |
| **AWS** | 52 | **500万** |
| **JavaScript** | 45 | **500万** |
| **Python** | 37 | **500万** |

Nhóm tin đòi tiếng Nhật cao phần lớn là **giảng dạy và dịch vụ**, không phải kỹ
thuật. Kết luận trung thực — và cũng là kết luận đáng giá hơn:

> **Tiếng Nhật mở ra *số lượng* cơ hội; kỹ năng quyết định *mức lương*.**

Vì nhiều nhóm chỉ có 12–14 mẫu, hệ thống áp hai quy tắc cứng:

1. **Mọi trung vị luôn hiện kèm cỡ mẫu `n`.**
2. **Nhóm có dưới 10 tin ghi lương thì KHÔNG hiện trung vị**, chỉ hiện cỡ mẫu.
   Riêng kỹ năng, các nhóm nhỏ được gộp thành một dòng chú thích thay vì liệt kê
   thành 59 dòng nhiễu.

Hai quy tắc này có test canh: `test_every_median_comes_with_its_sample_size`.

## 10.6. Máy tính lại nhanh cỡ nào

Một lượt chấm toàn bộ 430 tin mất khoảng **2 mili giây**. 15 phương án là **22
mili giây**. Vì vậy mỗi lần bạn tick một ô là hệ thống tính lại **ngay trong
request** — không cần tính trước, không cần bộ nhớ đệm.

Điểm quan trọng: phần này **không dùng tới AI**. Số tin đủ điều kiện chỉ phụ
thuộc bộ luật, nên **tắt hẳn service `embedder` thì con số vẫn y nguyên**. Có
test canh đúng điều đó.

## 10.7. Muốn thêm một loại phương án mới thì sửa ở đâu

Ví dụ muốn thêm "nếu tôi chấp nhận mức lương thấp hơn":

| Bước | File |
|---|---|
| 1. Cho phép loại mới | `server_python/app/controllers/match.py` → `VALID_ACTION_KINDS` |
| 2. Dạy cách áp dụng vào CV | `server_python/app/services/whatif.py` → `apply_actions` |
| 3. Cho vào danh sách gợi ý | cùng file → `candidate_actions` |
| 4. Đặt câu chữ cho 3 ngôn ngữ | `client/src/i18n/locales/{ja,vi,en}/whatif.json` → `action.*` |

> ⚠️ **Hai cái bẫy đã gặp thật:**
>
> - `apply_actions` phải **gộp**, không được ghi đè tuần tự. Bản đầu ghi đè nên
>   tick cùng lúc "lên N2" và "lên N1" cho ra +64 hay +68 **tuỳ thứ tự** client
>   gửi lên — cùng một lựa chọn mà hai kết quả.
> - Không phương án nào được làm CV **kém đi**. Đây là mô phỏng "nếu tôi học
>   thêm", nên áp mức thấp hơn phải bị bỏ qua.
>
> Cả hai đều có test pin lại.

## 10.8. Tự chạy lại các con số

```bash
# Test logic thuần (nhanh, không cần server)
docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm \
  api-tests python -m pytest tests/test_whatif.py tests/test_market.py -q

# Xem so lieu that qua API
TOKEN=$(curl -s -X POST localhost:3000/api/users/login -H 'Content-Type: application/json' \
  -d '{"email":"demo@fuurin.local","password":"Demo@12345"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['accessToken'])")

curl -s localhost:3000/api/match/whatif  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool | head -30
curl -s localhost:3000/api/jobs/market   -H "Authorization: Bearer $TOKEN" | python3 -m json.tool | head -30

# Chung minh khong phu thuoc embedder: tat di, con so KHONG doi
docker compose stop embedder
curl -s localhost:3000/api/match/whatif -H "Authorization: Bearer $TOKEN" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['baseline'])"
docker compose start embedder
```
