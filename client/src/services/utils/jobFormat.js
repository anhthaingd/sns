/**
 * Định dạng lương và trình độ ngôn ngữ của tin tuyển dụng.
 *
 * Backend lưu lương theo **yên/năm** và trình độ theo **mã thô** (`business`).
 * Việc đổi sang chữ hiển thị nằm ở đây vì mỗi ngôn ngữ có quy ước riêng:
 *
 *   ja  500万円 / 年     — người Nhật đọc theo đơn vị 万 (1 man = 10.000 yên)
 *   vi  500 man / năm    — cộng đồng người Việt ở Nhật cũng dùng "man"
 *   en  ¥5.0M / year     — người đọc tiếng Anh không có khái niệm "man"
 *
 * Nên cả ba con số (`man`, `triệu yên`) đều được tính sẵn và truyền vào câu
 * dịch; mỗi bản dịch tự chọn con số hợp với quy ước của mình.
 */

const toMan = (yen) => Math.round(yen / 10_000);
const toMillion = (yen) => (yen / 1_000_000).toFixed(1);

/**
 * Mọi khoá dưới đây đều ghi rõ namespace `job:`.
 *
 * Bắt buộc phải như vậy: các hàm này nhận `t` từ component gọi chúng, mà mỗi
 * component có namespace mặc định khác nhau. `MatchLayout` dùng
 * `useTranslation(['match', 'job'])` nên mặc định của nó là `match` — viết
 * `t('salary.range')` ở đây thì nó tra trong `match`, không thấy, và **in thẳng
 * chuỗi `salary.range` ra màn hình**. Lỗi này đã xảy ra thật ở trang chi tiết
 * công ty trước khi có tiền tố `job:`.
 *
 * @param t  hàm dịch của bất kỳ component nào, miễn là `job` nằm trong danh
 *           sách namespace của nó
 */
export const formatSalary = (t, min, max) => {
  if (!min && !max) return t('job:salary.undisclosed');
  if (min && max && min !== max) {
    return t('job:salary.range', {
      minMan: toMan(min), maxMan: toMan(max),
      minM: toMillion(min), maxM: toMillion(max),
    });
  }
  const value = min || max;
  return t('job:salary.single', { minMan: toMan(value), minM: toMillion(value) });
};

/** Nhãn trình độ tiếng Nhật; mã lạ thì trả lại nguyên mã thay vì để trống. */
export const japaneseLevelLabel = (t, level) =>
  level ? t(`job:level.${level}`, { defaultValue: level }) : '';

/** Nhãn số năm kinh nghiệm; `0` nghĩa là không yêu cầu, không phải "0 năm". */
export const experienceLabel = (t, years) =>
  years === 0 ? t('job:experience.none') : t('job:experience.years', { years });
