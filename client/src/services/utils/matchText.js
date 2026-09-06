/**
 * Dựng câu cho phần "còn thiếu gì" từ dữ liệu backend trả về.
 *
 * Backend gửi mỗi mục dưới dạng `{ kind, code, params, message }` — xem
 * `Gap`/`Met` trong `app/services/matching.py`. Ở đây ưu tiên dịch theo `code`,
 * và chỉ rơi về `message` (tiếng Việt dựng sẵn ở server) khi mã đó chưa có bản
 * dịch. Không bao giờ để lộ khoá thô ra màn hình.
 */

const resolve = (t, item) => {
  if (item?.code) {
    const translated = t(item.code, { ...(item.params || {}), defaultValue: '' });
    if (translated) return translated;
  }
  return item?.message || '';
};

/** Câu mô tả một điểm CV chưa đáp ứng. `t` phải thuộc namespace `match`. */
export const gapText = resolve;

/** Câu mô tả một yêu cầu CV đã đáp ứng. `t` phải thuộc namespace `match`. */
export const metText = resolve;
