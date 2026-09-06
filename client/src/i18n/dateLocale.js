/**
 * Cầu nối giữa ngôn ngữ giao diện và locale của date-fns.
 *
 * Trước khi có file này, `formatDate` cứng locale `'vi'` và năm chỗ dùng
 * `formatDistance` không truyền locale nên luôn ra tiếng Anh ("3 hours ago")
 * kể cả khi phần còn lại của trang là tiếng Việt.
 */
import { ja, vi, enUS } from 'date-fns/locale';
import i18n, { DEFAULT_LANGUAGE } from './config';

const LOCALES = { ja, vi, en: enUS };

/** Locale date-fns tương ứng ngôn ngữ đang chọn. */
export const currentDateLocale = () =>
  LOCALES[i18n.resolvedLanguage] || LOCALES[DEFAULT_LANGUAGE];

/** Mã BCP-47 cho `Intl` (date-fns `intlFormat` nhận chuỗi này, không nhận object). */
export const currentIntlLocale = () => i18n.resolvedLanguage || DEFAULT_LANGUAGE;
