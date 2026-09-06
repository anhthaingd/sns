import { intlFormat } from 'date-fns';
import { currentIntlLocale } from '../../i18n/dateLocale';

/**
 * Ngày dạng dài, theo ngôn ngữ giao diện đang chọn.
 *
 * Trước đây locale bị đặt cứng `'vi'`, nên người xem giao diện tiếng Nhật vẫn
 * thấy "21 tháng 8, 2026".
 */
export const formatDate = (date) => {
  if (!date) return '';
  return intlFormat(
    new Date(date),
    { year: 'numeric', month: 'long', day: 'numeric' },
    { locale: currentIntlLocale() }
  );
};

/**
 * Ngày dạng ngắn (ngày sinh, ngày tạo).
 *
 * Trước đây ba chỗ gọi `format(date, 'dd/MM/yyyy')` — khuôn ngày của người
 * Việt. Người Nhật viết 2026/09/06, người Anh viết 09/06/2026: cùng một chuỗi
 * số nhưng đọc ra ba ngày khác nhau, nên khuôn phải theo locale chứ không
 * được đặt cứng.
 */
export const formatShortDate = (date) => {
  if (!date) return '';
  return intlFormat(
    new Date(date),
    { year: 'numeric', month: '2-digit', day: '2-digit' },
    { locale: currentIntlLocale() }
  );
};
